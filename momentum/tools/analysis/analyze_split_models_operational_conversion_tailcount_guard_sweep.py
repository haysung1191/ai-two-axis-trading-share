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
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import _pct
from tools.analysis.analyze_split_models_tradeoff_frontier import (
    _build_context,
    _run_with_patch,
    _summarize_candidate,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_tailcount_guard_sweep"
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


def _patch_tail_release_with_bottom_count(
    *,
    top2_share: float,
    penalty_start: float,
    penalty_floor: float,
    bottom_count: int,
    penalty_power: float = 0.50,
):
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 5:
            return book
        out = book.copy()
        ranked = out.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True])
        top_index = ranked.head(2).index
        candidate_bottom = ranked.loc[~ranked.index.isin(top_index)]
        if candidate_bottom.empty:
            return out

        local_bottom_count = min(bottom_count, len(candidate_bottom))
        bottom_index = candidate_bottom.tail(local_bottom_count).index
        bottom_before = pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0).copy()

        if len(bottom_index) > 1:
            penalty_steps = pd.Series(
                pd.Series(range(len(bottom_index)), index=bottom_index, dtype=float) / float(len(bottom_index) - 1)
            ) ** penalty_power
            penalty_series = pd.Series(
                penalty_start + (penalty_floor - penalty_start) * penalty_steps,
                index=bottom_index,
            )
            out.loc[bottom_index, "TargetWeight"] = (
                pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0) * penalty_series
            )
        else:
            out.loc[bottom_index, "TargetWeight"] = (
                pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0) * penalty_start
            )

        released = float(
            bottom_before.sum() - pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0).sum()
        )
        if released > 0:
            top2_part = released * top2_share
            mid_part = released - top2_part
            out.loc[top_index, "TargetWeight"] = (
                pd.to_numeric(out.loc[top_index, "TargetWeight"], errors="coerce").fillna(0.0)
                + top2_part / float(len(top_index))
            )
            mid_index = ranked.loc[~ranked.index.isin(bottom_index.union(top_index))].index
            if len(mid_index) > 0 and mid_part > 0:
                mid_weights = pd.to_numeric(out.loc[mid_index, "TargetWeight"], errors="coerce").fillna(0.0)
                total = float(mid_weights.sum())
                if total > 0:
                    out.loc[mid_index, "TargetWeight"] = mid_weights + mid_part * (mid_weights / total)
                else:
                    out.loc[mid_index, "TargetWeight"] = mid_weights + mid_part / float(len(mid_index))

        total_after = float(pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0).sum())
        if total_after > 0:
            out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0) / total_after
        return out

    return patch


def _patch_conditional_tailcount_guard(
    *,
    weak_bottom_count: int,
    threshold_gap: float,
    base_bottom_count: int = 6,
):
    weak_patch = _patch_tail_release_with_bottom_count(
        top2_share=0.25,
        penalty_start=0.35,
        penalty_floor=0.25,
        bottom_count=weak_bottom_count,
    )
    base_patch = _patch_tail_release_with_bottom_count(
        top2_share=0.25,
        penalty_start=0.35,
        penalty_floor=0.25,
        bottom_count=base_bottom_count,
    )

    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 5 or "FlowScore" not in book.columns:
            return base_patch(book)
        ranked = book.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True]).copy()
        ranked["FlowScore"] = pd.to_numeric(ranked["FlowScore"], errors="coerce").fillna(0.0)
        top_flow_avg = float(ranked.head(2)["FlowScore"].mean())
        flow_median = float(ranked["FlowScore"].median())
        if top_flow_avg < flow_median - threshold_gap:
            return weak_patch(book)
        return base_patch(book)

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
        "# Split Models Operational Conversion Tailcount Guard Sweep",
        "",
        "## Purpose",
        "",
        "- test whether weak-flow periods should use a smaller redistributed tail slice",
        "- reduce redistribution aggressiveness only when the top2 flow profile softens",
        "",
        "## Current Read",
        "",
        f"- redistribution base point: `{summary['base_variant']}`",
        f"- best tailcount-guard point: `{summary['best_variant']}`",
        f"- best tailcount-guard MDD: `{_pct(summary['best_mdd'])}`",
        f"- best tailcount-guard CAGR: `{_pct(summary['best_cagr'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Bucket | Weak Bottom Count | Flow Gap | CAGR | MDD | Sharpe | Neg WF |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | `{row['Bucket']}` | {int(row['WeakBottomCount'])} | "
            f"{_pct(row['ThresholdGap'])} | {_pct(row['CAGR'])} | {_pct(row['MDD'])} | {row['Sharpe']:.4f} | {int(row['NegativeCAGRWindows'])} |"
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

    base_patch = _patch_tail_release_with_bottom_count(
        top2_share=0.25,
        penalty_start=0.35,
        penalty_floor=0.25,
        bottom_count=6,
    )
    grid = [
        (5, 0.00),
        (4, 0.00),
        (3, 0.00),
        (5, 0.02),
        (4, 0.02),
        (3, 0.02),
    ]

    rows: list[dict[str, object]] = []
    for weak_bottom_count, threshold_gap in grid:
        variant_name = f"{BASE_VARIANT}_tailguard_b{weak_bottom_count}_gap{int(round(threshold_gap * 100)):02d}"
        variant = replace(strongest, name=variant_name)
        result = _run_with_patch(
            variant,
            _patch_conditional_tailcount_guard(
                weak_bottom_count=weak_bottom_count,
                threshold_gap=threshold_gap,
            ),
            universe,
            price_cache,
            flow_cache,
            monthly_close,
            signal_dates,
            cfg,
        )
        summary = _summarize_candidate(variant_name, result, strongest_result)
        summary["WeakBottomCount"] = weak_bottom_count
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
    base_summary["WeakBottomCount"] = 6
    base_summary["ThresholdGap"] = 0.0
    base_summary["Bucket"] = _bucket(pd.Series(base_summary), pd.Series(baseline_summary))
    rows.append(base_summary)

    compare = pd.DataFrame(rows).sort_values(
        ["NegativeCAGRWindows", "MDD", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "tailcount_guard_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "base_variant": BASE_VARIANT,
        "best_variant": str(best["Variant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_weak_bottom_count": int(best["WeakBottomCount"]),
        "best_threshold_gap": float(best["ThresholdGap"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    if (
        abs(summary["best_cagr"] - float(base_summary["CAGR"])) < 1e-12
        and abs(summary["best_mdd"] - float(base_summary["MDD"])) < 1e-12
        and abs(summary["best_sharpe"] - float(base_summary["Sharpe"])) < 1e-12
    ):
        summary["verdict"] = (
            f"the weak-flow tailcount guard axis is effectively a no-op. "
            f"Shrinking the redistributed tail slice in weak-flow months does not change drawdown and does not create a better conversion point than `{BASE_VARIANT}`."
        )
    else:
        summary["verdict"] = (
            f"the weak-flow tailcount guard finds `{summary['best_variant']}` as the cleanest guarded point; "
            f"it moves MDD to {_pct(summary['best_mdd'])} with CAGR {_pct(summary['best_cagr'])}."
        )

    (OUTPUT_DIR / "tailcount_guard_sweep_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "tailcount_guard_sweep_review.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
