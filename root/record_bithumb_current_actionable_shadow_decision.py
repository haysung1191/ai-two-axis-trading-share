from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PHRASE_PACKET_JSON = ROOT / "reports/model_factory/gatekeeper_review_decision_phrase_packet_latest.json"
DECISION_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_gatekeeper_decision.json"
REPORT_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_decision_record_latest.json"
REPORT_MD = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_decision_record_latest.md"

ALLOWED_DECISIONS = {"APPROVE_SHADOW_REVIEW_ONLY", "REJECT", "DEFER"}
SAFETY = {
    "does_register_shadow_candidate": False,
    "does_start_shadow_loop": False,
    "does_enable_paper": False,
    "does_enable_live": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders": 0,
}


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def _target_phrase(phrase_packet: dict) -> dict:
    next_phrase = phrase_packet.get("next_phrase", {}) or {}
    if next_phrase.get("decision_id") == "bithumb_current_actionable_shadow_review":
        return next_phrase
    for row in phrase_packet.get("ready_phrases", []) or []:
        if row.get("decision_id") == "bithumb_current_actionable_shadow_review":
            return row
    return {}


def build_record(
    phrase_packet: dict,
    *,
    candidate_id: str,
    decision: str,
    rationale: str,
    write: bool = False,
    generated_at_utc: str | None = None,
) -> dict:
    generated_at_utc = generated_at_utc or datetime.now(timezone.utc).isoformat()
    target = _target_phrase(phrase_packet)
    expected_candidate_id = target.get("candidate_id")
    blockers = []
    if not target:
        blockers.append("BITHUMB_SHADOW_REVIEW_PHRASE_NOT_READY")
    if candidate_id != expected_candidate_id:
        blockers.append("CANDIDATE_ID_MISMATCH")
    if decision not in ALLOWED_DECISIONS:
        blockers.append("DECISION_NOT_ALLOWED")
    if not rationale.strip():
        blockers.append("RATIONALE_REQUIRED")
    decision_payload = {
        "candidate_id": candidate_id,
        "decision": decision,
        "decided_by": "human_gatekeeper",
        "rationale": rationale,
        "recorded_at_utc": generated_at_utc,
        "source_phrase_packet": str(PHRASE_PACKET_JSON),
        "review_only_effect": "This records shadow-review consideration only. It does not register a shadow candidate, start loops, enable paper/live, broker submit, private submit, or real orders.",
    }
    status = "READY_TO_WRITE_DECISION" if not blockers and not write else "BLOCKED"
    file_mutated = False
    if not blockers and write:
        DECISION_JSON.parent.mkdir(parents=True, exist_ok=True)
        DECISION_JSON.write_text(json.dumps(decision_payload, indent=2), encoding="utf-8")
        status = "DECISION_RECORDED"
        file_mutated = True
    return {
        "generated_at_utc": generated_at_utc,
        "report": "bithumb_current_actionable_shadow_decision_record",
        "status": status,
        "candidate_id": candidate_id,
        "expected_candidate_id": expected_candidate_id,
        "decision": decision,
        "decision_path": str(DECISION_JSON),
        "file_mutated": file_mutated,
        "blockers": sorted(set(blockers)),
        "decision_payload": decision_payload if not blockers else None,
        "safety": dict(SAFETY),
    }


def render_md(report: dict) -> str:
    return "\n".join(
        [
            "# Bithumb Current-Actionable Shadow Decision Record",
            "",
            f"- Status: `{report['status']}`",
            f"- Candidate: `{report.get('candidate_id', 'none')}`",
            f"- Decision: `{report.get('decision', 'none')}`",
            f"- File mutated: `{report['file_mutated']}`",
            f"- Blockers: `{', '.join(report['blockers']) if report['blockers'] else 'none'}`",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--decision", required=True, choices=sorted(ALLOWED_DECISIONS))
    parser.add_argument("--rationale", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = build_record(
        read_json(PHRASE_PACKET_JSON, {}),
        candidate_id=args.candidate_id,
        decision=args.decision,
        rationale=args.rationale,
        write=args.write,
    )
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "candidate_id": report["candidate_id"], "file_mutated": report["file_mutated"], "blockers": report["blockers"], "latest_json": str(REPORT_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
