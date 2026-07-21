from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ACTION_PACKET_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_registration_action_packet_latest.json"
REPORT_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_registration_latest.json"
REPORT_MD = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_registration_latest.md"
REGISTRY_JSON = ROOT / "registry/model_factory_shadow_candidates/bithumb_current_actionable_shadow_candidates.json"

SAFETY = {
    "does_start_shadow_loop": False,
    "does_emit_order_signal": False,
    "does_enable_paper": False,
    "does_enable_live": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders_allowed_by_this_report": False,
    "real_orders": 0,
}


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def _hash_payload(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _packet_safety_clean(packet: dict) -> bool:
    safety = packet.get("safety", {}) or {}
    expected_false = [
        "does_register_shadow_candidate",
        "does_start_shadow_loop",
        "does_enable_paper",
        "does_enable_live",
        "broker_submit_allowed_by_this_packet",
        "private_submit_allowed_by_this_packet",
        "real_orders_allowed_by_this_packet",
    ]
    return all(safety.get(key) is False for key in expected_false) and int(safety.get("real_orders", 0) or 0) == 0


def build_registration(
    action_packet: dict,
    previous_registry: dict | None = None,
    generated_at_utc: str | None = None,
) -> dict:
    generated_at_utc = generated_at_utc or datetime.now(timezone.utc).isoformat()
    previous_registry = previous_registry or {"records": []}
    candidate_id = action_packet.get("candidate_id")
    planned = action_packet.get("planned_shadow_registration", {}) or {}
    human = action_packet.get("human_decision_summary", {}) or {}
    blockers: list[str] = []
    if action_packet.get("status") != "READY_FOR_SHADOW_REGISTRATION_ACTION_REVIEW":
        blockers.append("ACTION_PACKET_NOT_READY")
    if action_packet.get("blockers"):
        blockers.append("ACTION_PACKET_HAS_BLOCKERS")
        blockers.extend(action_packet.get("blockers", []))
    if not _packet_safety_clean(action_packet):
        blockers.append("ACTION_PACKET_SAFETY_NOT_CLEAN")
    if not human.get("decision_recorded") or human.get("decision") != "APPROVE_SHADOW_REVIEW_ONLY":
        blockers.append("VALID_SHADOW_REVIEW_ONLY_DECISION_MISSING")
    if human.get("expected_candidate_id") != human.get("recorded_candidate_id") or human.get("recorded_candidate_id") != candidate_id:
        blockers.append("HUMAN_DECISION_CANDIDATE_MISMATCH")
    record = {
        "schema_version": "1.0",
        "registered_at_utc": generated_at_utc,
        "candidate_id": candidate_id,
        "lane": action_packet.get("lane", "bithumb_1d"),
        "market": planned.get("market"),
        "timeframe": planned.get("timeframe"),
        "mode": "shadow_review_only",
        "status": "REGISTERED" if not blockers else "NOT_REGISTERED",
        "shadow_gate": planned.get("shadow_gate", "G07_SHADOW_REVIEW_ONLY"),
        "recommended_exposure_cap": planned.get("recommended_exposure_cap"),
        "estimated_cagr": planned.get("estimated_cagr"),
        "estimated_mdd": planned.get("estimated_mdd"),
        "oos_status": planned.get("oos_status"),
        "oos_pass_fold_count": planned.get("oos_pass_fold_count"),
        "oos_total_trade_count": planned.get("oos_total_trade_count"),
        "robustness_status": planned.get("robustness_status"),
        "robustness_pass_count": planned.get("robustness_pass_count"),
        "robustness_cost_pass_count": planned.get("robustness_cost_pass_count"),
        "source_action_packet": str(ACTION_PACKET_JSON),
        "action_packet_hash": _hash_payload(action_packet),
        "human_decision": {
            "decision": human.get("decision"),
            "decided_by": human.get("decided_by"),
            "rationale": human.get("rationale", ""),
        },
        "runtime_limits": {
            "does_start_shadow_loop": False,
            "does_emit_order_signal": False,
            "does_enable_paper": False,
            "does_enable_live": False,
            "broker_submit_allowed": False,
            "private_submit_allowed": False,
            "real_orders_allowed": False,
            "real_orders": 0,
        },
    }
    already_registered = any(row.get("candidate_id") == candidate_id for row in previous_registry.get("records", []))
    return {
        "generated_at_utc": generated_at_utc,
        "report": "bithumb_current_actionable_shadow_registration",
        "status": "REGISTERED" if not blockers else "BLOCKED",
        "already_registered": already_registered,
        "candidate_id": candidate_id,
        "registry_path": str(REGISTRY_JSON),
        "blockers": sorted(set(blockers)),
        "record": record,
        "safety": dict(SAFETY),
        "next_action": "Registry record is file-only shadow-review metadata; a separate reviewed process is required before any loop starts."
        if not blockers
        else "Resolve blockers before writing a shadow-review registration record.",
    }


def update_registry(registration_report: dict, previous_registry: dict | None = None) -> dict:
    previous_registry = previous_registry or {"records": []}
    records = [
        row
        for row in previous_registry.get("records", [])
        if row.get("candidate_id") != registration_report.get("candidate_id")
    ]
    if registration_report.get("status") == "REGISTERED":
        records.append(registration_report["record"])
    return {
        "schema_version": "1.0",
        "updated_at_utc": registration_report.get("generated_at_utc"),
        "registered_count": len(records),
        "records": sorted(records, key=lambda row: row.get("candidate_id", "")),
    }


def render_md(report: dict) -> str:
    return "\n".join(
        [
            "# Bithumb Current-Actionable Shadow Registration",
            "",
            f"- Status: `{report['status']}`",
            f"- Candidate: `{report.get('candidate_id', 'none')}`",
            f"- Already registered: `{report['already_registered']}`",
            f"- Blockers: `{', '.join(report['blockers']) if report['blockers'] else 'none'}`",
            f"- Next action: {report['next_action']}",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Write registry only when the packet is fully ready.")
    args = parser.parse_args()
    previous = read_json(REGISTRY_JSON, {"records": []})
    report = build_registration(read_json(ACTION_PACKET_JSON, {}), previous)
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    registry_written = False
    if args.write and report.get("status") == "REGISTERED":
        REGISTRY_JSON.parent.mkdir(parents=True, exist_ok=True)
        REGISTRY_JSON.write_text(json.dumps(update_registry(report, previous), indent=2), encoding="utf-8")
        registry_written = True
    print(
        json.dumps(
            {
                "status": report["status"],
                "candidate_id": report.get("candidate_id"),
                "blockers": report["blockers"],
                "registry_written": registry_written,
                "latest_json": str(REPORT_JSON),
                "safety": report["safety"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
