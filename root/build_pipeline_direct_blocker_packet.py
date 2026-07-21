from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
STAGE13_JSON = ROOT / "reports/operations/stage13_completion_audit_latest.json"
BITHUMB_DECISION_RECORD_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_decision_record_latest.json"
BITHUMB_PHRASE_PACKET_JSON = ROOT / "reports/model_factory/gatekeeper_review_decision_phrase_packet_latest.json"
KIS_OPERATOR_PACKET_JSON = ROOT / "reports/operations/kis_axis_wide_source_export_operator_packet_latest.json"
REPORT_JSON = ROOT / "reports/operations/pipeline_direct_blocker_packet_latest.json"
REPORT_MD = ROOT / "reports/operations/pipeline_direct_blocker_packet_latest.md"

SAFETY = {
    "paper_enabled": False,
    "live_enabled": False,
    "broker_submit_allowed": False,
    "private_submit_used": False,
    "real_orders": 0,
    "order_intent_created": False,
    "pretrade_firewall_default_decision": "BLOCK",
}


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def _bithumb_row(stage13: dict) -> dict:
    for row in stage13.get("prompt_to_artifact_checklist", []) or []:
        if row.get("stage_id") == "axis_bithumb_krw":
            return row
    return {}


def _bithumb_blocker(stage13: dict, decision_record: dict, phrase_packet: dict) -> dict:
    row = _bithumb_row(stage13)
    observed = row.get("observed", {}) or {}
    next_phrase = phrase_packet.get("next_phrase", {}) or {}
    candidate_id = (
        decision_record.get("candidate_id")
        or observed.get("shadow_preflight_candidate_id")
        or next_phrase.get("candidate_id")
    )
    return {
        "axis": "BITHUMB_KRW",
        "status": "BLOCKED_WAITING_FOR_HUMAN_DECISION",
        "candidate_id": candidate_id,
        "market": (observed.get("top_triggered_candidate") or {}).get("market"),
        "required_decisions": ["APPROVE_SHADOW_REVIEW_ONLY", "REJECT", "DEFER"],
        "current_blockers": row.get("missing_or_blocked", []),
        "dry_run_status": decision_record.get("status"),
        "dry_run_file_mutated": decision_record.get("file_mutated"),
        "next_phrase": next_phrase.get("exact_phrase_to_record"),
        "command_if_human_approves_shadow_review_only": (
            "python .\\record_bithumb_current_actionable_shadow_decision.py "
            f"--candidate-id {candidate_id} "
            "--decision APPROVE_SHADOW_REVIEW_ONLY "
            "--rationale \"HUMAN_REVIEWED_SWEEP2154_SHADOW_REVIEW_ONLY_NO_PAPER_LIVE_BROKER_ORDERS\" "
            "--write"
        ),
        "commands_after_recording_valid_decision": [
            "python .\\build_bithumb_current_actionable_shadow_decision_template.py",
            "python .\\build_bithumb_current_actionable_shadow_preflight.py",
            "python .\\build_bithumb_current_actionable_shadow_registration_action_packet.py",
            "python .\\register_bithumb_current_actionable_shadow_candidate.py",
            "python .\\build_gatekeeper_pending_decision_board.py",
            "python .\\build_stage13_completion_audit.py",
        ],
        "non_goals": [
            "does_not_enable_paper",
            "does_not_enable_live",
            "does_not_allow_broker_submit",
            "does_not_create_order_intent",
            "does_not_submit_orders",
        ],
    }


def _kis_blocker(stage13: dict, kis_packet: dict) -> dict:
    return {
        "axis": "KIS_COMBINED_KRW",
        "status": "BLOCKED_WAITING_FOR_REVIEWED_AXIS_WIDE_SOURCE_EXPORT",
        "current_blockers": stage13.get("external_input_blockers", []),
        "blocked_worklist_row_count": kis_packet.get("blocked_worklist_row_count"),
        "valid_export_count": kis_packet.get("valid_export_count"),
        "raw_drop_dir": kis_packet.get("raw_drop_dir"),
        "normalized_export_dir": kis_packet.get("normalized_export_dir"),
        "manifest": (kis_packet.get("paths", {}) or {}).get("manifest"),
        "required_normalized_columns": kis_packet.get("required_normalized_columns", []),
        "accepted_evidence_quality": kis_packet.get("accepted_evidence_quality", []),
        "commands_after_files_are_placed": kis_packet.get("commands_after_files_are_placed", []),
        "guarded_apply_commands_after_review": kis_packet.get("guarded_apply_commands_after_review", []),
        "non_goals": [
            "does_not_bypass_krx_login_or_license_terms",
            "does_not_apply_worklist_without_exact_confirmation",
            "does_not_enable_trading",
        ],
    }


