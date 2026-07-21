from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOARD_JSON = ROOT / "reports/model_factory/gatekeeper_pending_decision_board_latest.json"
REPORT_JSON = ROOT / "reports/model_factory/gatekeeper_review_decision_phrase_packet_latest.json"
REPORT_MD = ROOT / "reports/model_factory/gatekeeper_review_decision_phrase_packet_latest.md"

PERMISSIONS = {
    "shadow_registration_allowed_by_this_packet": False,
    "paper_enabled_by_this_packet": False,
    "live_allowed_by_this_packet": False,
    "broker_submit_allowed_by_this_packet": False,
    "private_submit_allowed_by_this_packet": False,
    "real_orders_allowed_by_this_packet": False,
}


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def _phrase_item(item: dict) -> dict:
    phrase = item.get("exact_phrase_to_record") or item.get("recommended_decision")
    row = {
        "decision_id": item.get("decision_id"),
        "decision_type": item.get("decision_type"),
        "candidate_id": item.get("candidate_id"),
        "lane": item.get("lane"),
        "status": item.get("status"),
        "ready_for_human_review": item.get("ready_for_human_review"),
        "source_path": item.get("source_path"),
        "recommended_decision": item.get("recommended_decision"),
        "exact_phrase_to_record": phrase,
        "alternate_allowed_phrases": item.get("alternate_allowed_phrases", []),
        "human_decision_path": item.get("human_decision_path"),
        "review_only_effect": item.get("review_only_effect") or "Records review only; it does not register, enable paper/live, broker submit, private submit, or real orders.",
        "evidence_summary": item.get("evidence_summary", {}),
        "blockers": item.get("blockers", []),
    }
    if item.get("decision_type") == "shadow_registration_review":
        row["exact_phrase_to_record"] = "APPROVE_SHADOW_REVIEW_ONLY"
        row["alternate_allowed_phrases"] = ["REJECT", "DEFER"]
        row["review_only_effect"] = "Records human approval for shadow-review consideration only. It does not register a shadow candidate, start a loop, enable paper/live, or allow orders."
        row["human_decision_state"] = {
            "human_decision_present": item.get("human_decision_present"),
            "human_decision_valid": item.get("human_decision_valid"),
            "recorded_candidate_id": item.get("recorded_candidate_id"),
            "expected_candidate_id": item.get("candidate_id"),
            "decision_candidate_match": item.get("decision_candidate_match"),
        }
        row["human_decision_draft_status"] = item.get("human_decision_draft_status")
        row["human_decision_draft_candidate_id"] = item.get("human_decision_draft_candidate_id")
        row["human_decision_draft_path"] = item.get("human_decision_draft_path")
    return row


def build_packet(board: dict | None = None) -> dict:
    board = board if board is not None else read_json(BOARD_JSON, {})
    items = board.get("items", []) or []
    ready = [_phrase_item(item) for item in items if item.get("ready_for_human_review")]
    blocked = [item for item in items if not item.get("ready_for_human_review")]
    next_decision_id = (board.get("next_decision") or {}).get("decision_id")
    next_phrase = next((item for item in ready if item.get("decision_id") == next_decision_id), ready[0] if ready else None)
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "report": "gatekeeper_review_decision_phrase_packet",
        "scope": "human_phrase_packet_review_only_no_state_mutation_no_order_paths",
        "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW" if ready else "BLOCKED",
        "source_board": str(BOARD_JSON),
        "board_status": board.get("status"),
        "ready_phrase_count": len(ready),
        "blocked_decision_count": len(blocked),
        "next_phrase": next_phrase,
        "ready_phrases": ready,
        "blocked_decisions": blocked,
        "board_permissions": dict(PERMISSIONS),
        "safety": dict(PERMISSIONS),
    }


def render_md(packet: dict) -> str:
    next_phrase = packet.get("next_phrase") or {}
    return "\n".join(
        [
            "# Gatekeeper Review Decision Phrase Packet",
            "",
            f"- Status: `{packet['status']}`",
            f"- Ready phrases: `{packet['ready_phrase_count']}`",
            f"- Next decision: `{next_phrase.get('decision_id', 'none')}`",
            f"- Exact phrase: `{next_phrase.get('exact_phrase_to_record', 'none')}`",
            "",
        ]
    )


def main() -> int:
    packet = build_packet()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(packet), encoding="utf-8")
    print(json.dumps({"status": packet["status"], "ready_phrase_count": packet["ready_phrase_count"], "blocked_decision_count": packet["blocked_decision_count"], "latest_json": str(REPORT_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
