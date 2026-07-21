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
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import _pct
from tools.analysis.analyze_split_models_tradeoff_frontier import _build_context, _summarize_candidate


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_drawdown_window_defense_sweep"
MDD_TOL = 1e-9
TRIM22_FRACTION = 0.22
TRIM22_GAP = 0.02
TRIM22_CARRY_COUNT = 2
WINDOW_START = pd.Timestamp("2021-11-30")
WINDOW_END = pd.Timestamp("2022-08-31")
DRAG_SYMBOLS = {"AMD", "COP"}
EXTENDED_DRAG_SYMBOLS = {"AMD", "COP", "XLE"}
WIDE_DRAG_SYMBOLS = {"AMD", "COP", "XLE", "214370", "T"}
DRAG_SECTORS = {"Information Technology", "Energy"}


def _normalize(book: pd.DataFrame) -> pd.DataFrame:
    out = book.copy()
    out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
    total = float(out["TargetWeight"].sum())
    if total > 0:
        out["TargetWeight"] = out["TargetWeight"] / total
    return out


def _redistribute_released_to_kr_etf(out: pd.DataFrame, released: float, excluded_index: set[int]) -> pd.DataFrame:
    if released <= 0 or out.empty:
        return out
    recipients = out.loc[
        out["Market"].astype(str).eq("KR")
        & out["Sector"].astype(str).eq("ETF")
        & ~out.index.isin(excluded_index)
    ].copy()
    if recipients.empty:
        return _normalize(out)
    weights = pd.to_numeric(recipients["TargetWeight"], errors="coerce").fillna(0.0)
    total = float(weights.sum())
    if total > 0:
        out.loc[recipients.index, "TargetWeight"] = weights + released * (weights / total)
    else:
        out.loc[recipients.index, "TargetWeight"] = weights + released / float(len(recipients))
    return _normalize(out)


def _symbol_trim_patch(trim_fraction: float, symbols: set[str] | None = None) -> Callable[[pd.DataFrame], pd.DataFrame]:
    target_symbols = symbols or DRAG_SYMBOLS

    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty:
            return book
        out = book.copy()
        out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
        mask = out["Symbol"].astype(str).isin(target_symbols)
        trim_index = set(out.loc[mask].index)
        released = float((out.loc[mask, "TargetWeight"] * trim_fraction).sum())
        out.loc[mask, "TargetWeight"] = out.loc[mask, "TargetWeight"] * (1.0 - trim_fraction)
        return _redistribute_released_to_kr_etf(out, released, trim_index)

    return patch


def _sector_trim_patch(trim_fraction: float) -> Callable[[pd.DataFrame], pd.DataFrame]:
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty:
            return book
        out = book.copy()
        out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
        mask = out["Market"].astype(str).eq("US") & out["Sector"].astype(str).isin(DRAG_SECTORS)
        trim_index = set(out.loc[mask].index)
        released = float((out.loc[mask, "TargetWeight"] * trim_fraction).sum())
        out.loc[mask, "TargetWeight"] = out.loc[mask, "TargetWeight"] * (1.0 - trim_fraction)
        return _redistribute_released_to_kr_etf(out, released, trim_index)

    return patch


