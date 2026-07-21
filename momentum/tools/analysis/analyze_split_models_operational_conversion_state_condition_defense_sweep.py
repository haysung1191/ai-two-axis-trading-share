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
from split_models.backtest import _walkforward_summary
from tools.analysis.analyze_split_models_operational_conversion_baseline_switch_carry_sweep import (
    _carry_top_from_base,
)
from tools.analysis.analyze_split_models_operational_conversion_baseline_switch_sweep import (
    BASELINE_VARIANT,
    BASE_VARIANT,
    STRONGEST_VARIANT,
    _weak_flow_trigger,
)
from tools.analysis.analyze_split_models_operational_conversion_concentration_carry_kr_etf_trim_micro import (
    _compose_patch as _trim22_patch_factory,
)
from tools.analysis.analyze_split_models_operational_conversion_drawdown_window_defense_sweep import (
    EXTENDED_DRAG_SYMBOLS,
    _normalize,
    _redistribute_released_to_kr_etf,
)
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import _pct
from tools.analysis.analyze_split_models_tradeoff_frontier import _build_context, _summarize_candidate


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_state_condition_defense_sweep"
TRIM22_FRACTION = 0.22
TRIM22_GAP = 0.02
TRIM22_CARRY_COUNT = 2
OPERATING_BASELINE_MDD = -0.25241596238415986
DRAG_SECTORS = {"Information Technology", "Energy"}


def _symbol_trim_patch(trim_fraction: float, symbols: set[str]) -> Callable[[pd.DataFrame], pd.DataFrame]:
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty:
            return book
        out = book.copy()
        out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
        mask = out["Symbol"].astype(str).isin(symbols)
        trim_index = set(out.loc[mask].index)
        released = float((out.loc[mask, "TargetWeight"] * trim_fraction).sum())
        out.loc[mask, "TargetWeight"] = out.loc[mask, "TargetWeight"] * (1.0 - trim_fraction)
        return _redistribute_released_to_kr_etf(out, released, trim_index)

    return patch


def _state_condition_trigger(
    book: pd.DataFrame,
    *,
    min_symbol_weight: float,
    min_sector_weight: float,
    require_weak_flow: bool,
    require_drag_flow_weak: bool,
) -> bool:
    if book.empty or "TargetWeight" not in book.columns:
        return False
    ranked = book.copy()
    ranked["TargetWeight"] = pd.to_numeric(ranked["TargetWeight"], errors="coerce").fillna(0.0)
    symbol_weight = float(ranked.loc[ranked["Symbol"].astype(str).isin(EXTENDED_DRAG_SYMBOLS), "TargetWeight"].sum())
    sector_weight = float(
        ranked.loc[
            ranked["Market"].astype(str).eq("US") & ranked["Sector"].astype(str).isin(DRAG_SECTORS),
            "TargetWeight",
        ].sum()
    )
    if symbol_weight < min_symbol_weight or sector_weight < min_sector_weight:
        return False
    if require_weak_flow and not _weak_flow_trigger(ranked, threshold_gap=TRIM22_GAP, sector_bias_min=None):
        return False
    if require_drag_flow_weak:
        if "FlowScore" not in ranked.columns:
            return False
        ranked["FlowScore"] = pd.to_numeric(ranked["FlowScore"], errors="coerce").fillna(0.0)
        drag_flow = ranked.loc[ranked["Symbol"].astype(str).isin(EXTENDED_DRAG_SYMBOLS), "FlowScore"]
        if drag_flow.empty:
            return False
        if float(drag_flow.mean()) >= float(ranked["FlowScore"].median()):
            return False
    return True


