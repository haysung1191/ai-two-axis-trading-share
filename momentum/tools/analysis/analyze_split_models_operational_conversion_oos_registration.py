from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_oos_registration"
CANDIDATE_LADDER_JSON = (
    ROOT / "output" / "split_models_operational_conversion_candidate_ladder" / "candidate_ladder_summary.json"
)
VALIDATION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_drawdown_window_defense_validation"
    / "drawdown_window_defense_validation_latest.json"
)
STATE_CONDITION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_state_condition_defense_sweep"
    / "state_condition_defense_sweep_summary.json"
)
TARGETED_MDD_GUARD_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_targeted_mdd_guard_sweep"
    / "targeted_mdd_guard_sweep_summary.json"
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_markdown(summary: dict[str, object]) -> str:
    checks = "\n".join(
        f"- `{row['id']}`: {'PASS' if row['passed'] else 'BLOCK'}"
        for row in summary["checklist"]
    )
    return f"""# Split Models Operational Conversion OOS Registration

Generated: `{summary['generated_at']}`

## Status

- Status: `{summary['status']}`
- Candidate ID: `{summary['candidate_id']}`
- Variant: `{summary['variant']}`
- Stage: `{summary['next_stage']}`

## Metrics

- CAGR: `{summary['metrics']['cagr']:.2%}`
- MDD: `{summary['metrics']['mdd']:.2%}`
- Sharpe: `{summary['metrics']['sharpe']:.4f}`
- MDD margin vs operating baseline: `{summary['metrics']['mdd_margin_vs_operating_baseline']:.2%}`

## Checklist

{checks}

## Required Next Gates

```json
{json.dumps(summary['required_next_gates'], indent=2)}
```

## Non Goals

```json
{json.dumps(summary['non_goals'], indent=2)}
```
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ladder = _load_json(CANDIDATE_LADDER_JSON)
    validation = _load_json(VALIDATION_JSON)
    targeted_guard = _load_json(TARGETED_MDD_GUARD_JSON) if TARGETED_MDD_GUARD_JSON.exists() else {}
    state_condition = _load_json(STATE_CONDITION_JSON) if STATE_CONDITION_JSON.exists() else {}
    best_targeted_spec = next(
        (
            row
            for row in targeted_guard.get("ranked_specs", [])
            if row.get("all_shifts_pass")
            and int(row.get("worst_shift_negative_wf", 999)) == 0
            and float(row.get("worst_shift_mdd") or -1.0) > -0.25241596238415986
            and float(row.get("worst_shift_cagr") or 0.0) > 0.50
        ),
        None,
    )
    targeted_guard_usable = (
        bool(targeted_guard)
        and targeted_guard.get("sweep_decision") == "PASS_TARGETED_MDD_GUARD_FOUND"
        and best_targeted_spec is not None
    )
    state_condition_usable = (
        bool(state_condition)
        and not bool(state_condition.get("uses_explicit_historical_dates"))
        and int(state_condition.get("best_negative_cagr_windows", 999)) == 0
        and float(state_condition.get("best_mdd") or -1.0) > -0.25241596238415986
        and "removes fixed date-window gating" in str(state_condition.get("verdict") or "")
    )
    if targeted_guard_usable:
        shift_rows = best_targeted_spec.get("shift_rows") or []
        candidate = {
            "variant": best_targeted_spec["variant"],
            "cagr": best_targeted_spec["worst_shift_cagr"],
            "mdd": best_targeted_spec["worst_shift_mdd"],
            "sharpe": min(float(row["Sharpe"]) for row in shift_rows) if shift_rows else 0.0,
            "mdd_margin_vs_operating_baseline": float(best_targeted_spec["worst_shift_mdd"])
            - (-0.25241596238415986),
            "window_start": None,
            "window_end": None,
            "window_defense_count": max(int(row.get("DefenseCount", 0)) for row in shift_rows) if shift_rows else 0,
        }
        candidate_id = "MOM-CONV-TMG-001"
        source_family = "tail_release_top25_mid75_pen35_floor25_targeted_mdd_guard"
        registration_type = "targeted_mdd_guard_risk_conversion_candidate"
    elif state_condition_usable:
        candidate = {
            "variant": state_condition["best_variant"],
            "cagr": state_condition["best_cagr"],
            "mdd": state_condition["best_mdd"],
            "sharpe": state_condition["best_sharpe"],
            "mdd_margin_vs_operating_baseline": float(state_condition["best_mdd"]) - (-0.25241596238415986),
            "window_start": None,
            "window_end": None,
            "window_defense_count": int(state_condition["best_defense_count"]),
        }
        candidate_id = "MOM-CONV-SCD-001"
        source_family = "tail_release_top25_mid75_pen35_floor25_state_condition"
        registration_type = "generalized_risk_conversion_candidate"
    else:
        candidate = validation["candidate"]
        candidate_id = "MOM-CONV-DDW-001"
        source_family = "tail_release_top25_mid75_pen35_floor25"
        registration_type = "risk_conversion_candidate"
    variant = str(candidate["variant"])
    checklist = [
        {
            "id": "candidate_matches_ladder_drawdown_window_defense",
            "passed": targeted_guard_usable or state_condition_usable or variant == ladder.get("drawdown_window_defense_variant"),
            "evidence": str(
                TARGETED_MDD_GUARD_JSON
                if targeted_guard_usable
                else STATE_CONDITION_JSON
                if state_condition_usable
                else CANDIDATE_LADDER_JSON
            ),
        },
        {
            "id": "first_order_metric_validation_passed",
            "passed": targeted_guard_usable
            or state_condition_usable
            or validation.get("validation_decision") == "PASS_FIRST_ORDER_METRIC_VALIDATION",
            "evidence": str(
                TARGETED_MDD_GUARD_JSON
                if targeted_guard_usable
                else STATE_CONDITION_JSON
                if state_condition_usable
                else VALIDATION_JSON
            ),
        },
        {
            "id": "mdd_margin_positive",
            "passed": float(candidate.get("mdd_margin_vs_operating_baseline") or 0.0) > 0.0,
            "evidence": str(VALIDATION_JSON),
        },
    ]
    status = "REGISTERED_FOR_OOS_ROBUSTNESS" if all(row["passed"] for row in checklist) else "BLOCK_REGISTRATION"
    summary = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "candidate_id": candidate_id,
        "variant": variant,
        "source_family": source_family,
        "registration_type": registration_type,
        "next_stage": "OOS_ROBUSTNESS_VALIDATION",
        "metrics": {
            "cagr": float(candidate["cagr"]),
            "mdd": float(candidate["mdd"]),
            "sharpe": float(candidate["sharpe"]),
            "mdd_margin_vs_operating_baseline": float(candidate["mdd_margin_vs_operating_baseline"]),
        },
        "defense_spec": {
            "window_start": candidate["window_start"],
            "window_end": candidate["window_end"],
            "window_defense_count": int(candidate["window_defense_count"]),
            "uses_explicit_historical_dates": not (targeted_guard_usable or state_condition_usable),
            "trigger_type": (
                "state_condition_energy_cooldown_guard"
                if targeted_guard_usable
                else "state_condition_max_defense"
                if state_condition_usable
                else "fixed_historical_window"
            ),
            "max_defense_count": 8
            if targeted_guard_usable
            else state_condition.get("best_max_defense_count")
            if state_condition_usable
            else None,
            "guard_mode": best_targeted_spec.get("guard_mode") if targeted_guard_usable else None,
            "guard_exposure": best_targeted_spec.get("guard_exposure") if targeted_guard_usable else None,
            "energy_threshold": best_targeted_spec.get("energy_threshold") if targeted_guard_usable else None,
            "kr_etf_threshold": best_targeted_spec.get("kr_etf_threshold") if targeted_guard_usable else None,
            "it_threshold": best_targeted_spec.get("it_threshold") if targeted_guard_usable else None,
            "cooldown_months": 2 if targeted_guard_usable else None,
            "description": (
                "After state-condition defense, apply a targeted exposure guard during energy-heavy cooldown months to preserve high return while keeping OOS MDD under the operating baseline."
                if targeted_guard_usable
                else
                "When observable extended-drag symbol/sector weights exceed the registered thresholds, remove AMD, COP, and XLE from the trim22 branch and redistribute released weight to KR ETF recipients, capped by max defense count."
                if state_condition_usable
                else "During the diagnosed drawdown window, remove the extended drag symbols AMD, COP, and XLE from the trim22 branch and redistribute released weight to KR ETF recipients."
            ),
        },
        "checklist": checklist,
        "required_next_gates": [
            "OOS_START_SHIFT",
            "PARAMETER_SENSITIVITY",
            "WINDOW_OVERFIT_DIAGNOSTIC",
            "COST_AND_TURNOVER_STRESS",
            "NO_SUBMIT_SHADOW_DRY_RUN_BEFORE_OPERATIONS",
        ],
        "promotion_decision": "NOT_OPERATION_READY",
        "non_goals": [
            "does_not_enable_paper",
            "does_not_enable_live",
            "does_not_enable_broker_submit",
            "does_not_create_order_intent",
        ],
        "source_files": {
            "candidate_ladder": str(CANDIDATE_LADDER_JSON),
            "first_order_validation": str(VALIDATION_JSON),
            "state_condition_sweep": str(STATE_CONDITION_JSON),
            "targeted_mdd_guard_sweep": str(TARGETED_MDD_GUARD_JSON),
        },
    }
    (OUTPUT_DIR / "oos_registration_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "oos_registration.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
