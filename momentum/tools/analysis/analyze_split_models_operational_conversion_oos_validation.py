from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from split_models.backtest import BacktestConfig, _baseline_variant_map, _run_trading_backtest_variant
from tools.analysis.analyze_split_models_operational_conversion_baseline_switch_sweep import (
    BASELINE_VARIANT,
    STRONGEST_VARIANT,
)
from tools.analysis.analyze_split_models_operational_conversion_state_condition_defense_sweep import (
    OPERATING_BASELINE_MDD,
    _compose_variant_name,
    _run_state_condition_defense,
)
from tools.analysis.analyze_split_models_operational_conversion_targeted_mdd_guard_sweep import _run_targeted_guard
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import _pct
from tools.analysis.analyze_split_models_tradeoff_frontier import _build_context, _summarize_candidate


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_oos_validation"
REGISTRATION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_oos_registration"
    / "oos_registration_summary.json"
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pass_metrics(row: dict[str, object]) -> bool:
    return (
        int(row.get("NegativeCAGRWindows", 999)) == 0
        and float(row.get("MDD") or -1.0) > OPERATING_BASELINE_MDD
        and float(row.get("CAGR") or 0.0) > 0.50
        and float(row.get("DefenseCount", 0)) > 0
    )


def _run_candidate(
    *,
    strongest,
    baseline,
    universe,
    price_cache,
    flow_cache,
    monthly_close,
    signal_dates: list[pd.Timestamp],
    cfg: BacktestConfig,
    min_symbol_weight: float,
    min_sector_weight: float,
    max_defense_count: int,
    min_defense_gap_months: int = 0,
    trim_fraction: float = 1.0,
) -> dict[str, object]:
    strongest_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, strongest
    )
    variant_name = _compose_variant_name(
        min_symbol_weight=min_symbol_weight,
        min_sector_weight=min_sector_weight,
        require_weak_flow=False,
        require_drag_flow_weak=False,
        max_defense_count=max_defense_count,
        min_defense_gap_months=min_defense_gap_months,
        trim_fraction=trim_fraction,
    )
    result, diagnostics = _run_state_condition_defense(
        variant=replace(strongest, name=variant_name),
        fallback_variant=baseline,
        min_symbol_weight=min_symbol_weight,
        min_sector_weight=min_sector_weight,
        require_weak_flow=False,
        require_drag_flow_weak=False,
        max_defense_count=max_defense_count,
        min_defense_gap_months=min_defense_gap_months,
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
    row["MaxDefenseCount"] = max_defense_count
    row["MinDefenseGapMonths"] = min_defense_gap_months
    row["TrimFraction"] = trim_fraction
    row["DefenseCount"] = int(diagnostics["defense_count"])
    row["FirstDefenseDate"] = diagnostics["first_defense_date"]
    row["LastDefenseDate"] = diagnostics["last_defense_date"]
    row["DefenseDates"] = diagnostics["defense_dates"]
    row["PassMetrics"] = _pass_metrics(row)
    return row


def _run_targeted_guard_candidate(
    *,
    strongest,
    baseline,
    universe,
    price_cache,
    flow_cache,
    monthly_close,
    signal_dates: list[pd.Timestamp],
    cfg: BacktestConfig,
    variant_name: str,
    spec: dict[str, object],
) -> dict[str, object]:
    strongest_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, strongest
    )
    result, diagnostics = _run_targeted_guard(
        variant=replace(strongest, name=variant_name),
        fallback_variant=baseline,
        spec=spec,
        universe=universe,
        price_cache=price_cache,
        flow_cache=flow_cache,
        monthly_close=monthly_close,
        signal_dates=signal_dates,
        cfg=cfg,
    )
    row = _summarize_candidate(variant_name, result, strongest_result)
    row["Spec"] = (
        f"{spec['guard_mode']}:exposure={float(spec['guard_exposure']):.3f},"
        f"energy={float(spec['energy_threshold']):.2f}"
    )
    row["GuardMode"] = str(spec["guard_mode"])
    row["GuardExposure"] = float(spec["guard_exposure"])
    row["EnergyThreshold"] = float(spec["energy_threshold"])
    row["KrEtfThreshold"] = float(spec["kr_etf_threshold"])
    row["ItThreshold"] = float(spec["it_threshold"])
    row["DefenseCount"] = int(diagnostics["defense_count"])
    row["CooldownCount"] = int(diagnostics["cooldown_count"])
    row["GuardCount"] = int(diagnostics["guard_count"])
    row["FirstDefenseDate"] = diagnostics["first_defense_date"]
    row["LastDefenseDate"] = diagnostics["last_defense_date"]
    row["DefenseDates"] = diagnostics["defense_dates"]
    row["CooldownDates"] = diagnostics["cooldown_dates"]
    row["GuardDates"] = diagnostics["guard_dates"]
    row["PassMetrics"] = _pass_metrics(row)
    return row


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion OOS Validation",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "## Status",
        "",
        f"- Candidate: `{summary['candidate_id']}`",
        f"- Decision: `{summary['validation_decision']}`",
        f"- Start-shift: `{summary['start_shift_decision']}`",
        f"- Parameter sensitivity: `{summary['parameter_sensitivity_decision']}`",
        "",
        "## Start-Shift Rows",
        "",
        "| Shift | CAGR | MDD | Sharpe | Neg WF | Defense Count |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["start_shift_rows"]:
        lines.append(
            f"| {int(row['StartShiftMonths'])} | {_pct(row['CAGR'])} | {_pct(row['MDD'])} | "
            f"{row['Sharpe']:.4f} | {int(row['NegativeCAGRWindows'])} | {int(row['DefenseCount'])} |"
        )
    lines.extend(
        [
            "",
            "## Parameter Rows",
            "",
            "| Spec | CAGR | MDD | Sharpe | Neg WF | Defense Count |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["parameter_rows"]:
        lines.append(
            f"| `{row.get('Spec') or row.get('Variant')}` | {_pct(row['CAGR'])} | {_pct(row['MDD'])} | {row['Sharpe']:.4f} | "
            f"{int(row['NegativeCAGRWindows'])} | {int(row['DefenseCount'])} |"
        )
    lines.extend(["", "## Remaining Blockers", "", json.dumps(summary["remaining_blockers"], indent=2), ""])
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    registration = _load_json(REGISTRATION_JSON)
    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    variants = _baseline_variant_map()
    strongest = variants[STRONGEST_VARIANT]
    baseline = variants[BASELINE_VARIANT]

    defense_spec = registration.get("defense_spec") or {}
    targeted_guard_registered = defense_spec.get("trigger_type") == "state_condition_energy_cooldown_guard"
    base_targeted_spec = {
        "guard_mode": defense_spec.get("guard_mode") or "energy_cooldown",
        "guard_exposure": float(defense_spec.get("guard_exposure") or 0.88),
        "energy_threshold": float(defense_spec.get("energy_threshold") or 0.35),
        "kr_etf_threshold": float(defense_spec.get("kr_etf_threshold") or 0.45),
        "it_threshold": float(defense_spec.get("it_threshold") or 0.25),
    }
    base_params = {
        "min_symbol_weight": 0.09,
        "min_sector_weight": 0.28,
        "max_defense_count": 8,
        "trim_fraction": 1.0,
    }
    start_shift_rows: list[dict[str, object]] = []
    for start_shift_months in [0, 1, 2]:
        shifted_dates = signal_dates[start_shift_months:]
        if targeted_guard_registered:
            row = _run_targeted_guard_candidate(
                strongest=strongest,
                baseline=baseline,
                universe=universe,
                price_cache=price_cache,
                flow_cache=flow_cache,
                monthly_close=monthly_close,
                signal_dates=shifted_dates,
                cfg=cfg,
                variant_name=str(registration["variant"]),
                spec=base_targeted_spec,
            )
        else:
            row = _run_candidate(
                strongest=strongest,
                baseline=baseline,
                universe=universe,
                price_cache=price_cache,
                flow_cache=flow_cache,
                monthly_close=monthly_close,
                signal_dates=shifted_dates,
                cfg=cfg,
                **base_params,
            )
        row["StartShiftMonths"] = start_shift_months
        start_shift_rows.append(row)

    parameter_rows: list[dict[str, object]] = []
    if targeted_guard_registered:
        for spec in [
            base_targeted_spec,
            {**base_targeted_spec, "guard_exposure": 0.89},
            {**base_targeted_spec, "guard_exposure": 0.895},
        ]:
            suffix = int(round(float(spec["guard_exposure"]) * 1000))
            parameter_rows.append(
                _run_targeted_guard_candidate(
                    strongest=strongest,
                    baseline=baseline,
                    universe=universe,
                    price_cache=price_cache,
                    flow_cache=flow_cache,
                    monthly_close=monthly_close,
                    signal_dates=signal_dates,
                    cfg=cfg,
                    variant_name=f"targeted_mdd_guard_{spec['guard_mode']}_ex{suffix:03d}",
                    spec=spec,
                )
            )
    else:
        for params in [
            base_params,
            {"min_symbol_weight": 0.09, "min_sector_weight": 0.27, "max_defense_count": 8, "trim_fraction": 1.0},
            {"min_symbol_weight": 0.09, "min_sector_weight": 0.29, "max_defense_count": 8, "trim_fraction": 1.0},
        ]:
            parameter_rows.append(
                _run_candidate(
                    strongest=strongest,
                    baseline=baseline,
                    universe=universe,
                    price_cache=price_cache,
                    flow_cache=flow_cache,
                    monthly_close=monthly_close,
                    signal_dates=signal_dates,
                    cfg=cfg,
                    **params,
                )
            )

    start_shift_pass = all(bool(row["PassMetrics"]) for row in start_shift_rows)
    parameter_pass = all(bool(row["PassMetrics"]) for row in parameter_rows)
    blockers = []
    if not start_shift_pass:
        blockers.append("oos_start_shift_failed")
    if not parameter_pass:
        blockers.append("parameter_sensitivity_failed")
    summary = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": registration["candidate_id"],
        "variant": registration["variant"],
        "validation_decision": "PASS_OOS_VALIDATION" if not blockers else "BLOCK_OOS_VALIDATION",
        "start_shift_decision": "PASS" if start_shift_pass else "BLOCK",
        "parameter_sensitivity_decision": "PASS" if parameter_pass else "BLOCK",
        "pass_rule": {
            "negative_cagr_windows": 0,
            "mdd_must_exceed": OPERATING_BASELINE_MDD,
            "cagr_must_exceed": 0.50,
            "defense_count_must_exceed": 0,
        },
        "start_shift_rows": start_shift_rows,
        "parameter_rows": parameter_rows,
        "remaining_blockers": blockers,
        "safety": {
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "order_intent_created": False,
        },
    }
    (OUTPUT_DIR / "oos_validation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "oos_validation.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