def _run_state_condition_defense(
    *,
    variant: TradingVariant,
    fallback_variant: TradingVariant,
    min_symbol_weight: float,
    min_sector_weight: float,
    require_weak_flow: bool,
    require_drag_flow_weak: bool,
    max_defense_count: int | None,
    min_defense_gap_months: int = 0,
    trim_fraction: float,
    universe: pd.DataFrame,
    price_cache: dict[str, pd.DataFrame],
    flow_cache: dict[str, pd.DataFrame],
    monthly_close: pd.DataFrame,
    signal_dates: list[pd.Timestamp],
    cfg: BacktestConfig,
) -> tuple[dict[str, pd.DataFrame], dict[str, object]]:
    original = bt._build_momentum_candidates_for_date
    trim22_patch = _trim22_patch_factory(TRIM22_FRACTION)
    defense_patch = _symbol_trim_patch(trim_fraction, EXTENDED_DRAG_SYMBOLS)
    weak_switch_count = 0
    defense_dates: list[str] = []

    def _gap_ok(asof: pd.Timestamp) -> bool:
        if min_defense_gap_months <= 0 or not defense_dates:
            return True
        last = pd.Timestamp(defense_dates[-1])
        return (asof - last).days >= int(min_defense_gap_months * 30)

    def wrapped_build(metrics, flow_snapshot, cfg_inner, variant=None, prev_hold_keys=None, **kwargs):
        nonlocal weak_switch_count
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

        current_book = trim22_patch(book)
        if _weak_flow_trigger(current_book, threshold_gap=TRIM22_GAP, sector_bias_min=None):
            weak_switch_count += 1
            baseline_book = original(
                metrics,
                flow_snapshot,
                cfg_inner,
                variant=fallback_variant,
                prev_hold_keys=prev_hold_keys,
                **kwargs,
            )
            current_book = _carry_top_from_base(
                base_book=current_book,
                baseline_book=baseline_book,
                carry_count=TRIM22_CARRY_COUNT,
            )

        asof = pd.Timestamp(str(metrics["AsOfDate"].iloc[0]))
        if (
            (max_defense_count is None or len(defense_dates) < max_defense_count)
            and _gap_ok(asof)
            and _state_condition_trigger(
            current_book,
            min_symbol_weight=min_symbol_weight,
            min_sector_weight=min_sector_weight,
            require_weak_flow=require_weak_flow,
            require_drag_flow_weak=require_drag_flow_weak,
            )
        ):
            defense_dates.append(asof.strftime("%Y-%m-%d"))
            return defense_patch(current_book)
        return current_book

    bt._build_momentum_candidates_for_date = wrapped_build
    try:
        result = _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, variant)
        diagnostics = {
            "weak_switch_count": weak_switch_count,
            "defense_count": len(defense_dates),
            "first_defense_date": None if not defense_dates else defense_dates[0],
            "last_defense_date": None if not defense_dates else defense_dates[-1],
            "defense_dates": defense_dates,
        }
        return result, diagnostics
    finally:
        bt._build_momentum_candidates_for_date = original


