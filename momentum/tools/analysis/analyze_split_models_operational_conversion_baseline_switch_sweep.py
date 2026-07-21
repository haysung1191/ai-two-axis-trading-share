from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
import sys
from typing import Callable

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import split_models.backtest as bt
from split_models.backtest import BacktestConfig, TradingVariant, _baseline_variant_map, _run_trading_backtest_variant
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import (
    _patch_tail_release_custom,
    _pct,
)
from tools.analysis.analyze_split_models_tradeoff_frontier import (
    _build_context,
    _summarize_candidate,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_baseline_switch_sweep"
BASELINE_VARIANT = "rule_breadth_it_us5_cap"
STRONGEST_VARIANT = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"
BASE_VARIANT = "tail_release_top25_mid75_pen35_floor25"
US_SECTOR_DRAG_SET = {"Information Technology", "Energy"}


def _compose_variant_name(threshold_gap: float, sector_bias_min: float | None) -> str:
    gap_tag = f"gap{int(round(threshold_gap * 100)):02d}"
    if sector_bias_min is None:
        return f"{BASE_VARIANT}_switch_baseline_{gap_tag}"
    sector_tag = f"sector{int(round(sector_bias_min * 100)):02d}"
    return f"{BASE_VARIANT}_switch_baseline_{gap_tag}_{sector_tag}"


def _weak_flow_trigger(book: pd.DataFrame, threshold_gap: float, sector_bias_min: float | None) -> bool:
    if book.empty or len(book) < 4 or "FlowScore" not in book.columns:
        return False

    ranked = book.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True]).copy()
    ranked["FlowScore"] = pd.to_numeric(ranked["FlowScore"], errors="coerce").fillna(0.0)
    top_flow_avg = float(ranked.head(2)["FlowScore"].mean())
    flow_median = float(ranked["FlowScore"].median())
    weak_flow = top_flow_avg < flow_median - threshold_gap
    if not weak_flow:
        return False

    if sector_bias_min is None:
        return True

    if "TargetWeight" not in ranked.columns or "Sector" not in ranked.columns or "Market" not in ranked.columns:
        return False

    ranked["TargetWeight"] = pd.to_numeric(ranked["TargetWeight"], errors="coerce").fillna(0.0)
    us_drag_weight = float(
        ranked.loc[
            (ranked["Market"].astype(str) == "US")
            & (ranked["Sector"].astype(str).isin(US_SECTOR_DRAG_SET)),
            "TargetWeight",
        ].sum()
    )
    return us_drag_weight >= sector_bias_min


def _run_with_baseline_switch(
    *,
    variant: TradingVariant,
    fallback_variant: TradingVariant,
    redistribution_patch: Callable[[pd.DataFrame], pd.DataFrame],
    threshold_gap: float,
    sector_bias_min: float | None,
    universe: pd.DataFrame,
    price_cache: dict[str, pd.DataFrame],
    flow_cache: dict[str, pd.DataFrame],
    monthly_close: pd.DataFrame,
    signal_dates: list[pd.Timestamp],
    cfg: BacktestConfig,
) -> tuple[dict[str, pd.DataFrame], list[str], int]:
    original = bt._build_momentum_candidates_for_date
    switch_dates: list[str] = []
    switch_count = 0

    def _infer_switch_date(flow_snapshot) -> str | None:
        if isinstance(flow_snapshot, pd.DataFrame):
            for column in ("SignalDate", "Date", "NextDate"):
                if column in flow_snapshot.columns and not flow_snapshot.empty:
                    value = flow_snapshot[column].iloc[-1]
                    if pd.notna(value):
                        return pd.Timestamp(value).strftime("%Y-%m-%d")
        return None

    def wrapped_build(metrics, flow_snapshot, cfg_inner, variant=None, prev_hold_keys=None, **kwargs):
        nonlocal switch_count
        variant_inner = variant
        book = original(
            metrics,
            flow_snapshot,
            cfg_inner,
            variant=variant_inner,
            prev_hold_keys=prev_hold_keys,
            **kwargs,
        )
        if variant_inner.name != variant.name:
            return book

        if _weak_flow_trigger(book, threshold_gap=threshold_gap, sector_bias_min=sector_bias_min):
            switch_count += 1
            signal_date = kwargs.get("signal_date")
            if signal_date is None:
                signal_date = _infer_switch_date(flow_snapshot)
            if signal_date is not None:
                try:
                    switch_dates.append(pd.Timestamp(signal_date).strftime("%Y-%m-%d"))
                except Exception:
                    pass
            return original(
                metrics,
                flow_snapshot,
                cfg_inner,
                variant=fallback_variant,
                prev_hold_keys=prev_hold_keys,
                **kwargs,
            )

        return redistribution_patch(book)

    bt._build_momentum_candidates_for_date = wrapped_build
    try:
        result = _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, variant)
        deduped_dates = list(dict.fromkeys(switch_dates))
        return result, deduped_dates, switch_count
    finally:
        bt._build_momentum_candidates_for_date = original


