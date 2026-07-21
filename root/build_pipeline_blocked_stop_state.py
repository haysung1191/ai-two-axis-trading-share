from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
RECHECK_JSON = ROOT / "reports/operations/pipeline_direct_recheck_latest.json"
NEXT_COMMAND_JSON = ROOT / "reports/operations/pipeline_direct_next_command_latest.json"
BLOCKER_PACKET_JSON = ROOT / "reports/operations/pipeline_direct_blocker_packet_latest.json"
STAGE13_JSON = ROOT / "reports/operations/stage13_completion_audit_latest.json"
REPORT_JSON = ROOT / "reports/operations/pipeline_blocked_stop_state_latest.json"
REPORT_MD = ROOT / "reports/operations/pipeline_blocked_stop_state_latest.md"


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def build_report(
    recheck: dict,
    next_command: dict,
    blocker_packet: dict,
    stage13: dict,
    generated_at: str | None = None,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    stage13_complete = bool(stage13.get("stage13_complete", False))
    direct_blockers = blocker_packet.get("direct_blockers", []) or []
    unblock_inputs = []
    for row in direct_blockers:
        if row.get("axis") == "BITHUMB_KRW":
            unblock_inputs.append(
                {
                    "axis": "BITHUMB_KRW",
                    "needed_input": "explicit human decision for current candidate",
                    "candidate_id": row.get("candidate_id"),
                    "allowed_decisions": row.get("required_decisions", []),
                    "current_blockers": row.get("current_blockers", []),
                }
            )
        elif row.get("axis") == "KIS_COMBINED_KRW":
            unblock_inputs.append(
                {
                    "axis": "KIS_COMBINED_KRW",
                    "needed_input": "reviewed axis-wide historical membership source export CSV",
                    "blocked_worklist_row_count": row.get("blocked_worklist_row_count"),
                    "current_blockers": row.get("current_blockers", []),
                    "raw_drop_dir": row.get("raw_drop_dir"),
                    "normalized_export_dir": row.get("normalized_export_dir"),
                    "manifest": row.get("manifest"),
                }
            )
    status = "COMPLETE" if stage13_complete else "STOPPED_BLOCKED_ON_EXTERNAL_OR_HUMAN_INPUT"
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "report": "pipeline_blocked_stop_state",
        "status": status,
        "objective": stage13.get("objective_restatement"),
        "completion_decision": stage13.get("completion_decision"),
        "stage13_complete": stage13_complete,
        "next_command_status": next_command.get("status"),
        "next_command_kind": next_command.get("command_kind"),
        "direct_blocker_count": blocker_packet.get("direct_blocker_count"),
        "unblock_inputs": unblock_inputs,
        "safe_recheck_command": "powershell -ExecutionPolicy Bypass -File .\\run_pipeline_direct_recheck.ps1",
        "must_not_do": [
            "do_not_enable_paper",
            "do_not_enable_live",
            "do_not_allow_broker_submit",
            "do_not_create_order_intent",
            "do_not_submit_orders",
            "do_not_run_generic_research_as_substitute",
        ],
        "safety": next_command.get("safety", stage13.get("safety", {})),
        "source_files": {
            "recheck": str(RECHECK_JSON),
            "next_command": str(NEXT_COMMAND_JSON),
            "blocker_packet": str(BLOCKER_PACKET_JSON),
            "stage13": str(STAGE13_JSON),
        },
    }


def render_md(report: dict) -> str:
    lines = [
        "# Pipeline Blocked Stop State",
        "",
        f"- Status: `{report['status']}`",
        f"- Completion: `{report.get('completion_decision')}`",
        f"- Stage13 complete: `{report['stage13_complete']}`",
        f"- Next command status: `{report.get('next_command_status')}`",
        f"- Safe recheck: `{report['safe_recheck_command']}`",
        "",
        "## Needed Inputs",
    ]
    for row in report.get("unblock_inputs", []):
        lines.extend(
            [
                f"- `{row['axis']}`: {row['needed_input']}",
                f"  - Candidate: `{row.get('candidate_id', 'n/a')}`",
                f"  - Blockers: `{', '.join(row.get('current_blockers', [])) if row.get('current_blockers') else 'none'}`",
            ]
        )
    lines.extend(["", "## Must Not Do"])
    lines.extend(f"- `{item}`" for item in report["must_not_do"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report(
        read_json(RECHECK_JSON, {}),
        read_json(NEXT_COMMAND_JSON, {}),
        read_json(BLOCKER_PACKET_JSON, {}),
        read_json(STAGE13_JSON, {}),
    )
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "completion_decision": report["completion_decision"],
                "stage13_complete": report["stage13_complete"],
                "direct_blocker_count": report["direct_blocker_count"],
                "latest_json": str(REPORT_JSON),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
