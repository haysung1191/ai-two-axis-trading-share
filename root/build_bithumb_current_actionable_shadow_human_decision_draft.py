from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
ROLLOVER_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_rollover_review_packet_latest.json"
GATEKEEPER_PACKET_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_gatekeeper_review_packet_latest.json"
EXISTING_DECISION_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_gatekeeper_decision.json"
REPORT_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_human_decision_draft_latest.json"
DRAFT_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_gatekeeper_decision_draft.json"
REPORT_MD = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_human_decision_draft_latest.md"

SAFETY = {
    "does_write_human_decision_file": False,
    "does_register_shadow_candidate": False,
    "does_emit_order_signal": False,
    "does_enable_paper": False,
    "does_enable_live": False,
    "broker_submit_allowed_by_this_report": False,
    "real_orders": 0,
}


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def _candidate_id(rollover: dict, gatekeeper_packet: dict) -> str | None:
    return (
        gatekeeper_packet.get("candidate_id")
        or (rollover.get("latest_oos_candidate") or {}).get("candidate_id")
        or (rollover.get("registered_candidate") or {}).get("candidate_id")
    )


def build_draft(
    rollover: dict | None = None,
    gatekeeper_packet: dict | None = None,
    existing_human_decision: dict | None = None,
    generated_at: str | None = None,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    rollover = rollover or {}
    gatekeeper_packet = gatekeeper_packet or {}
    existing_human_decision = existing_human_decision or {}
    candidate_id = _candidate_id(rollover, gatekeeper_packet)
    blockers = list(rollover.get("blockers", []) or [])
    if not candidate_id:
        blockers.append("LATEST_OOS_CANDIDATE_MISSING")
    if existing_human_decision and existing_human_decision.get("candidate_id") != candidate_id:
        blockers.append("EXISTING_DECISION_POINTS_TO_DIFFERENT_CANDIDATE")
    status = "DRAFT_READY" if candidate_id else "BLOCKED"
    draft_decision = {
        "candidate_id": candidate_id,
        "decision": "HUMAN_MUST_CHOOSE_APPROVE_REJECT_OR_DEFER",
        "allowed_decisions": ["APPROVE_SHADOW_REVIEW_ONLY", "REJECT", "DEFER"],
        "decided_by": "human_gatekeeper",
        "rationale": "Fill in after reviewing the current Bithumb shadow preflight packet.",
    }
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "candidate_id": candidate_id,
        "draft_path": str(DRAFT_JSON),
        "draft_decision": draft_decision,
        "existing_human_decision_present": bool(existing_human_decision),
        "existing_human_decision_candidate_id": existing_human_decision.get("candidate_id"),
        "blockers": sorted(set(blockers)),
        "safety": dict(SAFETY),
    }


def render_md(report: dict) -> str:
    return "\n".join(
        [
            "# Bithumb Current-Actionable Shadow Human Decision Draft",
            "",
            f"- Status: `{report['status']}`",
            f"- Candidate: `{report.get('candidate_id', 'none')}`",
            f"- Draft path: `{report.get('draft_path')}`",
            f"- Blockers: `{', '.join(report['blockers']) if report['blockers'] else 'none'}`",
            "",
        ]
    )


def main() -> int:
    report = build_draft(
        read_json(ROLLOVER_JSON, {}),
        read_json(GATEKEEPER_PACKET_JSON, {}),
        read_json(EXISTING_DECISION_JSON, {}),
    )
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    DRAFT_JSON.write_text(json.dumps(report["draft_decision"], indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "candidate_id": report.get("candidate_id"), "blockers": report["blockers"], "draft_path": report["draft_path"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
