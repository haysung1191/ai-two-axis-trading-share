from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Callable

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import split_models.backtest as bt
from split_models.backtest import BacktestConfig, TradingVariant, _baseline_variant_map, _run_trading_backtest_variant
from tools.analysis.analyze_split_models_operational_conversion_baseline_switch_carry_sweep import _carry_top_from_base
from tools.analysis.analyze_split_models_operational_conversion_baseline_switch_sweep import (
    BASELINE_VARIANT,
    STRONGEST_VARIANT,
    _weak_flow_trigger,
)
from tools.analysis.analyze_split_models_operational_conversion_concentration_carry_kr_etf_trim_micro import (
    _compose_patch as _trim22_patch_factory,
)
from tools.analysis.analyze_split_models_operational_conversion_drawdown_window_defense_sweep import (
    EXTENDED_DRAG_SYMBOLS,
    _redistribute_released_to_kr_etf,
)
from tools.analysis.analyze_split_models_operational_conversion_oos_validation import _pass_metrics
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import _pct
from tools.analysis.analyze_split_models_operational_conversion_state_condition_defense_sweep import _state_condition_trigger
from tools.analysis.analyze_split_models_tradeoff_frontier import _build_context, _summarize_candidate


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_post_defense_cooldown_sweep"
TRIM22_FRACTION = 0.22
TRIM22_GAP = 0.02
TRIM22_CARRY_COUNT = 2


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


def _run_post_defense_cooldown(
    *,
    variant: TradingVariant,
    fallback_variant: TradingVariant,
    cooldown_months: int,
    cooldown_mode: str,
    cooldown_exposure: float,
    universe: pd.DataFrame,
    price_cache: dict[str, pd.DataFrame],
    flow_cache: dict[str, pd.DataFrame],
    monthly_close: pd.DataFrame,
    signal_dates: list[pd.Timestamp],
    cfg: BacktestConfig,
) -> tuple[dict[str, pd.DataFrame], dict[str, object]]:
    original = bt._build_momentum_candidates_for_date
    trim22_patch = _trim22_patch_factory(TRIM22_FRACTION)
    defense_patch = _symbol_trim_patch(1.0, EXTENDED_DRAG_SYMBOLS)
    weak_switch_count = 0
    cooldown_remaining = 0
    defense_dates: list[str] = []
    cooldown_dates: list[str] = []

    def _apply_cooldown_exposure(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or float(cooldown_exposure) == 1.0:
            return book
        out = book.copy()
        out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
        out["TargetWeight"] = out["TargetWeight"] * float(cooldown_exposure)
        return out

    def wrapped_build(metrics, flow_snapshot, cfg_inner, variant=None, prev_hold_keys=None, **kwargs):
        nonlocal weak_switch_count, cooldown_remaining
        variant_inner = variant
        raw_book = original(
            metrics,
            flow_snapshot,
            cfg_inner,
            variant=variant_inner,
            prev_hold_keys=prev_hold_keys,
            **kwargs,
        )
        if variant_inner.name != variant.name:
            return raw_book

        asof = pd.Timestamp(str(metrics["AsOfDate"].iloc[0])).strftime("%Y-%m-%d")
        if cooldown_remaining > 0:
            cooldown_remaining -= 1
            cooldown_dates.append(asof)
            if cooldown_mode == "fallback":
                fallback_book = original(
                    metrics,
                    flow_snapshot,
                    cfg_inner,
                    variant=fallback_variant,
                    prev_hold_keys=prev_hold_keys,
                    **kwargs,
                )
                return _apply_cooldown_exposure(fallback_book)
            return _apply_cooldown_exposure(raw_book)

        current_book = trim22_patch(raw_book)
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

        if (
            len(defense_dates) < 8
            and _state_condition_trigger(
                current_book,
                min_symbol_weight=0.09,
                min_sector_weight=0.28,
                require_weak_flow=False,
                require_drag_flow_weak=False,
            )
        ):
            defense_dates.append(asof)
            cooldown_remaining = max(int(cooldown_months), 0)
            return defense_patch(current_book)
        return current_book

    bt._build_momentum_candidates_for_date = wrapped_build
    try:
        result = _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, variant)
        diagnostics = {
            "weak_switch_count": weak_switch_count,
            "defense_count": len(defense_dates),
            "cooldown_count": len(cooldown_dates),
            "first_defense_date": None if not defense_dates else defense_dates[0],
            "last_defense_date": None if not defense_dates else defense_dates[-1],
            "defense_dates": defense_dates,
            "cooldown_dates": cooldown_dates,
        }
        return result, diagnostics
    finally:
        bt._build_momentum_candidates_for_date = original


