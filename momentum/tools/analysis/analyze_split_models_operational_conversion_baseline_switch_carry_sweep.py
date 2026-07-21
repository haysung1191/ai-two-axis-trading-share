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
from tools.analysis.analyze_split_models_operational_conversion_baseline_switch_sweep import (
    BASELINE_VARIANT,
    BASE_VARIANT,
    STRONGEST_VARIANT,
    _weak_flow_trigger,
)
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import (
    _patch_tail_release_custom,
    _pct,
)
from tools.analysis.analyze_split_models_tradeoff_frontier import (
    _build_context,
    _summarize_candidate,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_baseline_switch_carry_sweep"
MDD_TOL = 1e-9


def _compose_variant_name(threshold_gap: float, carry_count: int) -> str:
    return f"{BASE_VARIANT}_switchcarry_gap{int(round(threshold_gap * 100)):02d}_top{carry_count}"


def _normalize(book: pd.DataFrame) -> pd.DataFrame:
    out = book.copy()
    out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
    total = float(out["TargetWeight"].sum())
    if total > 0:
        out["TargetWeight"] = out["TargetWeight"] / total
    return out


def _carry_top_from_base(
    *,
    base_book: pd.DataFrame,
    baseline_book: pd.DataFrame,
    carry_count: int,
) -> pd.DataFrame:
    if baseline_book.empty:
        return baseline_book

    base = _normalize(base_book)
    fallback = _normalize(baseline_book)
    if base.empty:
        return fallback

    sort_cols = ["TargetWeight"]
    ascending = [False]
    if "MomentumScore" in base.columns:
        sort_cols.append("MomentumScore")
        ascending.append(False)
    if "FlowScore" in base.columns:
        sort_cols.append("FlowScore")
        ascending.append(False)
    if "Symbol" in base.columns:
        sort_cols.append("Symbol")
        ascending.append(True)

    leaders = base.sort_values(sort_cols, ascending=ascending).head(carry_count).copy()
    if leaders.empty:
        return fallback

    key_col = "AssetKey" if "AssetKey" in leaders.columns and "AssetKey" in fallback.columns else "Symbol"
    carried_keys = set(leaders[key_col].astype(str))
    carried_total = float(pd.to_numeric(leaders["TargetWeight"], errors="coerce").fillna(0.0).sum())
    residual_target = max(0.0, 1.0 - carried_total)

    residual = fallback.loc[~fallback[key_col].astype(str).isin(carried_keys)].copy()
    residual["TargetWeight"] = pd.to_numeric(residual["TargetWeight"], errors="coerce").fillna(0.0)
    residual_total = float(residual["TargetWeight"].sum())
    if residual_total > 0 and residual_target > 0:
        residual["TargetWeight"] = residual["TargetWeight"] * (residual_target / residual_total)
    else:
        residual["TargetWeight"] = 0.0

    combined = pd.concat([leaders, residual], ignore_index=True, sort=False)
    combined = combined.drop_duplicates(subset=[key_col], keep="first")
    return _normalize(combined)


def _run_with_baseline_switch_carry(
    *,
    variant: TradingVariant,
    fallback_variant: TradingVariant,
    redistribution_patch: Callable[[pd.DataFrame], pd.DataFrame],
    threshold_gap: float,
    carry_count: int,
    universe: pd.DataFrame,
    price_cache: dict[str, pd.DataFrame],
    flow_cache: dict[str, pd.DataFrame],
    monthly_close: pd.DataFrame,
    signal_dates: list[pd.Timestamp],
    cfg: BacktestConfig,
) -> tuple[dict[str, pd.DataFrame], int]:
    original = bt._build_momentum_candidates_for_date
    switch_count = 0

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

        base_book = redistribution_patch(book)
        if not _weak_flow_trigger(base_book, threshold_gap=threshold_gap, sector_bias_min=None):
            return base_book

        switch_count += 1
        baseline_book = original(
            metrics,
            flow_snapshot,
            cfg_inner,
            variant=fallback_variant,
            prev_hold_keys=prev_hold_keys,
            **kwargs,
        )
        return _carry_top_from_base(base_book=base_book, baseline_book=baseline_book, carry_count=carry_count)

    bt._build_momentum_candidates_for_date = wrapped_build
    try:
        result = _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, variant)
        return result, switch_count
    finally:
        bt._build_momentum_candidates_for_date = original


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Baseline Switch Carry Sweep",
        "",
        "## Purpose",
        "",
        "- test a hybrid switch: in weak-flow months, move to the baseline book but preserve the strongest concentrated base leaders",
        "- check whether preserving top-weight concentration fixes the failure seen in the raw baseline-switch axis",
        "",
        "## Current Read",
        "",
        f"- base point: `{summary['base_variant']}`",
        f"- best carry-switch point: `{summary['best_variant']}`",
        f"- best MDD: `{_pct(summary['best_mdd'])}`",
        f"- best CAGR: `{_pct(summary['best_cagr'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Carry | Gap | Switch Count | CAGR | MDD | Sharpe | Neg WF |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | {int(row['CarryCount'])} | {_pct(row['ThresholdGap'])} | {int(row['SwitchCount'])} | "
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
    redistribution_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)

    base_variant = replace(strongest, name=BASE_VARIANT)
    base_result, _ = _run_with_baseline_switch_carry(
        variant=base_variant,
        fallback_variant=baseline,
        redistribution_patch=redistribution_patch,
        threshold_gap=999.0,
        carry_count=0,
        universe=universe,
        price_cache=price_cache,
        flow_cache=flow_cache,
        monthly_close=monthly_close,
        signal_dates=signal_dates,
        cfg=cfg,
    )
    base_summary = _summarize_candidate(BASE_VARIANT, base_result, strongest_result)
    base_summary["CarryCount"] = 0
    base_summary["ThresholdGap"] = None
    base_summary["SwitchCount"] = 0

    grid = [
        (0.00, 1),
        (0.00, 2),
        (0.02, 1),
        (0.02, 2),
        (0.04, 2),
    ]

    rows: list[dict[str, object]] = [base_summary]
    for threshold_gap, carry_count in grid:
        variant_name = _compose_variant_name(threshold_gap, carry_count)
        variant = replace(strongest, name=variant_name)
        result, switch_count = _run_with_baseline_switch_carry(
            variant=variant,
            fallback_variant=baseline,
            redistribution_patch=redistribution_patch,
            threshold_gap=threshold_gap,
            carry_count=carry_count,
            universe=universe,
            price_cache=price_cache,
            flow_cache=flow_cache,
            monthly_close=monthly_close,
            signal_dates=signal_dates,
            cfg=cfg,
        )
        summary = _summarize_candidate(variant_name, result, strongest_result)
        summary["CarryCount"] = carry_count
        summary["ThresholdGap"] = threshold_gap
        summary["SwitchCount"] = switch_count
        rows.append(summary)

    compare = pd.DataFrame(rows)
    compare["MDDBucket"] = compare["MDD"].round(9)
    compare = compare.sort_values(
        ["NegativeCAGRWindows", "MDDBucket", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "baseline_switch_carry_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "base_variant": BASE_VARIANT,
        "best_variant": str(best["Variant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_carry_count": int(best["CarryCount"]),
        "best_threshold_gap": None if pd.isna(best["ThresholdGap"]) else float(best["ThresholdGap"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    if best["MDD"] > base_summary["MDD"] + MDD_TOL:
        summary["verdict"] = (
            f"the carry-switch axis improves drawdown: `{summary['best_variant']}` lifts MDD to {_pct(summary['best_mdd'])} "
            f"with CAGR {_pct(summary['best_cagr'])}."
        )
    elif abs(best["MDD"] - base_summary["MDD"]) <= MDD_TOL and (
        best["CAGR"] > base_summary["CAGR"] + 1e-12 or best["Sharpe"] > base_summary["Sharpe"] + 1e-12
    ):
        summary["verdict"] = (
            f"the carry-switch axis improves quality but not drawdown. "
            f"`{summary['best_variant']}` keeps MDD flat at {_pct(summary['best_mdd'])} while moving CAGR to {_pct(summary['best_cagr'])}."
        )
    else:
        summary["verdict"] = (
            f"the carry-switch axis fails: no carry point improves drawdown or quality versus `{BASE_VARIANT}`."
        )

    (OUTPUT_DIR / "baseline_switch_carry_sweep_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "baseline_switch_carry_sweep_review.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
