from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from split_models.backtest import BacktestConfig, _baseline_variant_map, _run_trading_backtest_variant
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import (
    _patch_tail_release_custom,
    _pct,
)
from tools.analysis.analyze_split_models_tradeoff_frontier import (
    _build_context,
    _run_with_patch,
    _summarize_candidate,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_fallback_sweep"
BASELINE_VARIANT = "rule_breadth_it_us5_cap"
STRONGEST_VARIANT = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"
BASE_VARIANT = "tail_release_top25_mid75_pen35_floor25"


def _compose_patches(*patches):
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        out = book.copy()
        for patch_fn in patches:
            out = patch_fn(out)
        return out

    return patch


def _patch_conditional_fallback(*, threshold_gap: float, fallback_mode: str):
    redistribution_patch = _patch_tail_release_custom(
        top2_share=0.25,
        penalty_start=0.35,
        penalty_floor=0.25,
    )
    mild_patch = _patch_tail_release_custom(
        top2_share=0.35,
        penalty_start=0.35,
        penalty_floor=0.30,
    )

    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 4 or "FlowScore" not in book.columns:
            return redistribution_patch(book)

        ranked = book.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True]).copy()
        ranked["FlowScore"] = pd.to_numeric(ranked["FlowScore"], errors="coerce").fillna(0.0)
        top_flow_avg = float(ranked.head(2)["FlowScore"].mean())
        flow_median = float(ranked["FlowScore"].median())
        weak_flow = top_flow_avg < flow_median - threshold_gap

        if not weak_flow:
            return redistribution_patch(book)

        if fallback_mode == "strongest":
            return book.copy()
        if fallback_mode == "mild":
            return mild_patch(book)
        return redistribution_patch(book)

    return patch


def _bucket(row: pd.Series, baseline: pd.Series) -> str:
    if (
        row["NegativeCAGRWindows"] == 0
        and row["CAGR"] > baseline["CAGR"]
        and row["Sharpe"] > baseline["Sharpe"]
        and row["MDD"] >= -0.32
    ):
        return "tight_watch"
    if row["NegativeCAGRWindows"] == 0 and row["CAGR"] > 0.70:
        return "watch"
    return "monitor"


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Fallback Sweep",
        "",
        "## Purpose",
        "",
        "- test whether weak-flow months should disable or soften redistribution entirely",
        "- use a true structure change instead of another micro guard that leaves the core redistribution intact",
        "",
        "## Current Read",
        "",
        f"- redistribution base point: `{summary['base_variant']}`",
        f"- best fallback point: `{summary['best_variant']}`",
        f"- best fallback MDD: `{_pct(summary['best_mdd'])}`",
        f"- best fallback CAGR: `{_pct(summary['best_cagr'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Bucket | Fallback | Flow Gap | CAGR | MDD | Sharpe | Neg WF |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | `{row['Bucket']}` | `{row['FallbackMode']}` | {_pct(row['ThresholdGap'])} | "
            f"{_pct(row['CAGR'])} | {_pct(row['MDD'])} | {row['Sharpe']:.4f} | {int(row['NegativeCAGRWindows'])} |"
        )
    lines.extend(["", "## Verdict", "", f"- {summary['verdict']}", ""])
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    variants = _baseline_variant_map()
    baseline = variants[BASELINE_VARIANT]
    strongest = variants[STRONGEST_VARIANT]

    strongest_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, strongest
    )
    baseline_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, baseline
    )
    baseline_summary = _summarize_candidate(BASELINE_VARIANT, baseline_result, strongest_result)

    grid = [
        ("strongest", 0.00),
        ("strongest", 0.02),
        ("strongest", 0.04),
        ("mild", 0.00),
        ("mild", 0.02),
        ("mild", 0.04),
    ]

    rows: list[dict[str, object]] = []
    for fallback_mode, threshold_gap in grid:
        variant_name = f"{BASE_VARIANT}_fallback_{fallback_mode}_gap{int(round(threshold_gap * 100)):02d}"
        variant = replace(strongest, name=variant_name)
        result = _run_with_patch(
            variant,
            _patch_conditional_fallback(threshold_gap=threshold_gap, fallback_mode=fallback_mode),
            universe,
            price_cache,
            flow_cache,
            monthly_close,
            signal_dates,
            cfg,
        )
        summary = _summarize_candidate(variant_name, result, strongest_result)
        summary["FallbackMode"] = fallback_mode
        summary["ThresholdGap"] = threshold_gap
        summary["Bucket"] = _bucket(pd.Series(summary), pd.Series(baseline_summary))
        rows.append(summary)

    base_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)
    base_variant = replace(strongest, name=BASE_VARIANT)
    base_result = _run_with_patch(
        base_variant,
        base_patch,
        universe,
        price_cache,
        flow_cache,
        monthly_close,
        signal_dates,
        cfg,
    )
    base_summary = _summarize_candidate(BASE_VARIANT, base_result, strongest_result)
    base_summary["FallbackMode"] = "none"
    base_summary["ThresholdGap"] = 0.0
    base_summary["Bucket"] = _bucket(pd.Series(base_summary), pd.Series(baseline_summary))
    rows.append(base_summary)

    compare = pd.DataFrame(rows).sort_values(
        ["NegativeCAGRWindows", "MDD", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "fallback_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "base_variant": BASE_VARIANT,
        "best_variant": str(best["Variant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_fallback_mode": str(best["FallbackMode"]),
        "best_threshold_gap": float(best["ThresholdGap"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    if best["MDD"] > base_summary["MDD"] + 1e-12:
        summary["verdict"] = (
            f"the fallback axis finally improves drawdown: `{summary['best_variant']}` raises MDD to {_pct(summary['best_mdd'])} "
            f"with CAGR {_pct(summary['best_cagr'])}."
        )
    elif abs(best["MDD"] - base_summary["MDD"]) < 1e-12 and (
        best["CAGR"] > base_summary["CAGR"] + 1e-12 or best["Sharpe"] > base_summary["Sharpe"] + 1e-12
    ):
        summary["verdict"] = (
            f"the fallback axis improves quality but not drawdown. "
            f"`{summary['best_variant']}` keeps MDD flat at {_pct(summary['best_mdd'])} while moving CAGR to {_pct(summary['best_cagr'])}."
        )
    else:
        summary["verdict"] = (
            f"the fallback axis fails: no fallback point improves drawdown or quality versus `{BASE_VARIANT}`."
        )

    (OUTPUT_DIR / "fallback_sweep_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "fallback_sweep_review.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
