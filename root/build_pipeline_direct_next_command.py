from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
BLOCKER_PACKET_JSON = ROOT / "reports/operations/pipeline_direct_blocker_packet_latest.json"
REPORT_JSON = ROOT / "reports/operations/pipeline_direct_next_command_latest.json"
REPORT_MD = ROOT / "reports/operations/pipeline_direct_next_command_latest.md"

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


def _find(blocker_packet: dict, axis: str) -> dict:
    for row in blocker_packet.get("direct_blockers", []) or []:
        if row.get("axis") == axis:
            return row
    return {}


def build_report(blocker_packet: dict | None = None, generated_at: str | None = None) -> dict:
    blocker_packet = blocker_packet or {}
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    bithumb = _find(blocker_packet, "BITHUMB_KRW")
    kis = _find(blocker_packet, "KIS_COMBINED_KRW")
    stage9 = _find(blocker_packet, "PIPELINE_STAGE9")
    stage10 = _find(blocker_packet, "PIPELINE_STAGE10")
    blockers = []
    next_command = ""
    operator_action = ""
    command_kind = "none"
    allowed_work = ["refresh_completion_audit_report_only"]
    if blocker_packet.get("stage13_complete"):
        status = "COMPLETE"
        operator_action = "No blocker remains."
    elif bithumb.get("status") == "BLOCKED_WAITING_FOR_HUMAN_DECISION":
        status = "WAITING_FOR_HUMAN_BITHUMB_DECISION"
        command_kind = "human_decision_record_command_after_explicit_human_choice"
        next_command = bithumb.get("command_if_human_approves_shadow_review_only", "")
        operator_action = (
            f"Human must choose APPROVE_SHADOW_REVIEW_ONLY, REJECT, or DEFER for {bithumb.get('candidate_id')}. "
            "Codex must not write this without that explicit decision."
        )
        blockers.extend(bithumb.get("current_blockers", []))
        allowed_work = ["record_explicit_human_bithumb_shadow_review_decision", "refresh_completion_audit_report_only"]
    elif kis.get("status") == "BLOCKED_WAITING_FOR_REVIEWED_AXIS_WIDE_SOURCE_EXPORT":
        status = "WAITING_FOR_KIS_REVIEWED_SOURCE_EXPORT"
        command_kind = "kis_source_export_commands_after_files_exist"
        commands = kis.get("commands_after_files_are_placed", []) or []
        next_command = "\n".join(commands)
        operator_action = "Place reviewed KRX/licensed vendor source CSVs, then run the listed KIS intake commands."
        blockers.extend(kis.get("current_blockers", []))
        allowed_work = ["ingest_reviewed_kis_axis_wide_source_export", "refresh_completion_audit_report_only"]
    elif stage9.get("status") == "BLOCKED_WAITING_FOR_EXACT_LIVE_APPROVAL_OR_NO_SUBMIT_POLICY":
        status = "WAITING_FOR_EXACT_LIVE_APPROVAL_OR_NO_SUBMIT_POLICY"
        command_kind = "operator_live_approval_phrase_required_before_order_intent"
        next_command = stage9.get("required_phrase_format", "")
        operator_action = (
            "Shadow and paper are no longer required stages. The next required gate is Stage 9, "
            "but Codex must not create an order intent or enable live without the exact LIVE APPROVE phrase."
        )
        blockers.extend(stage9.get("current_blockers", []))
        allowed_work = [
            "refresh_report_only_status",
            "wait_for_exact_live_approval_phrase",
            "after_exact_approval_only_build_order_intent_and_run_pretrade_firewall",
        ]
    elif stage10.get("status") == "BLOCKED_BY_GLOBAL_DISABLE_OR_SUBMIT_GUARD":
        status = "TINY_LIVE_PREFLIGHT_PASSED_BROKER_SUBMIT_BLOCKED_BY_GLOBAL_DISABLE"
        command_kind = "operator_review_global_disable_before_submit"
        next_command = "Review C:\\AI\\ops\\runstate\\DISABLE_ALL_TRADING before any broker submit call."
        operator_action = (
            "Stage 9 is complete: order intent exists and the pretrade firewall allowed limited live. "
            "Actual broker submit is still blocked by the global disable guard."
        )
        blockers.extend(stage10.get("current_blockers", []))
        allowed_work = [
            "audit_global_disable_guard",
            "verify_no_duplicate_live_submission",
            "prepare_broker_submit_command_but_do_not_run_while_global_disable_exists",
        ]
    else:
        status = "BLOCKED_NO_DIRECT_NEXT_COMMAND"
        operator_action = "Refresh pipeline_direct_blocker_packet before continuing."
        blockers.append("direct_blocker_packet_missing_or_unrecognized")
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "report": "pipeline_direct_next_command",
        "status": status,
        "command_kind": command_kind,
        "operator_action": operator_action,
        "next_command": next_command,
        "blockers": sorted(set(blockers)),
        "source_packet": str(BLOCKER_PACKET_JSON),
        "allowed_work": allowed_work,
        "excluded_work": blocker_packet.get("excluded_work", []),
        "safety": blocker_packet.get("safety") or dict(SAFETY),
    }


def render_md(report: dict) -> str:
    return "\n".join(
        [
            "# Pipeline Direct Next Command",
            "",
            f"- Status: `{report['status']}`",
            f"- Command kind: `{report['command_kind']}`",
            f"- Operator action: {report['operator_action']}",
            f"- Blockers: `{', '.join(report['blockers']) if report['blockers'] else 'none'}`",
            "",
            "```powershell",
            report.get("next_command", ""),
            "```",
            "",
        ]
    )


def main() -> int:
    report = build_report(read_json(BLOCKER_PACKET_JSON, {}))
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "command_kind": report["command_kind"],
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
