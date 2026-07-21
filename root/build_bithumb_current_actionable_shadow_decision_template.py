from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
PREFLIGHT_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_preflight_latest.json"
HUMAN_DECISION_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_gatekeeper_decision.json"
REPORT_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_decision_template_latest.json"
REPORT_MD = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_decision_template_latest.md"

ALLOWED_DECISIONS = {"APPROVE_SHADOW_REVIEW_ONLY", "REJECT", "DEFER"}
SAFETY = {
    "does_register_shadow_candidate": False,
    "does_start_shadow_loop": False,
    "does_enable_paper": False,
    "does_enable_live": False,
    "broker_submit_allowed": False,
    "private_submit_allowed": False,
    "real_orders_allowed": False,
}


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def _decision_state(preflight: dict, decision: dict, decision_present: bool) -> dict:
    normalized = {
        "candidate_id": decision.get("candidate_id"),
        "decision": decision.get("decision"),
        "decided_by": decision.get("decided_by"),
        "rationale": decision.get("rationale", ""),
    }
    blockers = []
    if not decision_present:
        blockers.append("HUMAN_GATEKEEPER_SHADOW_DECISION_MISSING")
    if decision_present and normalized["candidate_id"] != preflight.get("candidate_id"):
        blockers.append("HUMAN_GATEKEEPER_DECISION_CANDIDATE_MISMATCH")
    if decision_present and normalized["decision"] not in ALLOWED_DECISIONS:
        blockers.append("HUMAN_GATEKEEPER_DECISION_NOT_ALLOWED")
    if decision_present and normalized["decided_by"] != "human_gatekeeper":
        blockers.append("HUMAN_GATEKEEPER_DECIDED_BY_INVALID")
    valid = decision_present and not blockers and normalized["decision"] == "APPROVE_SHADOW_REVIEW_ONLY"
    return {
        "path": str(HUMAN_DECISION_JSON),
        "present": decision_present,
        "valid": valid,
        "decision_recorded": valid,
        "normalized": normalized,
        "blockers": blockers,
    }


def build_report(
    preflight: dict | None = None,
    human_decision: dict | None = None,
    human_decision_present: bool | None = None,
    generated_at: str | None = None,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    preflight = preflight if preflight is not None else read_json(PREFLIGHT_JSON, {})
    if human_decision is None:
        human_decision = read_json(HUMAN_DECISION_JSON, {})
    if human_decision_present is None:
        human_decision_present = HUMAN_DECISION_JSON.exists()
    decision_state = _decision_state(preflight, human_decision, bool(human_decision_present))
    preflight_ready = preflight.get("status") == "READY_FOR_SEPARATE_SHADOW_REGISTRATION_REVIEW"
    blockers = list(decision_state["blockers"])
    approved = bool(decision_state["valid"] and preflight_ready)
    if decision_state["valid"] and not preflight_ready:
        blockers.append("SHADOW_PREFLIGHT_NOT_READY_FOR_REGISTRATION_REVIEW")
        status = "HUMAN_GATEKEEPER_DECISION_RECORDED_BUT_PREFLIGHT_BLOCKED"
    elif approved:
        status = "HUMAN_GATEKEEPER_SHADOW_DECISION_RECORDED"
    elif human_decision_present and blockers:
        status = "INVALID_HUMAN_GATEKEEPER_DECISION"
    else:
        status = "PENDING_HUMAN_GATEKEEPER_DECISION"
    if not human_decision_present and "HUMAN_GATEKEEPER_SHADOW_DECISION_MISSING" not in blockers:
        blockers.append("HUMAN_GATEKEEPER_SHADOW_DECISION_MISSING")
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "candidate_id": preflight.get("candidate_id"),
        "evidence_summary": preflight.get("evidence_summary", {}),
        "human_decision": decision_state,
        "approved_for_separate_shadow_registration_review": approved,
        "blockers": sorted(set(blockers)),
        "blocker_count": len(set(blockers)),
        "exact_phrase_to_record": "APPROVE_SHADOW_REVIEW_ONLY",
        "alternate_allowed_phrases": ["REJECT", "DEFER"],
        "safety": dict(SAFETY),
    }


def render_md(report: dict) -> str:
    return "\n".join(
        [
            "# Bithumb Current-Actionable Shadow Decision Template",
            "",
            f"- Status: `{report['status']}`",
            f"- Candidate: `{report.get('candidate_id', 'none')}`",
            f"- Blockers: `{', '.join(report['blockers']) if report['blockers'] else 'none'}`",
            f"- Exact phrase: `{report['exact_phrase_to_record']}`",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "candidate_id": report.get("candidate_id"), "blockers": report["blockers"], "latest_json": str(REPORT_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
