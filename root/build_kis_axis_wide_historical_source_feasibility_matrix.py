from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_kis_axis_wide_source_export_intake_contract as intake_contract


KST = ZoneInfo("Asia/Seoul")
FILL_REPORT_JSON = ROOT / "reports/operations/kis_axis_wide_membership_worklist_fill_progress_latest.json"
REPORT_JSON = ROOT / "reports/operations/kis_axis_wide_historical_source_feasibility_matrix_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_axis_wide_historical_source_feasibility_matrix_latest.md"
SAFETY = intake_contract.SAFETY


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _source_candidates() -> list[dict]:
    return [
        {
            "source_id": "LICENSED_SECURITY_MASTER_VENDOR",
            "source_name": "Licensed security master / corporate actions vendor",
            "covered_axes": ["kis_us_stocks", "kis_us_etfs", "kis_korea_stocks", "kis_korea_etfs"],
            "feasibility": "PROMISING_REQUIRES_REVIEWED_EXPORT",
            "direct_replacement_ready": False,
            "required_fields": ["symbol", "asset_type", "active_from", "active_to", "source", "snapshot_id", "evidence_quality"],
        },
        {
            "source_id": "KRX_DATA_MARKETPLACE_LISTED_DELISTED",
            "source_name": "KRX Data Marketplace listed/delisted history",
            "covered_axes": ["kis_korea_stocks", "kis_korea_etfs"],
            "feasibility": "PROMISING_REQUIRES_MANUAL_LOGIN_EXPORT",
            "direct_replacement_ready": False,
            "required_fields": ["symbol", "listed_date", "delisted_date", "source", "snapshot_id", "evidence_quality"],
        },
        {
            "source_id": "NASDAQ_TRADER_SYMBOL_DIRECTORY",
            "source_name": "NASDAQ Trader symbol directory",
            "covered_axes": ["kis_us_stocks", "kis_us_etfs"],
            "feasibility": "CURRENT_SNAPSHOT_ONLY_NOT_HISTORICAL_PIT",
            "direct_replacement_ready": False,
            "required_fields": [],
        },
        {
            "source_id": "OFFICIAL_KIS_MASTER_SNAPSHOTS",
            "source_name": "Official KIS current master snapshots",
            "covered_axes": ["kis_us_stocks", "kis_us_etfs", "kis_korea_stocks", "kis_korea_etfs"],
            "feasibility": "CURRENT_SNAPSHOT_ONLY_NOT_HISTORICAL_PIT",
            "direct_replacement_ready": False,
            "required_fields": [],
        },
    ]


def build_report(generated_at: str | None = None, fill_report: dict | None = None) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    fill_report = fill_report or _read_json(FILL_REPORT_JSON)
    candidates = _source_candidates()
    blocked = int(fill_report.get("blocked_row_count", 0) or 0)
    if not blocked:
        blocked = sum(int(row.get("blocked_row_count", 0) or 0) for row in fill_report.get("axis_reports", []))
    direct_count = sum(1 for row in candidates if row["direct_replacement_ready"])
    promising_count = sum(1 for row in candidates if row["feasibility"].startswith("PROMISING"))
    status = "READY_DIRECT_OPERATION_READY_HISTORICAL_SOURCE_CAPTURED" if direct_count else "BLOCK_NO_DIRECT_OPERATION_READY_HISTORICAL_SOURCE_CAPTURED"
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "universe_id": "KIS_COMBINED_KRW",
        "status": status,
        "blocked_worklist_row_count": blocked,
        "direct_operation_ready_source_count": direct_count,
        "promising_source_count": promising_count,
        "source_candidates": candidates,
        "single_next_action": "Obtain a reviewed KRX or licensed vendor export and place it under axis_wide_source_exports.",
        "non_goals": [
            "does_not_download_or_scrape_licensed_data",
            "does_not_import_rows",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    lines = [
        "# KIS Axis-Wide Historical Source Feasibility Matrix",
        "",
        f"- Status: `{report['status']}`",
        f"- Blocked worklist rows: `{report['blocked_worklist_row_count']}`",
        f"- Single next action: {report['single_next_action']}",
        "",
        "| Source | Feasibility | Direct ready |",
        "|---|---|---|",
    ]
    for row in report["source_candidates"]:
        lines.append(f"| {row['source_id']} | {row['feasibility']} | {row['direct_replacement_ready']} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "blocked_worklist_row_count": report["blocked_worklist_row_count"],
        "direct_operation_ready_source_count": report["direct_operation_ready_source_count"],
        "promising_source_count": report["promising_source_count"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
