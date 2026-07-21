from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
REPORT_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_preflight_latest.json"
REPORT_MD = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_preflight_latest.md"
GATEKEEPER_PACKET_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_gatekeeper_review_packet_latest.json"
RISK_GUARD_JSON = ROOT / "ops/reports/realtime_risk_guard_latest.json"
HUMAN_DECISION_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_gatekeeper_decision.json"

SAFE_PACKET_ASSERTIONS = {
    "promotion_allowed_by_this_packet": False,
    "shadow_enabled_by_this_packet": False,
    "paper_enabled_by_this_packet": False,
    "live_allowed_by_this_packet": False,
    "broker_submit_allowed_by_this_packet": False,
    "private_submit_allowed_by_this_packet": False,
    "real_orders_allowed_by_this_packet": False,
}

SAFETY = {
    "does_register_shadow_candidate": False,
    "does_start_shadow_loop": False,
    "does_enable_paper": False,
    "does_enable_live": False,
    "broker_submit_allowed": False,
    "real_orders_allowed": False,
}


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def _packet_safe(packet: dict) -> bool:
    assertions = packet.get("no_order_assertions", {})
    return all(assertions.get(key) is value for key, value in SAFE_PACKET_ASSERTIONS.items())


def _human_approval(packet: dict, decision: dict | None) -> dict:
    decision = decision or {}
    approved = (
        decision.get("candidate_id") == packet.get("candidate_id")
        and decision.get("decision") == "APPROVE_SHADOW_REVIEW_ONLY"
        and decision.get("decided_by") == "human_gatekeeper"
    )
    return {
        "approved_for_shadow_review_only": approved,
        "decision": decision.get("decision"),
        "candidate_id": decision.get("candidate_id"),
        "decided_by": decision.get("decided_by"),
        "rationale": decision.get("rationale", ""),
    }


def build_report(
    gatekeeper_packet: dict | None = None,
    risk_guard: dict | None = None,
    operating_state: dict | None = None,
    human_decision: dict | None = None,
    generated_at: str | None = None,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    caller_supplied_context = gatekeeper_packet is not None or risk_guard is not None or operating_state is not None
    gatekeeper_packet = gatekeeper_packet if gatekeeper_packet is not None else read_json(GATEKEEPER_PACKET_JSON, {})
    risk_guard = risk_guard if risk_guard is not None else read_json(RISK_GUARD_JSON, {"status": "WARN"})
    operating_state = operating_state or {"shadow_enabled": False, "paper_enabled": False, "live_enabled": False}
    human_decision = human_decision if human_decision is not None else ({} if caller_supplied_context else read_json(HUMAN_DECISION_JSON, {}))
    blockers = []
    if gatekeeper_packet.get("status") != "READY_FOR_HUMAN_GATEKEEPER_REVIEW":
        blockers.append("gatekeeper_review_packet_ready")
    if gatekeeper_packet.get("blockers"):
        blockers.append("gatekeeper_review_packet_has_no_blockers")
        blockers.extend(gatekeeper_packet.get("blockers", []))
    if not _packet_safe(gatekeeper_packet):
        blockers.append("gatekeeper_packet_no_order_safe")
    if risk_guard.get("status") != "PASS":
        blockers.append("risk_guard_pass")
    if operating_state.get("paper_enabled"):
        blockers.append("paper_disabled")
    if operating_state.get("live_enabled"):
        blockers.append("live_disabled")
    approval = _human_approval(gatekeeper_packet, human_decision)
    if not approval["approved_for_shadow_review_only"]:
        blockers.append("HUMAN_GATEKEEPER_SHADOW_DECISION_INVALID" if human_decision else "HUMAN_GATEKEEPER_SHADOW_DECISION_MISSING")
    if not blockers:
        status = "READY_FOR_SEPARATE_SHADOW_REGISTRATION_REVIEW"
    else:
        status = "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION"
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "candidate_id": gatekeeper_packet.get("candidate_id"),
        "evidence_summary": gatekeeper_packet.get("evidence_summary", {}),
        "human_decision": approval,
        "operating_state": operating_state,
        "blockers": sorted(set(blockers)),
        "single_next_action": "Record separate human shadow-review-only decision before registration." if status.startswith("BLOCKED") else "Review separate shadow registration packet; this preflight does not register or start loops.",
        "no_order_assertions": gatekeeper_packet.get("no_order_assertions"),
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    return "\n".join(
        [
            "# Bithumb Current-Actionable Shadow Preflight",
            "",
            f"- Status: `{report['status']}`",
            f"- Candidate: `{report.get('candidate_id', 'none')}`",
            f"- Blockers: `{', '.join(report['blockers']) if report['blockers'] else 'none'}`",
            f"- Single next action: {report['single_next_action']}",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "candidate_id": report["candidate_id"], "blockers": report["blockers"], "latest_json": str(REPORT_JSON), "safety": SAFETY}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
