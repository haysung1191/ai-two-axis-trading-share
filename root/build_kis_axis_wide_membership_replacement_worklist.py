from __future__ import annotations

import csv
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
HANDOFF_PACKAGE_JSON = ROOT / "reports/operations/kis_axis_wide_membership_handoff_package_latest.json"
WORKLIST_DIR = ROOT / "data_snapshots/kis_pit_membership/axis_wide_handoff/replacement_worklists"
COMBINED_WORKLIST = WORKLIST_DIR / "kis_axis_wide_membership_replacement_worklist_latest.csv"
REPORT_JSON = ROOT / "reports/operations/kis_axis_wide_membership_replacement_worklist_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_axis_wide_membership_replacement_worklist_latest.md"
SAFETY = intake_contract.SAFETY

WORKLIST_COLUMNS = [
    "request_id",
    "axis",
    "symbol",
    "asset_type",
    "current_active_from",
    "current_active_to",
    "current_listed_date",
    "current_delisted_date",
    "current_source",
    "current_snapshot_id",
    "current_evidence_quality",
    "current_notes",
    "target_response_shard",
    "request_source_verified_ready_row_count",
    "request_source_verified_gap_after_ready_rows",
    "request_required_source_acquisition_row_count",
    "required_replacement_evidence_quality",
    "accepted_source_family",
    "replacement_symbol",
    "replacement_asset_type",
    "replacement_active_from",
    "replacement_active_to",
    "replacement_listed_date",
    "replacement_delisted_date",
    "replacement_source",
    "replacement_snapshot_id",
    "replacement_evidence_quality",
    "replacement_notes",
]


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=WORKLIST_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{col: row.get(col, "") for col in WORKLIST_COLUMNS} for row in rows])


def _axis_worklist_path(axis: str) -> Path:
    safe_axis = axis.replace("/", "_").replace("\\", "_")
    return WORKLIST_DIR / f"{safe_axis}_replacement_worklist_latest.csv"


def _response_shard_for_request(package: dict) -> dict[str, str]:
    return {
        row.get("request_id", ""): row.get("path", "")
        for row in package.get("response_shards", [])
        if row.get("request_id") and row.get("path")
    }


def _worklist_row(request: dict[str, str], membership: dict[str, str], target_response_shard: str) -> dict[str, str]:
    return {
        "request_id": request.get("request_id", ""),
        "axis": request.get("axis", membership.get("axis", "")),
        "symbol": membership.get("symbol", ""),
        "asset_type": membership.get("asset_type", ""),
        "current_active_from": membership.get("active_from", ""),
        "current_active_to": membership.get("active_to", ""),
        "current_listed_date": membership.get("listed_date", ""),
        "current_delisted_date": membership.get("delisted_date", ""),
        "current_source": membership.get("source", ""),
        "current_snapshot_id": membership.get("snapshot_id", ""),
        "current_evidence_quality": membership.get("evidence_quality", ""),
        "current_notes": membership.get("notes", ""),
        "target_response_shard": target_response_shard,
        "request_source_verified_ready_row_count": str(request.get("source_verified_ready_row_count", "")),
        "request_source_verified_gap_after_ready_rows": str(request.get("source_verified_gap_after_ready_rows", "")),
        "request_required_source_acquisition_row_count": str(request.get("required_source_acquisition_row_count", "")),
        "required_replacement_evidence_quality": "authoritative|exchange_official|licensed_vendor",
        "accepted_source_family": "licensed security master, exchange listing history, or official issuer/exchange action feed",
        "replacement_symbol": membership.get("symbol", ""),
        "replacement_asset_type": membership.get("asset_type", ""),
        "replacement_active_from": "",
        "replacement_active_to": "",
        "replacement_listed_date": "",
        "replacement_delisted_date": "",
        "replacement_source": "",
        "replacement_snapshot_id": "",
        "replacement_evidence_quality": "",
        "replacement_notes": "",
    }


