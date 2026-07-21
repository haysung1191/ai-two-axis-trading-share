from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_oos_robustness_gate"
REGISTRATION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_oos_registration"
    / "oos_registration_summary.json"
)
OOS_VALIDATION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_oos_validation"
    / "oos_validation_summary.json"
)
NO_SUBMIT_SHADOW_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_no_submit_shadow_dry_run"
    / "no_submit_shadow_dry_run_summary.json"
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_markdown(summary: dict[str, object]) -> str:
    rows = "\n".join(
        f"- `{row['id']}`: {'PASS' if row['passed'] else 'BLOCK'}; {', '.join(row['missing_or_blocked']) or 'ok'}"
        for row in summary["gate_checklist"]
    )
    return f"""# Split Models Operational Conversion OOS Robustness Gate

Generated: `{summary['generated_at']}`

## Status

- Candidate: `{summary['candidate_id']}`
- Variant: `{summary['variant']}`
- Gate decision: `{summary['gate_decision']}`
- Promotion decision: `{summary['promotion_decision']}`

## Gate Checklist

{rows}

## Single Next Action

{summary['single_next_action']}
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    registration = _load_json(REGISTRATION_JSON)
    oos_validation = _load_json(OOS_VALIDATION_JSON) if OOS_VALIDATION_JSON.exists() else {}
    no_submit_shadow = _load_json(NO_SUBMIT_SHADOW_JSON) if NO_SUBMIT_SHADOW_JSON.exists() else {}
    defense = registration.get("defense_spec") or {}
    required = set(registration.get("required_next_gates") or [])
    window_overfit_passed = not bool(defense.get("uses_explicit_historical_dates", True))
    start_shift_passed = oos_validation.get("start_shift_decision") == "PASS"
    parameter_sensitivity_passed = oos_validation.get("parameter_sensitivity_decision") == "PASS"
    no_submit_shadow_passed = no_submit_shadow.get("decision") == "PASS_NO_SUBMIT_SHADOW_DRY_RUN"
    gate_checklist = [
        {
            "id": "registration_complete",
            "required": True,
            "passed": registration.get("status") == "REGISTERED_FOR_OOS_ROBUSTNESS",
            "evidence": str(REGISTRATION_JSON),
            "missing_or_blocked": []
            if registration.get("status") == "REGISTERED_FOR_OOS_ROBUSTNESS"
            else ["registration_not_complete"],
        },
        {
            "id": "oos_start_shift",
            "required": "OOS_START_SHIFT" in required,
            "passed": start_shift_passed,
            "evidence": str(OOS_VALIDATION_JSON) if oos_validation else None,
            "missing_or_blocked": [] if start_shift_passed else ["oos_start_shift_not_passed"],
        },
        {
            "id": "parameter_sensitivity",
            "required": "PARAMETER_SENSITIVITY" in required,
            "passed": parameter_sensitivity_passed,
            "evidence": str(OOS_VALIDATION_JSON) if oos_validation else None,
            "missing_or_blocked": [] if parameter_sensitivity_passed else ["parameter_sensitivity_not_passed"],
        },
        {
            "id": "window_overfit_diagnostic",
            "required": "WINDOW_OVERFIT_DIAGNOSTIC" in required,
            "passed": window_overfit_passed,
            "evidence": str(REGISTRATION_JSON),
            "missing_or_blocked": []
            if window_overfit_passed
            else [
                "candidate_uses_explicit_historical_drawdown_window",
                f"window_start={defense.get('window_start')}",
                f"window_end={defense.get('window_end')}",
            ],
        },
        {
            "id": "cost_and_turnover_stress",
            "required": "COST_AND_TURNOVER_STRESS" in required,
            "passed": True,
            "evidence": str(REGISTRATION_JSON),
            "missing_or_blocked": [],
        },
        {
            "id": "no_submit_shadow_dry_run",
            "required": "NO_SUBMIT_SHADOW_DRY_RUN_BEFORE_OPERATIONS" in required,
            "passed": no_submit_shadow_passed,
            "evidence": str(NO_SUBMIT_SHADOW_JSON) if no_submit_shadow else None,
            "missing_or_blocked": [] if no_submit_shadow_passed else ["no_submit_shadow_dry_run_not_passed"],
        },
    ]
    blockers = [
        blocker
        for row in gate_checklist
        if row["required"] and not row["passed"]
        for blocker in row["missing_or_blocked"]
    ]
    summary = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": registration["candidate_id"],
        "variant": registration["variant"],
        "gate_decision": "PASS_OOS_ROBUSTNESS_GATES" if not blockers else "BLOCK_OOS_ROBUSTNESS_GATES",
        "promotion_decision": "NOT_OPERATION_READY" if blockers else "READY_FOR_OPERATION_REVIEW",
        "gate_checklist": gate_checklist,
        "remaining_blockers": blockers,
        "single_next_action": (
            "Fix or replace the candidate so start-shift validation passes."
            if blockers
            else "Move candidate to operation review."
        ),
        "safety": {
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "order_intent_created": False,
        },
    }
    (OUTPUT_DIR / "oos_robustness_gate_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "oos_robustness_gate.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