def _walkforward_compare(result: dict[str, pd.DataFrame], base_result: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    walk = _walkforward_summary(result["nav"], window_months=24, step_months=12)
    base_walk = _walkforward_summary(base_result["nav"], window_months=24, step_months=12)
    compare = walk[["WindowStart", "WindowEnd", "CAGR", "Sharpe"]].merge(
        base_walk[["WindowStart", "WindowEnd", "CAGR", "Sharpe"]],
        on=["WindowStart", "WindowEnd"],
        how="inner",
        suffixes=("_candidate", "_base"),
    )
    compare["CAGRDelta"] = (
        pd.to_numeric(compare["CAGR_candidate"], errors="coerce")
        - pd.to_numeric(compare["CAGR_base"], errors="coerce")
    )
    compare["SharpeDelta"] = (
        pd.to_numeric(compare["Sharpe_candidate"], errors="coerce")
        - pd.to_numeric(compare["Sharpe_base"], errors="coerce")
    )
    for column in ("WindowStart", "WindowEnd"):
        compare[column] = pd.to_datetime(compare[column]).dt.strftime("%Y-%m-%d")
    return compare.to_dict(orient="records")


def _compose_variant_name(
    *,
    min_symbol_weight: float,
    min_sector_weight: float,
    require_weak_flow: bool,
    require_drag_flow_weak: bool,
    max_defense_count: int | None,
    min_defense_gap_months: int = 0,
    trim_fraction: float,
) -> str:
    flow_tag = "weakflow" if require_weak_flow else "state"
    drag_flow_tag = "_dragweak" if require_drag_flow_weak else ""
    max_tag = "" if max_defense_count is None else f"_max{max_defense_count:02d}"
    gap_tag = "" if min_defense_gap_months <= 0 else f"_gapm{min_defense_gap_months:02d}"
    return (
        f"{BASE_VARIANT}_trim22_{flow_tag}{drag_flow_tag}_extsymbol"
        f"_sym{int(round(min_symbol_weight * 100)):02d}"
        f"_sector{int(round(min_sector_weight * 100)):02d}"
        f"_trim{int(round(trim_fraction * 100)):02d}"
        f"{max_tag}"
        f"{gap_tag}"
    )


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion State-Condition Defense Sweep",
        "",
        "## Purpose",
        "",
        "- replace the fixed historical drawdown-window defense with observable portfolio-state triggers",
        "- keep the same trim22 branch and KR ETF redistribution target, but remove date-window gating",
        "",
        "## Best Result",
        "",
        f"- best variant: `{summary['best_variant']}`",
        f"- best CAGR: `{_pct(summary['best_cagr'])}`",
        f"- best MDD: `{_pct(summary['best_mdd'])}`",
        f"- best Sharpe: `{summary['best_sharpe']:.4f}`",
        f"- best defense count: `{summary['best_defense_count']}`",
        "",
        "## Ranked Rows",
        "",
        "| Rank | Variant | CAGR | MDD | Sharpe | Neg WF | Defenses | First | Last |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | {_pct(row['CAGR'])} | {_pct(row['MDD'])} | "
            f"{row['Sharpe']:.4f} | {int(row['NegativeCAGRWindows'])} | {int(row['DefenseCount'])} | "
            f"`{row['FirstDefenseDate'] or '-'}` | `{row['LastDefenseDate'] or '-'}` |"
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

    grid = [
        (0.09, 0.28, False, False, 4, 1.00),
        (0.09, 0.28, False, False, 6, 1.00),
        (0.09, 0.28, False, False, 8, 1.00),
        (0.10, 0.30, False, False, 4, 1.00),
        (0.10, 0.30, False, False, 6, 1.00),
        (0.10, 0.30, False, False, 8, 1.00),
    ]

    rows: list[dict[str, object]] = []
    for min_symbol_weight, min_sector_weight, require_weak_flow, require_drag_flow_weak, max_defense_count, trim_fraction in grid:
        variant_name = _compose_variant_name(
            min_symbol_weight=min_symbol_weight,
            min_sector_weight=min_sector_weight,
            require_weak_flow=require_weak_flow,
            require_drag_flow_weak=require_drag_flow_weak,
            max_defense_count=max_defense_count,
            trim_fraction=trim_fraction,
        )
        variant = replace(strongest, name=variant_name)
        result, diagnostics = _run_state_condition_defense(
            variant=variant,
            fallback_variant=baseline,
            min_symbol_weight=min_symbol_weight,
            min_sector_weight=min_sector_weight,
            require_weak_flow=require_weak_flow,
            require_drag_flow_weak=require_drag_flow_weak,
            max_defense_count=max_defense_count,
            trim_fraction=trim_fraction,
            universe=universe,
            price_cache=price_cache,
            flow_cache=flow_cache,
            monthly_close=monthly_close,
            signal_dates=signal_dates,
            cfg=cfg,
        )
        row = _summarize_candidate(variant_name, result, strongest_result)
        row["MinSymbolWeight"] = min_symbol_weight
        row["MinSectorWeight"] = min_sector_weight
        row["RequireWeakFlow"] = require_weak_flow
        row["RequireDragFlowWeak"] = require_drag_flow_weak
        row["MaxDefenseCount"] = max_defense_count
        row["TrimFraction"] = trim_fraction
        row["WeakSwitchCount"] = int(diagnostics["weak_switch_count"])
        row["DefenseCount"] = int(diagnostics["defense_count"])
        row["FirstDefenseDate"] = diagnostics["first_defense_date"]
        row["LastDefenseDate"] = diagnostics["last_defense_date"]
        row["DefenseDates"] = diagnostics["defense_dates"]
        row["WalkforwardCompare"] = _walkforward_compare(result, strongest_result)
        rows.append(row)

    compare = pd.DataFrame(rows)
    compare["MDDBucket"] = compare["MDD"].round(9)
    compare = compare.sort_values(
        ["NegativeCAGRWindows", "MDDBucket", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "state_condition_defense_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "schema_version": "1.0.0",
        "base_variant": BASE_VARIANT,
        "best_variant": str(best["Variant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_negative_cagr_windows": int(best["NegativeCAGRWindows"]),
        "best_min_symbol_weight": float(best["MinSymbolWeight"]),
        "best_min_sector_weight": float(best["MinSectorWeight"]),
        "best_require_weak_flow": bool(best["RequireWeakFlow"]),
        "best_require_drag_flow_weak": bool(best["RequireDragFlowWeak"]),
        "best_max_defense_count": None if pd.isna(best["MaxDefenseCount"]) else int(best["MaxDefenseCount"]),
        "best_trim_fraction": float(best["TrimFraction"]),
        "best_weak_switch_count": int(best["WeakSwitchCount"]),
        "best_defense_count": int(best["DefenseCount"]),
        "best_first_defense_date": None if pd.isna(best["FirstDefenseDate"]) else str(best["FirstDefenseDate"]),
        "best_last_defense_date": None if pd.isna(best["LastDefenseDate"]) else str(best["LastDefenseDate"]),
        "best_defense_dates": list(best["DefenseDates"]),
        "uses_explicit_historical_dates": False,
        "ranked_rows": compare.to_dict(orient="records"),
    }
    if (
        summary["best_negative_cagr_windows"] == 0
        and summary["best_defense_count"] > 0
        and summary["best_mdd"] > OPERATING_BASELINE_MDD
    ):
        summary["verdict"] = (
            f"the state-condition defense removes fixed date-window gating: `{summary['best_variant']}` reaches "
            f"{_pct(summary['best_cagr'])} CAGR and {_pct(summary['best_mdd'])} MDD with "
            f"{summary['best_defense_count']} condition-triggered defenses."
        )
    else:
        summary["verdict"] = (
            "the state-condition defense did not produce a usable non-date candidate; keep the candidate blocked "
            "and search for a different observable risk trigger."
        )

    (OUTPUT_DIR / "state_condition_defense_sweep_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "state_condition_defense_sweep_review.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