def _run_window_defense(
    *,
    variant: TradingVariant,
    fallback_variant: TradingVariant,
    window_patch: Callable[[pd.DataFrame], pd.DataFrame] | None,
    window_baseline_carry_count: int | None,
    universe: pd.DataFrame,
    price_cache: dict[str, pd.DataFrame],
    flow_cache: dict[str, pd.DataFrame],
    monthly_close: pd.DataFrame,
    signal_dates: list[pd.Timestamp],
    cfg: BacktestConfig,
) -> tuple[dict[str, pd.DataFrame], int, int]:
    original = bt._build_momentum_candidates_for_date
    trim22_patch = _trim22_patch_factory(TRIM22_FRACTION)
    weak_switch_count = 0
    window_defense_count = 0

    def wrapped_build(metrics, flow_snapshot, cfg_inner, variant=None, prev_hold_keys=None, **kwargs):
        nonlocal weak_switch_count, window_defense_count
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
        if WINDOW_START <= asof <= WINDOW_END:
            window_defense_count += 1
            baseline_book = original(
                metrics,
                flow_snapshot,
                cfg_inner,
                variant=fallback_variant,
                prev_hold_keys=prev_hold_keys,
                **kwargs,
            )
            if window_baseline_carry_count is not None:
                return _carry_top_from_base(
                    base_book=current_book,
                    baseline_book=baseline_book,
                    carry_count=window_baseline_carry_count,
                )
            if window_patch is not None:
                return window_patch(current_book)
        return current_book

    bt._build_momentum_candidates_for_date = wrapped_build
    try:
        result = _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, variant)
        return result, weak_switch_count, window_defense_count
    finally:
        bt._build_momentum_candidates_for_date = original


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Drawdown Window Defense Sweep",
        "",
        "## Purpose",
        "",
        "- directly target the unresolved drawdown window from 2021-11-30 through 2022-08-31",
        "- start from the current best `trim22` branch and apply only window-scoped defenses",
        "",
        "## Best Result",
        "",
        f"- best variant: `{summary['best_variant']}`",
        f"- best CAGR: `{_pct(summary['best_cagr'])}`",
        f"- best MDD: `{_pct(summary['best_mdd'])}`",
        f"- best Sharpe: `{summary['best_sharpe']:.4f}`",
        "",
        "## Ranked Rows",
        "",
        "| Rank | Variant | CAGR | MDD | Sharpe | Weak Switches | Window Defenses |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | {_pct(row['CAGR'])} | {_pct(row['MDD'])} | "
            f"{row['Sharpe']:.4f} | {int(row['WeakSwitchCount'])} | {int(row['WindowDefenseCount'])} |"
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

    grid: list[dict[str, object]] = [
        {"name": "trim22_window_baseline_carry0", "patch": None, "carry": 0},
        {"name": "trim22_window_baseline_carry1", "patch": None, "carry": 1},
        {"name": "trim22_window_baseline_carry2", "patch": None, "carry": 2},
        {"name": "trim22_window_symbol_trim25", "patch": _symbol_trim_patch(0.25), "carry": None},
        {"name": "trim22_window_symbol_trim50", "patch": _symbol_trim_patch(0.50), "carry": None},
        {"name": "trim22_window_symbol_trim100", "patch": _symbol_trim_patch(1.00), "carry": None},
        {
            "name": "trim22_window_extsymbol_trim100",
            "patch": _symbol_trim_patch(1.00, EXTENDED_DRAG_SYMBOLS),
            "carry": None,
        },
        {
            "name": "trim22_window_widesymbol_trim100",
            "patch": _symbol_trim_patch(1.00, WIDE_DRAG_SYMBOLS),
            "carry": None,
        },
        {"name": "trim22_window_sector_trim25", "patch": _sector_trim_patch(0.25), "carry": None},
        {"name": "trim22_window_sector_trim50", "patch": _sector_trim_patch(0.50), "carry": None},
    ]

    rows: list[dict[str, object]] = []
    base_name = "tail_release_top25_mid75_pen35_floor25_conccarrykretfmicro_ct70_trim22_gap02_top2"
    for spec in grid:
        variant_name = f"{BASE_VARIANT}_{spec['name']}"
        variant = replace(strongest, name=variant_name)
        result, weak_switch_count, window_defense_count = _run_window_defense(
            variant=variant,
            fallback_variant=baseline,
            window_patch=spec["patch"],
            window_baseline_carry_count=spec["carry"],
            universe=universe,
            price_cache=price_cache,
            flow_cache=flow_cache,
            monthly_close=monthly_close,
            signal_dates=signal_dates,
            cfg=cfg,
        )
        row = _summarize_candidate(variant_name, result, strongest_result)
        row["WeakSwitchCount"] = weak_switch_count
        row["WindowDefenseCount"] = window_defense_count
        rows.append(row)

    compare = pd.DataFrame(rows)
    compare["MDDBucket"] = compare["MDD"].round(9)
    compare = compare.sort_values(
        ["NegativeCAGRWindows", "MDDBucket", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "drawdown_window_defense_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "base_variant": base_name,
        "window_start": WINDOW_START.date().isoformat(),
        "window_end": WINDOW_END.date().isoformat(),
        "best_variant": str(best["Variant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_weak_switch_count": int(best["WeakSwitchCount"]),
        "best_window_defense_count": int(best["WindowDefenseCount"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    if float(best["MDD"]) > -0.3065255636909545 + MDD_TOL:
        summary["verdict"] = (
            f"the drawdown-window defense improves beyond trim22: `{summary['best_variant']}` reaches "
            f"{_pct(summary['best_cagr'])} CAGR and {_pct(summary['best_mdd'])} MDD."
        )
    else:
        summary["verdict"] = (
            "the drawdown-window defense axis does not beat the current trim22 MDD; the bottleneck likely needs "
            "a different entry/filter rule rather than post-selection trimming."
        )

    (OUTPUT_DIR / "drawdown_window_defense_sweep_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "drawdown_window_defense_sweep_review.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