def _stage9_blocker(stage13: dict) -> dict:
    return {
        "axis": "PIPELINE_STAGE9",
        "status": "BLOCKED_WAITING_FOR_EXACT_LIVE_APPROVAL_OR_NO_SUBMIT_POLICY",
        "current_blockers": stage13.get("current_target_stage_missing_or_blocked", []),
        "required_phrase_format": "LIVE APPROVE <max_krw> <max_daily_loss_krw> <max_total_loss_krw>",
        "current_target_stage_id": stage13.get("current_target_stage_id"),
        "current_target_stage_name": stage13.get("current_target_stage_name"),
        "non_goals": [
            "does_not_enable_paper",
            "does_not_enable_live_without_exact_approval",
            "does_not_allow_broker_submit",
            "does_not_create_order_intent_without_live_approval",
            "does_not_submit_orders",
        ],
    }


def _stage10_blocker(stage13: dict) -> dict:
    return {
        "axis": "PIPELINE_STAGE10",
        "status": "BLOCKED_BY_GLOBAL_DISABLE_OR_SUBMIT_GUARD",
        "current_blockers": stage13.get("current_target_stage_missing_or_blocked", []),
        "current_target_stage_id": stage13.get("current_target_stage_id"),
        "current_target_stage_name": stage13.get("current_target_stage_name"),
        "non_goals": [
            "does_not_delete_global_disable_implicitly",
            "does_not_use_private_submit_without_auditable_submit_call",
            "does_not_submit_duplicate_orders",
        ],
    }


def build_packet(
    stage13: dict | None = None,
    decision_record: dict | None = None,
    phrase_packet: dict | None = None,
    kis_operator_packet: dict | None = None,
    generated_at: str | None = None,
) -> dict:
    stage13 = stage13 or {}
    decision_record = decision_record or {}
    phrase_packet = phrase_packet or {}
    kis_operator_packet = kis_operator_packet or {}
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    direct_blockers = []
    bithumb_blocker = _bithumb_blocker(stage13, decision_record, phrase_packet)
    if bithumb_blocker.get("current_blockers"):
        direct_blockers.append(bithumb_blocker)
    kis_blocker = _kis_blocker(stage13, kis_operator_packet)
    if kis_blocker.get("current_blockers"):
        direct_blockers.append(kis_blocker)
    if (
        not direct_blockers
        and stage13.get("current_target_stage_id") == 9
        and not stage13.get("stage13_complete")
    ):
        direct_blockers.append(_stage9_blocker(stage13))
    if (
        not direct_blockers
        and stage13.get("current_target_stage_id") == 10
        and not stage13.get("stage13_complete")
    ):
        direct_blockers.append(_stage10_blocker(stage13))
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "report": "pipeline_direct_blocker_packet",
        "objective": "Complete only the direct blockers for the two-axis capital-growth pipeline and tiny-live preconditions.",
        "completion_decision": stage13.get("completion_decision"),
        "stage13_complete": bool(stage13.get("stage13_complete", False)),
        "status": "BLOCKED_ON_EXTERNAL_OR_HUMAN_INPUT" if not stage13.get("stage13_complete") else "COMPLETE",
        "direct_blocker_count": len(direct_blockers),
        "direct_blockers": direct_blockers,
        "safety": stage13.get("safety") or dict(SAFETY),
        "excluded_work": [
            "generic model research not tied to these blockers",
            "paper/live/broker/order enablement",
            "threshold weakening or forced trades",
            "unlicensed or unreviewed KIS data ingestion",
        ],
    }


def render_md(packet: dict) -> str:
    lines = [
        "# Pipeline Direct Blocker Packet",
        "",
        f"- Status: `{packet['status']}`",
        f"- Completion: `{packet.get('completion_decision')}`",
        f"- Stage13 complete: `{packet['stage13_complete']}`",
        f"- Direct blockers: `{packet['direct_blocker_count']}`",
        "",
    ]
    for row in packet["direct_blockers"]:
        lines.extend(
            [
                f"## {row['axis']}",
                f"- Status: `{row['status']}`",
                f"- Candidate: `{row.get('candidate_id', 'n/a')}`",
                f"- Current blockers: `{', '.join(row.get('current_blockers', [])) if row.get('current_blockers') else 'none'}`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    packet = build_packet(
        read_json(STAGE13_JSON, {}),
        read_json(BITHUMB_DECISION_RECORD_JSON, {}),
        read_json(BITHUMB_PHRASE_PACKET_JSON, {}),
        read_json(KIS_OPERATOR_PACKET_JSON, {}),
    )
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(packet), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": packet["status"],
                "completion_decision": packet["completion_decision"],
                "direct_blocker_count": packet["direct_blocker_count"],
                "latest_json": str(REPORT_JSON),
                "safety": packet["safety"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