def build_report(generated_at: str | None = None, package: dict | None = None, write_files: bool = False) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    package = package or _read_json(HANDOFF_PACKAGE_JSON)
    shard_by_request = _response_shard_for_request(package)
    worklist_rows = []
    axis_reports = []
    blockers = []

    for request in package.get("request_rows", []):
        request_id = request.get("request_id", "")
        axis = request.get("axis", "")
        target = request.get("canonical_target_file", "")
        target_response_shard = shard_by_request.get(request_id, request.get("target_response_shard", ""))
        memberships = _read_csv(Path(target))
        caveated_rows = [
            row for row in memberships
            if row.get("evidence_quality") == "current_snapshot_caveated"
        ]
        request_rows = [_worklist_row(request, row, target_response_shard) for row in caveated_rows]
        worklist_rows.extend(request_rows)
        required = int(request.get("current_caveated_row_count", len(caveated_rows)) or 0)
        required_source_acquisition = int(request.get("required_source_acquisition_row_count", required) or 0)
        source_verified_ready = int(request.get("source_verified_ready_row_count", 0) or 0)
        source_verified_gap = int(request.get("source_verified_gap_after_ready_rows", required_source_acquisition) or 0)
        row_count_matches = len(request_rows) == required
        if not row_count_matches:
            blockers.append(f"worklist_count_mismatch_for_{request_id}")
        axis_reports.append({
            "request_id": request_id,
            "axis": axis,
            "canonical_target_file": target,
            "target_response_shard": target_response_shard,
            "worklist_row_count": len(request_rows),
            "required_replacement_row_count": required,
            "source_verified_ready_row_count": source_verified_ready,
            "source_verified_gap_after_ready_rows": source_verified_gap,
            "required_source_acquisition_row_count": required_source_acquisition,
            "row_count_matches_required": row_count_matches,
        })

    status = "READY_AXIS_WIDE_REPLACEMENT_WORKLISTS" if not blockers else "BLOCK_AXIS_WIDE_REPLACEMENT_WORKLISTS"
    report = {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "universe_id": "KIS_COMBINED_KRW",
        "status": status,
        "operation_ready": False,
        "worklist_row_count": len(worklist_rows),
        "axis_reports": axis_reports,
        "blockers": sorted(set(blockers)),
        "single_next_action": "Fill replacement_* fields from authoritative/licensed membership-history evidence, then copy reviewed rows into the target response shard files.",
        "non_goals": [
            "does_not_fill_authoritative_evidence",
            "does_not_import_rows",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
        "source_files": {"handoff_package": str(HANDOFF_PACKAGE_JSON)},
        "output_files": {
            "combined_worklist_csv": str(COMBINED_WORKLIST),
            "worklist_dir": str(WORKLIST_DIR),
            "latest_json": str(REPORT_JSON),
            "latest_md": str(REPORT_MD),
        },
        "worklist_rows": worklist_rows,
    }
    if write_files:
        write_report(report)
    return report


def render_md(report: dict) -> str:
    lines = [
        "# KIS Axis-Wide Membership Replacement Worklist",
        "",
        f"- Status: `{report['status']}`",
        f"- Worklist rows: `{report['worklist_row_count']}`",
        "",
        "| Request | Axis | Rows | Required | Source gap | Match |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in report.get("axis_reports", []):
        lines.append(
            f"| {row['request_id']} | {row['axis']} | {row['worklist_row_count']} | {row['required_replacement_row_count']} | {row.get('required_source_acquisition_row_count')} | {row['row_count_matches_required']} |"
        )
    return "\n".join(lines) + "\n"


def write_report(report: dict) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    _write_csv(COMBINED_WORKLIST, report["worklist_rows"])
    for axis in sorted({row.get("axis", "") for row in report["worklist_rows"] if row.get("axis")}):
        _write_csv(_axis_worklist_path(axis), [row for row in report["worklist_rows"] if row.get("axis") == axis])


def main() -> int:
    report = build_report(write_files=True)
    print(json.dumps({
        "status": report["status"],
        "worklist_row_count": report["worklist_row_count"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
