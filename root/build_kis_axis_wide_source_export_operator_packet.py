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
import build_kis_axis_wide_source_export_intake_contract as intake_contract_builder
import build_kis_axis_wide_source_export_next_command as next_command_builder


KST = ZoneInfo("Asia/Seoul")
REPORT_JSON = ROOT / "reports/operations/kis_axis_wide_source_export_operator_packet_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_axis_wide_source_export_operator_packet_latest.md"
SAFETY = intake_contract_builder.SAFETY
EXPORT_DIR = ROOT / "data_snapshots/kis_pit_membership/axis_wide_source_exports"
RUNBOOK = EXPORT_DIR / "README.md"


def _read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(
    generated_at: str | None = None,
    intake_contract: dict | None = None,
    feasibility_matrix: dict | None = None,
    krx_access_probe: dict | None = None,
    exports_to_worklist: dict | None = None,
    inbox_status: dict | None = None,
    next_command: dict | None = None,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    intake_contract = intake_contract or intake_contract_builder.build_report(generated_at, ensure_contract_files=True)
    feasibility_matrix = feasibility_matrix or _read_json(
        ROOT / "reports/operations/kis_axis_wide_historical_source_feasibility_matrix_latest.json"
    )
    krx_access_probe = krx_access_probe or _read_json(ROOT / "reports/operations/krx_data_marketplace_access_probe_latest.json")
    exports_to_worklist = exports_to_worklist or _read_json(
        ROOT / "reports/operations/kis_axis_wide_source_exports_to_replacement_worklist_latest.json"
    )
    inbox_status = inbox_status or inbox_status_builder.build_report(generated_at)
    next_command = next_command or next_command_builder.build_report(generated_at, inbox_status)

    valid_export_count = int(intake_contract.get("valid_export_count", 0) or 0)
    status = "READY_VALID_EXPORTS_PRESENT_REVIEW_MAPPER_DRY_RUN" if valid_export_count else "READY_OPERATOR_SOURCE_EXPORT_PACKET"

    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "operation_ready": False,
        "blocked_worklist_row_count": int(feasibility_matrix.get("blocked_worklist_row_count", 0) or 0),
        "valid_export_count": valid_export_count,
        "inbox_status": inbox_status.get("status"),
        "inbox_actionable_file_count": int(inbox_status.get("actionable_file_count", 0) or 0),
        "raw_drop_dir": inbox_status.get("raw_drop_dir", str(EXPORT_DIR / "raw")),
        "normalized_export_dir": inbox_status.get("normalized_export_dir", str(EXPORT_DIR / "exports")),
        "next_command_status": next_command.get("status"),
        "next_command_kind": next_command.get("command_kind"),
        "next_command": next_command.get("next_command", ""),
        "krx_unattended_access_blocked": krx_access_probe.get("status") == "BLOCK_KRX_DATA_MARKETPLACE_UNATTENDED_ACCESS",
        "paths": {
            "export_dir": str(EXPORT_DIR),
            "runbook": str(RUNBOOK),
            "manifest": str(intake_contract_builder.MANIFEST),
            "normalized_template": str(intake_contract_builder.NORMALIZED_TEMPLATE),
            "intake_contract_report": str(intake_contract_builder.REPORT_JSON),
            "mapper_report": str(ROOT / "reports/operations/kis_axis_wide_source_exports_to_replacement_worklist_latest.json"),
            "inbox_status_report": str(inbox_status_builder.REPORT_JSON),
            "next_command_report": str(next_command_builder.REPORT_JSON),
            "raw_export_normalizer": str(ROOT / "normalize_kis_axis_wide_source_export.py"),
            "manifest_row_upsert": str(ROOT / "upsert_kis_axis_wide_source_export_manifest_row.py"),
        },
        "required_manifest_columns": intake_contract.get("required_manifest_columns", intake_contract_builder.MANIFEST_COLUMNS),
        "required_normalized_columns": intake_contract.get("required_normalized_columns", intake_contract_builder.NORMALIZED_COLUMNS),
        "accepted_evidence_quality": sorted(intake_contract_builder.ACCEPTED_EVIDENCE),
        "source_options": [
            {
                "route": "KRX manual export",
                "covered_axes": ["kis_korea_stocks", "kis_korea_etfs"],
                "relevant_blocked_rows": 3857,
                "requirement": "Manual reviewed export because unattended KRX OTP currently returns LOGOUT.",
            },
            {
                "route": "Licensed security master / corporate actions vendor",
                "covered_axes": ["kis_us_stocks", "kis_us_etfs", "kis_korea_stocks", "kis_korea_etfs"],
                "relevant_blocked_rows": int(feasibility_matrix.get("blocked_worklist_row_count", 16444) or 16444),
                "requirement": "Vendor export with historical listing intervals, delistings, identifiers, source, snapshot_id, and license scope.",
            },
        ],
        "commands_after_files_are_placed": [
            "cd C:\\AI",
            "python .\\normalize_kis_axis_wide_source_export.py --raw-file raw\\YOUR_REVIEWED_RAW_EXPORT.csv --output-file exports\\YOUR_NORMALIZED_EXPORT.csv --axis kis_korea_stocks --asset-type korea_stock --source \"KRX Data Marketplace\" --snapshot-id krx_export_YYYYMMDD --evidence-quality exchange_official --license-scope reviewed_internal_research --map symbol=YOUR_SYMBOL_COLUMN --map active_from=YOUR_LISTED_DATE_COLUMN",
            "python .\\upsert_kis_axis_wide_source_export_manifest_row.py --export-id KRX_EXPORT_YYYYMMDD --source-family exchange_official --source-name \"KRX Data Marketplace\" --source-url https://data.krx.co.kr/ --local-file exports\\YOUR_NORMALIZED_EXPORT.csv --snapshot-id krx_export_YYYYMMDD --license-scope reviewed_internal_research --evidence-quality exchange_official --covered-axes kis_korea_stocks --replace-example",
            "python .\\build_kis_axis_wide_source_export_intake_contract.py",
            "python .\\apply_kis_axis_wide_source_exports_to_replacement_worklist.py",
            "python .\\build_kis_axis_wide_membership_worklist_fill_progress.py",
            "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120",
        ],
        "guarded_apply_commands_after_review": [
            "python .\\apply_kis_axis_wide_source_exports_to_replacement_worklist.py --apply --i-understand-source-exports-to-worklist \"APPLY KIS AXIS WIDE SOURCE EXPORTS TO WORKLIST REVIEWED NO_TRADING\"",
            "python .\\apply_kis_axis_wide_membership_worklist_to_shards.py --apply --i-understand-worklist-to-shards \"APPLY KIS AXIS WIDE WORKLIST TO SHARDS REVIEWED NO_TRADING\"",
            "python .\\apply_kis_axis_wide_membership_import.py --replace-caveated-axis --apply --i-understand-axis-wide-membership-import \"APPLY KIS AXIS WIDE MEMBERSHIP IMPORT REVIEWED NO_TRADING\"",
        ],
        "blockers": [],
        "single_next_action": "Add a reviewed normalized KRX or licensed vendor CSV under axis_wide_source_exports, replace the example manifest row, then run the intake contract validator.",
        "non_goals": [
            "does_not_provide_trading_approval",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
            "does_not_bypass_krx_login_or_license_terms",
            "does_not_apply_worklist_or_canonical_import_without_exact_confirmation",
        ],
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    lines = [
        "# KIS Axis-Wide Source Export Operator Packet",
        "",
        f"- Status: `{report['status']}`",
        f"- Valid export count: `{report['valid_export_count']}`",
        f"- Blocked worklist rows: `{report['blocked_worklist_row_count']}`",
        f"- Inbox status: `{report.get('inbox_status')}`",
        f"- Raw drop dir: `{report.get('raw_drop_dir')}`",
        f"- Normalized export dir: `{report.get('normalized_export_dir')}`",
        f"- Runbook: `{report['paths'].get('runbook')}`",
        "",
        "## Current Planned Next Command",
        "",
        f"`{report.get('next_command', '')}`",
        "",
        "## Commands After Files Are Placed",
        "",
    ]
    lines.extend(f"- `{cmd}`" for cmd in report["commands_after_files_are_placed"])
    lines.extend(["", "## Guarded Apply Commands After Review", ""])
    lines.extend(f"- `{cmd}`" for cmd in report["guarded_apply_commands_after_review"])
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
        "valid_export_count": report["valid_export_count"],
        "next_command_status": report["next_command_status"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
