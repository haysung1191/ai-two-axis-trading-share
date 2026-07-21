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
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_concentrated_book_sweep"
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


def _patch_concentrated_book(*, drop_count: int, threshold_gap: float):
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 6 or "FlowScore" not in book.columns:
            return book
        out = book.copy()
        out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
        out["FlowScore"] = pd.to_numeric(out["FlowScore"], errors="coerce").fillna(0.0)

        ranked = out.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True])
        top_flow_avg = float(ranked.head(2)["FlowScore"].mean())
        flow_median = float(ranked["FlowScore"].median())
        if top_flow_avg >= flow_median - threshold_gap:
            return out

        candidate_pool = ranked.iloc[2:].copy()
        local_drop_count = min(drop_count, len(candidate_pool))
        if local_drop_count <= 0:
            return out

        bottom_to_drop = candidate_pool.tail(local_drop_count)
        released = float(pd.to_numeric(bottom_to_drop["TargetWeight"], errors="coerce").fillna(0.0).sum())
        if released <= 0:
            return out

        out = out.drop(index=bottom_to_drop.index).copy()
        reranked = out.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True])
        recipients = reranked.index
        recipient_weights = pd.to_numeric(out.loc[recipients, "TargetWeight"], errors="coerce").fillna(0.0)
        total = float(recipient_weights.sum())
        if total > 0:
            out.loc[recipients, "TargetWeight"] = recipient_weights + released * (recipient_weights / total)
        else:
            out.loc[recipients, "TargetWeight"] = recipient_weights + released / float(len(recipients))

        total_after = float(pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0).sum())
        if total_after > 0:
            out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0) / total_after
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
        "# Split Models Operational Conversion Concentrated Book Sweep",
        "",
        "## Purpose",
        "",
        "- test a discrete book-structure change on top of the redistribution base",
        "- in weak-flow months, drop multiple bottom holdings entirely and reallocate to the remaining book",
        "",
        "## Current Read",
        "",
        f"- redistribution base point: `{summary['base_variant']}`",
        f"- best concentrated-book point: `{summary['best_variant']}`",
        f"- best concentrated-book MDD: `{_pct(summary['best_mdd'])}`",
        f"- best concentrated-book CAGR: `{_pct(summary['best_cagr'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Bucket | Drop Count | Flow Gap | CAGR | MDD | Sharpe | Neg WF |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | `{row['Bucket']}` | {int(row['DropCount'])} | {_pct(row['ThresholdGap'])} | "
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
        (2, 0.00),
        (3, 0.00),
        (4, 0.00),
        (2, 0.02),
        (3, 0.02),
        (4, 0.02),
    ]

    rows: list[dict[str, object]] = []
    for drop_count, threshold_gap in grid:
        variant_name = (
            f"{BASE_VARIANT}_conbook_drop{int(drop_count)}_gap{int(round(threshold_gap * 100)):02d}"
        )
        variant = replace(strongest, name=variant_name)
        result = _run_with_patch(
            variant,
            _compose_patches(base_patch, _patch_concentrated_book(drop_count=drop_count, threshold_gap=threshold_gap)),
            universe,
            price_cache,
            flow_cache,
            monthly_close,
            signal_dates,
            cfg,
        )
        summary = _summarize_candidate(variant_name, result, strongest_result)
        summary["DropCount"] = drop_count
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
    base_summary["DropCount"] = 0
    base_summary["ThresholdGap"] = 0.0
    base_summary["Bucket"] = _bucket(pd.Series(base_summary), pd.Series(baseline_summary))
    rows.append(base_summary)

    compare = pd.DataFrame(rows).sort_values(
        ["NegativeCAGRWindows", "MDD", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "concentrated_book_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "base_variant": BASE_VARIANT,
        "best_variant": str(best["Variant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_drop_count": int(best["DropCount"]),
        "best_threshold_gap": float(best["ThresholdGap"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    if (
        abs(summary["best_cagr"] - float(base_summary["CAGR"])) < 1e-12
        and abs(summary["best_mdd"] - float(base_summary["MDD"])) < 1e-12
        and abs(summary["best_sharpe"] - float(base_summary["Sharpe"])) < 1e-12
    ):
        summary["verdict"] = (
            f"the concentrated-book axis is effectively a no-op. "
            f"Dropping multiple weak-flow bottom holdings does not improve drawdown or create a better conversion point than `{BASE_VARIANT}`."
        )
    else:
        summary["verdict"] = (
            f"the concentrated-book axis finds `{summary['best_variant']}` as the cleanest guarded point; "
            f"it moves MDD to {_pct(summary['best_mdd'])} with CAGR {_pct(summary['best_cagr'])}."
        )

    (OUTPUT_DIR / "concentrated_book_sweep_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "concentrated_book_sweep_review.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