def _bucket(row: pd.Series, baseline: pd.Series) -> str:
    if (
        row["NegativeCAGRWindows"] == 0
        and row["MDD"] > baseline["MDD"]
        and row["CAGR"] > 0.60
    ):
        return "drawdown_watch"
    if row["NegativeCAGRWindows"] == 0 and row["CAGR"] > baseline["CAGR"]:
        return "quality_watch"
    return "monitor"


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Baseline Switch Sweep",
        "",
        "## Purpose",
        "",
        "- test a real structure change: in weak-flow months, replace the redistribution book with the operating baseline book",
        "- check whether a hard branch switch can finally improve drawdown where micro guards failed",
        "",
        "## Current Read",
        "",
        f"- redistribution base point: `{summary['base_variant']}`",
        f"- best switch point: `{summary['best_variant']}`",
        f"- best switch MDD: `{_pct(summary['best_mdd'])}`",
        f"- best switch CAGR: `{_pct(summary['best_cagr'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Bucket | Flow Gap | Sector Bias Min | CAGR | MDD | Sharpe | Neg WF |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        sector_bias = "-" if row["SectorBiasMin"] is None else _pct(row["SectorBiasMin"])
        lines.append(
            f"| {idx} | `{row['Variant']}` | `{row['Bucket']}` | {_pct(row['ThresholdGap'])} | {sector_bias} | "
            f"{_pct(row['CAGR'])} | {_pct(row['MDD'])} | {row['Sharpe']:.4f} | {int(row['NegativeCAGRWindows'])} |"
        )
    lines.extend(
        [
            "",
            "## Trigger Read",
            "",
            "| Variant | Switch Count | First Switch | Last Switch |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for row in summary["ranked_rows"]:
        lines.append(
            f"| `{row['Variant']}` | {int(row['SwitchCount'])} | `{row['FirstSwitchDate'] or '-'}` | `{row['LastSwitchDate'] or '-'}` |"
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

    redistribution_patch = _patch_tail_release_custom(
        top2_share=0.25,
        penalty_start=0.35,
        penalty_floor=0.25,
    )
    base_result, base_switch_dates, base_switch_count = _run_with_baseline_switch(
        variant=replace(strongest, name=BASE_VARIANT),
        fallback_variant=baseline,
        redistribution_patch=redistribution_patch,
        threshold_gap=999.0,
        sector_bias_min=None,
        universe=universe,
        price_cache=price_cache,
        flow_cache=flow_cache,
        monthly_close=monthly_close,
        signal_dates=signal_dates,
        cfg=cfg,
    )
    base_summary = _summarize_candidate(BASE_VARIANT, base_result, strongest_result)
    base_summary["ThresholdGap"] = None
    base_summary["SectorBiasMin"] = None
    base_summary["SwitchCount"] = base_switch_count
    base_summary["FirstSwitchDate"] = None if not base_switch_dates else base_switch_dates[0]
    base_summary["LastSwitchDate"] = None if not base_switch_dates else base_switch_dates[-1]
    base_summary["Bucket"] = _bucket(pd.Series(base_summary), pd.Series(baseline_summary))

    grid = [
        (0.00, None),
        (0.02, None),
        (0.04, None),
        (0.02, 0.35),
        (0.04, 0.35),
        (0.02, 0.50),
    ]

    rows: list[dict[str, object]] = [base_summary]
    for threshold_gap, sector_bias_min in grid:
        variant_name = _compose_variant_name(threshold_gap, sector_bias_min)
        variant = replace(strongest, name=variant_name)
        result, switch_dates, switch_count = _run_with_baseline_switch(
            variant=variant,
            fallback_variant=baseline,
            redistribution_patch=redistribution_patch,
            threshold_gap=threshold_gap,
            sector_bias_min=sector_bias_min,
            universe=universe,
            price_cache=price_cache,
            flow_cache=flow_cache,
            monthly_close=monthly_close,
            signal_dates=signal_dates,
            cfg=cfg,
        )
        summary = _summarize_candidate(variant_name, result, strongest_result)
        summary["ThresholdGap"] = threshold_gap
        summary["SectorBiasMin"] = sector_bias_min
        summary["SwitchCount"] = switch_count
        summary["FirstSwitchDate"] = None if not switch_dates else switch_dates[0]
        summary["LastSwitchDate"] = None if not switch_dates else switch_dates[-1]
        summary["Bucket"] = _bucket(pd.Series(summary), pd.Series(baseline_summary))
        rows.append(summary)

    compare = pd.DataFrame(rows).sort_values(
        ["NegativeCAGRWindows", "MDD", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "baseline_switch_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "base_variant": BASE_VARIANT,
        "best_variant": str(best["Variant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_threshold_gap": None if pd.isna(best["ThresholdGap"]) else float(best["ThresholdGap"]),
        "best_sector_bias_min": None if pd.isna(best["SectorBiasMin"]) else float(best["SectorBiasMin"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    if best["MDD"] > base_summary["MDD"] + 1e-12:
        summary["verdict"] = (
            f"the baseline-switch axis finally improves drawdown: `{summary['best_variant']}` lifts MDD to {_pct(summary['best_mdd'])} "
            f"while keeping CAGR at {_pct(summary['best_cagr'])}."
        )
    elif abs(best["MDD"] - base_summary["MDD"]) < 1e-12 and (
        best["CAGR"] > base_summary["CAGR"] + 1e-12 or best["Sharpe"] > base_summary["Sharpe"] + 1e-12
    ):
        summary["verdict"] = (
            f"the baseline-switch axis improves quality but not drawdown. "
            f"`{summary['best_variant']}` keeps MDD flat at {_pct(summary['best_mdd'])} while moving CAGR to {_pct(summary['best_cagr'])}."
        )
    else:
        summary["verdict"] = (
            f"the baseline-switch axis fails: no switch point improves drawdown or quality versus `{BASE_VARIANT}`."
        )

    (OUTPUT_DIR / "baseline_switch_sweep_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "baseline_switch_sweep_review.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
