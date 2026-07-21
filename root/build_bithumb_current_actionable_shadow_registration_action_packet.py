from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREFLIGHT_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_preflight_latest.json"
DECISION_TEMPLATE_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_decision_template_latest.json"
RISK_GUARD_JSON = ROOT / "ops/reports/realtime_risk_guard_latest.json"
KILL_SWITCH_JSON = ROOT / "ops/runstate/kill_switch.json"
REPORT_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_registration_action_packet_latest.json"
REPORT_MD = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_registration_action_packet_latest.md"

SAFETY = {
    "does_register_shadow_candidate": False,
    "does_start_shadow_loop": False,
    "does_enable_paper": False,
    "does_enable_live": False,
    "broker_submit_allowed_by_this_packet": False,
    "private_submit_allowed_by_this_packet": False,
    "real_orders_allowed_by_this_packet": False,
    "real_orders": 0,
}


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def _risk_guard_hard_safety_ok(risk_guard: dict) -> bool:
    if risk_guard.get("status") == "PASS":
        return True
    hard_names = {"live_disabled", "private_submit_unused", "real_orders_zero", "broker_submit_scope"}
    checks = risk_guard.get("checks", []) or []
    if not checks:
        return False
    return all(row.get("status") == "PASS" for row in checks if row.get("name") in hard_names)


def _planned_registration(preflight: dict) -> dict:
    evidence = preflight.get("evidence_summary", {}) or {}
    return {
        "candidate_id": preflight.get("candidate_id"),
        "market": evidence.get("market"),
        "timeframe": evidence.get("timeframe"),
        "shadow_gate": "G07_SHADOW_REVIEW_ONLY",
        "recommended_exposure_cap": evidence.get("recommended_exposure_cap"),
        "estimated_cagr": evidence.get("estimated_cagr"),
        "estimated_mdd": evidence.get("estimated_mdd"),
        "oos_status": evidence.get("oos_status"),
        "oos_pass_fold_count": evidence.get("oos_pass_fold_count"),
        "oos_total_trade_count": evidence.get("oos_total_trade_count"),
        "robustness_status": evidence.get("robustness_status"),
        "robustness_pass_count": evidence.get("robustness_pass_count"),
        "robustness_cost_pass_count": evidence.get("robustness_cost_pass_count"),
    }


def _decision_summary(decision_template: dict, expected_candidate_id: str | None) -> dict:
    human = decision_template.get("human_decision", {}) or {}
    normalized = human.get("normalized", {}) or {}
    return {
        "decision_recorded": bool(human.get("decision_recorded")),
        "decision": normalized.get("decision"),
        "expected_candidate_id": expected_candidate_id,
        "recorded_candidate_id": normalized.get("candidate_id"),
        "decided_by": normalized.get("decided_by"),
        "rationale": normalized.get("rationale", ""),
    }


def build_packet(
    shadow_preflight: dict | None = None,
    decision_template: dict | None = None,
    risk_guard: dict | None = None,
    operating_state: dict | None = None,
    generated_at_utc: str | None = None,
) -> dict:
    generated_at_utc = generated_at_utc or datetime.now(timezone.utc).isoformat()
    shadow_preflight = shadow_preflight or {}
    decision_template = decision_template or {}
    risk_guard = risk_guard or {"status": "WARN", "checks": []}
    operating_state = operating_state or {"paper_enabled": False, "live_enabled": False}
    candidate_id = shadow_preflight.get("candidate_id") or decision_template.get("candidate_id")
    blockers = []
    if shadow_preflight.get("status") != "READY_FOR_SEPARATE_SHADOW_REGISTRATION_REVIEW":
        blockers.append("SHADOW_PREFLIGHT_NOT_READY_FOR_REGISTRATION_REVIEW")
    if not decision_template.get("approved_for_separate_shadow_registration_review", False):
        blockers.append("HUMAN_SHADOW_REVIEW_ONLY_APPROVAL_NOT_RECORDED")
    human = decision_template.get("human_decision", {}) or {}
    if not human.get("decision_recorded", False):
        blockers.append("VALID_HUMAN_SHADOW_REVIEW_ONLY_DECISION_MISSING")
    blockers.extend(decision_template.get("blockers", []) or [])
    if operating_state.get("paper_enabled"):
        blockers.append("PAPER_MUST_REMAIN_DISABLED")
    if operating_state.get("live_enabled"):
        blockers.append("LIVE_MUST_REMAIN_DISABLED")
    risk_ok = _risk_guard_hard_safety_ok(risk_guard)
    if not risk_ok:
        blockers.append("RISK_GUARD_NOT_PASS")
    status = "READY_FOR_SHADOW_REGISTRATION_ACTION_REVIEW" if not blockers else "BLOCKED"
    safety = dict(SAFETY)
    safety["risk_guard_status"] = risk_guard.get("status")
    safety["risk_guard_hard_safety_ok"] = risk_ok
    return {
        "generated_at_utc": generated_at_utc,
        "report": "bithumb_current_actionable_shadow_registration_action_packet",
        "status": status,
        "scope": "action_packet_only_no_registration_no_order_paths",
        "candidate_id": candidate_id,
        "lane": "bithumb_1d",
        "sources": {
            "shadow_preflight": str(PREFLIGHT_JSON),
            "decision_template": str(DECISION_TEMPLATE_JSON),
            "risk_guard": str(RISK_GUARD_JSON),
            "kill_switch": str(KILL_SWITCH_JSON),
        },
        "planned_shadow_registration": _planned_registration(shadow_preflight),
        "human_decision_summary": _decision_summary(decision_template, candidate_id),
        "blockers": sorted(set(blockers)),
        "safety": safety,
        "next_action": "Review separate shadow registration action packet; this packet itself does not register, start loops, enable trading, or submit orders."
        if status == "READY_FOR_SHADOW_REGISTRATION_ACTION_REVIEW"
        else "Resolve blockers before preparing any separate shadow-registration implementation step.",
    }


def build_report() -> dict:
    return build_packet(
        read_json(PREFLIGHT_JSON, {}),
        read_json(DECISION_TEMPLATE_JSON, {}),
        read_json(RISK_GUARD_JSON, {"status": "WARN"}),
        {"paper_enabled": False, "live_enabled": False},
    )


def render_md(report: dict) -> str:
    return "\n".join(
        [
            "# Bithumb Current-Actionable Shadow Registration Action Packet",
            "",
            f"- Status: `{report['status']}`",
            f"- Candidate: `{report.get('candidate_id', 'none')}`",
            f"- Blockers: `{', '.join(report['blockers']) if report['blockers'] else 'none'}`",
            f"- Next action: {report['next_action']}",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "candidate_id": report.get("candidate_id"),
                "blockers": report["blockers"],
                "latest_json": str(REPORT_JSON),
                "safety": report["safety"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