def _run_candidate(
    *,
    strongest: TradingVariant,
    baseline: TradingVariant,
    base_result: dict[str, pd.DataFrame],
    universe: pd.DataFrame,
    price_cache: dict[str, pd.DataFrame],
    flow_cache: dict[str, pd.DataFrame],
    monthly_close: pd.DataFrame,
    signal_dates: list[pd.Timestamp],
    cfg: BacktestConfig,
    spec: dict[str, object],
) -> dict[str, object]:
    exposure = float(spec.get("cooldown_exposure", 1.0))
    variant_name = (
        f"post_defense_cooldown_{spec['cooldown_mode']}_m{int(spec['cooldown_months'])}"
        f"_ex{int(round(exposure * 100)):03d}"
    )
    result, diagnostics = _run_post_defense_cooldown(
        variant=replace(strongest, name=variant_name),
        fallback_variant=baseline,
        cooldown_months=int(spec["cooldown_months"]),
        cooldown_mode=str(spec["cooldown_mode"]),
        cooldown_exposure=exposure,
        universe=universe,
        price_cache=price_cache,
        flow_cache=flow_cache,
        monthly_close=monthly_close,
        signal_dates=signal_dates,
        cfg=cfg,
    )
    row = _summarize_candidate(variant_name, result, base_result)
    row.update(
        {
            "CooldownMonths": int(spec["cooldown_months"]),
            "CooldownMode": str(spec["cooldown_mode"]),
            "CooldownExposure": exposure,
            "DefenseCount": int(diagnostics["defense_count"]),
            "CooldownCount": int(diagnostics["cooldown_count"]),
            "FirstDefenseDate": diagnostics["first_defense_date"],
            "LastDefenseDate": diagnostics["last_defense_date"],
            "DefenseDates": diagnostics["defense_dates"],
            "CooldownDates": diagnostics["cooldown_dates"],
        }
    )
    row["PassMetrics"] = _pass_metrics(row)
    return row


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Post-Defense Cooldown Sweep",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        f"- decision: `{summary['sweep_decision']}`",
        f"- best variant: `{summary['best_variant']}`",
        f"- worst shift CAGR: `{_pct(summary['best_worst_shift_cagr'])}`",
        f"- worst shift MDD: `{_pct(summary['best_worst_shift_mdd'])}`",
        f"- worst shift negative WF: `{summary['best_worst_shift_negative_wf']}`",
        "",
        "## Ranked Specs",
        "",
        "| Rank | Mode | Months | Exposure | Pass | Passed Shifts | Worst CAGR | Worst MDD | Worst Neg WF |",
        "| ---: | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_specs"], start=1):
        lines.append(
            f"| {idx} | `{row['cooldown_mode']}` | {int(row['cooldown_months'])} | "
            f"{_pct(row.get('cooldown_exposure', 1.0))} | "
            f"`{row['all_shifts_pass']}` | {int(row['passed_shift_count'])} | "
            f"{_pct(row['worst_shift_cagr'])} | {_pct(row['worst_shift_mdd'])} | "
            f"{int(row['worst_shift_negative_wf'])} |"
        )
    lines.extend(["", "## Safety", "", json.dumps(summary["safety"], indent=2), ""])
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    variants = _baseline_variant_map()
    strongest = variants[STRONGEST_VARIANT]
    baseline = variants[BASELINE_VARIANT]
    specs = [
        {"cooldown_mode": "raw", "cooldown_months": 2, "cooldown_exposure": 0.99},
        {"cooldown_mode": "raw", "cooldown_months": 2, "cooldown_exposure": 0.98},
        {"cooldown_mode": "raw", "cooldown_months": 2, "cooldown_exposure": 0.97},
        {"cooldown_mode": "raw", "cooldown_months": 2, "cooldown_exposure": 0.96},
    ]
    spec_rows: list[dict[str, object]] = []
    all_rows: list[dict[str, object]] = []
    for spec in specs:
        shift_rows: list[dict[str, object]] = []
        for start_shift_months in [0, 1, 2]:
            shifted_dates = signal_dates[start_shift_months:]
            base_result = _run_trading_backtest_variant(
                universe, price_cache, flow_cache, monthly_close, shifted_dates, cfg, strongest
            )
            row = _run_candidate(
                strongest=strongest,
                baseline=baseline,
                base_result=base_result,
                universe=universe,
                price_cache=price_cache,
                flow_cache=flow_cache,
                monthly_close=monthly_close,
                signal_dates=shifted_dates,
                cfg=cfg,
                spec=spec,
            )
            row["StartShiftMonths"] = start_shift_months
            shift_rows.append(row)
            all_rows.append({**spec, **row})
        pass_flags = [bool(row["PassMetrics"]) for row in shift_rows]
        spec_rows.append(
            {
                **spec,
                "variant": str(shift_rows[0]["Variant"]),
                "all_shifts_pass": all(pass_flags),
                "passed_shift_count": int(sum(pass_flags)),
                "worst_shift_cagr": float(min(float(row["CAGR"]) for row in shift_rows)),
                "worst_shift_mdd": float(min(float(row["MDD"]) for row in shift_rows)),
                "worst_shift_negative_wf": int(max(int(row["NegativeCAGRWindows"]) for row in shift_rows)),
                "shift_rows": shift_rows,
            }
        )
    ranked = sorted(
        spec_rows,
        key=lambda row: (
            not bool(row["all_shifts_pass"]),
            -int(row["passed_shift_count"]),
            int(row["worst_shift_negative_wf"]),
            -float(row["worst_shift_mdd"]),
            -float(row["worst_shift_cagr"]),
        ),
    )
    best = ranked[0]
    summary = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sweep_decision": "PASS_POST_DEFENSE_COOLDOWN_FOUND" if best["all_shifts_pass"] else "BLOCK_POST_DEFENSE_COOLDOWN",
        "best_variant": best["variant"],
        "best_worst_shift_cagr": best["worst_shift_cagr"],
        "best_worst_shift_mdd": best["worst_shift_mdd"],
        "best_worst_shift_negative_wf": best["worst_shift_negative_wf"],
        "ranked_specs": ranked,
        "safety": {
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "order_intent_created": False,
        },
    }
    pd.DataFrame(all_rows).drop(columns=["DefenseDates", "CooldownDates"], errors="ignore").to_csv(
        OUTPUT_DIR / "post_defense_cooldown_sweep_rows.csv", index=False, encoding="utf-8-sig"
    )
    (OUTPUT_DIR / "post_defense_cooldown_sweep_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "post_defense_cooldown_sweep.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
