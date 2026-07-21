from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_kis_axis_wide_source_export_inbox_status as inbox_status_builder
import build_kis_axis_wide_source_export_intake_contract as intake_contract


KST = ZoneInfo("Asia/Seoul")
REPORT_JSON = ROOT / "reports/operations/kis_axis_wide_source_export_next_command_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_axis_wide_source_export_next_command_latest.md"
SAFETY = intake_contract.SAFETY


def _first_file(inbox_status: dict, role: str) -> dict | None:
    for row in inbox_status.get("files", []):
        if row.get("role") == role:
            return row
    return None


def _quote(value: str) -> str:
    return f'"{value}"'


def build_report(generated_at: str | None = None, inbox_status: dict | None = None) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    inbox_status = inbox_status or inbox_status_builder.build_report(generated_at)

    normalized = _first_file(inbox_status, "unreferenced_normalized_export")
    raw = _first_file(inbox_status, "unreferenced_raw_or_unknown_export")
    blockers: list[str] = []
    command_kind = "none"
    next_command = ""

    if normalized:
        rel = normalized.get("relative_path", "")
        status = "READY_NEXT_COMMAND_FOR_NORMALIZED_EXPORT"
        command_kind = "manifest_upsert_dry_run"
        next_command = (
            "python .\\upsert_kis_axis_wide_source_export_manifest_row.py "
            f"--local-file {_quote(rel)} "
            "--export-id REPLACE_EXPORT_ID "
            "--source-family REPLACE_SOURCE_FAMILY "
            "--source-name \"REPLACE_SOURCE_NAME\" "
            "--source-url \"REPLACE_SOURCE_URL\" "
            "--snapshot-id REPLACE_SNAPSHOT_ID "
            "--license-scope reviewed_internal_research "
            "--evidence-quality licensed_vendor "
            "--covered-axes REPLACE_AXIS"
        )
    elif raw:
        rel = raw.get("relative_path", "")
        stem = Path(rel).stem
        output = f"exports\\NORMALIZED_FROM_{stem}.csv"
        status = "READY_NEXT_COMMAND_FOR_RAW_EXPORT"
        command_kind = "normalizer_dry_run"
        next_command = (
            "python .\\normalize_kis_axis_wide_source_export.py "
            f"--raw-file {_quote(rel)} "
            f"--output-file {_quote(output)} "
            "--axis REPLACE_AXIS "
            "--asset-type REPLACE_ASSET_TYPE "
            "--source \"REPLACE_SOURCE_NAME\" "
            "--snapshot-id REPLACE_SNAPSHOT_ID "
            "--evidence-quality licensed_vendor "
            "--license-scope reviewed_internal_research "
            "--map symbol=REPLACE_SYMBOL_COLUMN "
            "--map active_from=REPLACE_ACTIVE_FROM_COLUMN"
        )
    else:
        status = "BLOCK_NO_ACTIONABLE_SOURCE_EXPORT_FILE"
        blockers.append("no_unreferenced_source_export_file")

    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "inbox_status": inbox_status.get("status"),
        "command_kind": command_kind,
        "next_command": next_command,
        "blockers": blockers,
        "single_next_action": "Place a reviewed raw or normalized KRX/licensed vendor CSV under axis_wide_source_exports.",
        "non_goals": [
            "does_not_execute_next_command",
            "does_not_normalize_files",
            "does_not_edit_manifest",
            "does_not_fill_replacement_worklists",
            "does_not_import_canonical_membership_rows",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    lines = [
        "# KIS Axis-Wide Source Export Next Command",
        "",
        f"- Status: `{report['status']}`",
        f"- Inbox status: `{report.get('inbox_status')}`",
        f"- Command kind: `{report['command_kind']}`",
        f"- Next command: `{report['next_command']}`",
        f"- Single next action: {report['single_next_action']}",
    ]
    if report.get("blockers"):
        lines.append(f"- Blockers: `{', '.join(report['blockers'])}`")
    return "\n".join(lines) + "\n"


def write_files(report: dict) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")


def main() -> int:
    report = build_report()
    write_files(report)
    print(json.dumps({
        "status": report["status"],
        "latest_json": str(REPORT_JSON),
        "command_kind": report["command_kind"],
        "next_command": report["next_command"],
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
