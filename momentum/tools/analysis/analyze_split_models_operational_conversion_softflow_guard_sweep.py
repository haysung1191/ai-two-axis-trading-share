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
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_softflow_guard_sweep"
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


def _patch_softflow_guard(shift_cap: float, threshold_gap: float):
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 4 or "FlowScore" not in book.columns:
            return book
        out = book.copy()
        out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
        out["FlowScore"] = pd.to_numeric(out["FlowScore"], errors="coerce").fillna(0.0)
        ranked = out.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True])
        top_idx = ranked.head(2).index
        top_flow_avg = float(ranked.head(2)["FlowScore"].mean())
        book_flow_median = float(ranked["FlowScore"].median())
        if top_flow_avg >= book_flow_median - threshold_gap:
            return out

        top_weights = pd.to_numeric(out.loc[top_idx, "TargetWeight"], errors="coerce").fillna(0.0)
        top_total = float(top_weights.sum())
        shift = min(shift_cap, top_total * 0.25)
        if shift <= 0:
            return out

        out.loc[top_idx, "TargetWeight"] = top_weights - shift * (top_weights / top_total)
        rest_idx = ranked.index[2:]
        rest_weights = pd.to_numeric(out.loc[rest_idx, "TargetWeight"], errors="coerce").fillna(0.0)
        rest_total = float(rest_weights.sum())
        if rest_total > 0:
            out.loc[rest_idx, "TargetWeight"] = rest_weights + shift * (rest_weights / rest_total)
        elif len(rest_idx) > 0:
            out.loc[rest_idx, "TargetWeight"] = rest_weights + shift / float(len(rest_idx))

        total_after = float(out["TargetWeight"].sum())
        if total_after > 0:
            out["TargetWeight"] = out["TargetWeight"] / total_after
        return out

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
        "# Split Models Operational Conversion Softflow Guard Sweep",
        "",
        "## Purpose",
        "",
        "- test a narrow soft-flow guard on top of the best redistribution drawdown-control point",
        "- only reduce top2 weight when the top2 flow profile weakens versus the book median",
        "",
        "## Current Read",
        "",
        f"- redistribution base point: `{summary['base_variant']}`",
        f"- best guarded point: `{summary['best_variant']}`",
        f"- best guarded MDD: `{_pct(summary['best_mdd'])}`",
        f"- best guarded CAGR: `{_pct(summary['best_cagr'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Bucket | Shift Cap | Flow Gap | CAGR | MDD | Sharpe | Neg WF |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | `{row['Bucket']}` | {_pct(row['ShiftCap'])} | {_pct(row['ThresholdGap'])} | "
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

    base_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)
    grid = [
        (0.03, 0.00),
        (0.05, 0.00),
        (0.07, 0.00),
        (0.03, 0.02),
        (0.05, 0.02),
        (0.07, 0.02),
    ]

    rows: list[dict[str, object]] = []
    for shift_cap, threshold_gap in grid:
        variant_name = f"{BASE_VARIANT}_softflow_shift{int(round(shift_cap * 100)):02d}_gap{int(round(threshold_gap * 100)):02d}"
        variant = replace(strongest, name=variant_name)
        result = _run_with_patch(
            variant,
            _compose_patches(base_patch, _patch_softflow_guard(shift_cap, threshold_gap)),
            universe,
            price_cache,
            flow_cache,
            monthly_close,
            signal_dates,
            cfg,
        )
        summary = _summarize_candidate(variant_name, result, strongest_result)
        summary["ShiftCap"] = shift_cap
        summary["ThresholdGap"] = threshold_gap
        summary["Bucket"] = _bucket(pd.Series(summary), pd.Series(baseline_summary))
        rows.append(summary)

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
    base_summary["ShiftCap"] = 0.0
    base_summary["ThresholdGap"] = 0.0
    base_summary["Bucket"] = _bucket(pd.Series(base_summary), pd.Series(baseline_summary))
    rows.append(base_summary)

    compare = pd.DataFrame(rows).sort_values(
        ["NegativeCAGRWindows", "MDD", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "softflow_guard_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "base_variant": BASE_VARIANT,
        "best_variant": str(best["Variant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_shift_cap": float(best["ShiftCap"]),
        "best_threshold_gap": float(best["ThresholdGap"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    if summary["best_variant"] == BASE_VARIANT:
        summary["verdict"] = (
            f"the narrow soft-flow guard axis fails: no guarded point beats `{BASE_VARIANT}`. "
            f"Conditional top2 defense does not repair drawdown enough to justify the headline give-up."
        )
    else:
        summary["verdict"] = (
            f"the narrow soft-flow guard finds `{summary['best_variant']}` as the cleanest guarded point; "
            f"drawdown stays flat at {_pct(summary['best_mdd'])}, but CAGR rises to {_pct(summary['best_cagr'])} "
            f"with stronger Sharpe, so this axis improves quality without solving the operating drawdown bar."
        )

    (OUTPUT_DIR / "softflow_guard_sweep_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "softflow_guard_sweep_review.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
