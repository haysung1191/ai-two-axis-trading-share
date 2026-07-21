from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_kis_axis_wide_source_export_intake_contract as intake_contract


KST = ZoneInfo("Asia/Seoul")
PACKAGE_JSON = ROOT / "reports/operations/kis_axis_wide_membership_handoff_package_latest.json"
RESPONSE_PATH = ROOT / "data_snapshots/kis_pit_membership/axis_wide_handoff/kis_axis_wide_membership_response_template.csv"
REPORT_JSON = ROOT / "reports/operations/kis_axis_wide_membership_response_validator_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_axis_wide_membership_response_validator_latest.md"
SAFETY = intake_contract.SAFETY
REQUIRED_FIELDS = ["symbol", "asset_type", "active_from", "source", "snapshot_id", "evidence_quality"]
REJECTED_SOURCE_MARKERS = ["current_snapshot_caveated", "current_full_market_universe_snapshot"]


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def response_input_files(package: dict, response_path: Path = RESPONSE_PATH) -> list[str]:
    files = [str(response_path)]
    for shard in package.get("response_shards", []):
        path = shard.get("path")
        if path:
            files.append(str(path))
    return files


def read_response_rows(package: dict, response_path: Path = RESPONSE_PATH) -> list[dict[str, str]]:
    rows = []
    for path_text in response_input_files(package, response_path):
        rows.extend(_read_csv(Path(path_text)))
    nonblank_request_ids = {
        row.get("request_id", "")
        for row in rows
        if row.get("request_id") and any(row.get(field, "").strip() for field in REQUIRED_FIELDS)
    }
    filtered = []
    for row in rows:
        if row.get("request_id") in nonblank_request_ids and not any(row.get(field, "").strip() for field in REQUIRED_FIELDS):
            continue
        filtered.append(row)
    return filtered


def _request_axis(package: dict) -> dict[str, str]:
    return {row.get("request_id", ""): row.get("axis", "") for row in package.get("request_rows", [])}


def _required_replacements(package: dict) -> dict[str, int]:
    return {
        row.get("request_id", ""): int(row.get("current_caveated_row_count", 1) or 1)
        for row in package.get("request_rows", [])
    }


def _row_blockers(row: dict[str, str], expected_axis: str) -> tuple[list[str], list[str], list[str]]:
    missing = [field for field in REQUIRED_FIELDS if not row.get(field, "").strip()]
    rejected = [marker for marker in REJECTED_SOURCE_MARKERS if marker in row.get("source", "")]
    blockers = []
    if missing:
        blockers.append("required_fields_missing")
    if len(missing) == len(REQUIRED_FIELDS):
        blockers.append("response_row_blank")
    if rejected:
        blockers.append("rejected_source_marker_found")
    if row.get("axis") != expected_axis:
        blockers.append("axis_does_not_match_request")
    if row.get("evidence_quality") and row.get("evidence_quality") not in intake_contract.ACCEPTED_EVIDENCE:
        blockers.append("evidence_quality_not_operation_ready")
    return blockers, missing, rejected


def build_report(
    generated_at: str | None = None,
    package: dict | None = None,
    response_rows: list[dict[str, str]] | None = None,
    response_path: Path = RESPONSE_PATH,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    package = package or _read_json(PACKAGE_JSON)
    response_rows = response_rows if response_rows is not None else read_response_rows(package, response_path)
    axis_by_request = _request_axis(package)
    required_by_request = _required_replacements(package)
    valid_rows = []
    blocked_rows = []
    valid_by_request: Counter = Counter()

    for row_number, row in enumerate(response_rows, start=2):
        request_id = row.get("request_id", "")
        blockers, missing, rejected = _row_blockers(row, axis_by_request.get(request_id, ""))
        wrapped = {"request_id": request_id, "axis": row.get("axis", ""), "symbol": row.get("symbol", ""), "row": row}
        if blockers:
            blocked_rows.append({
                "row_number": row_number,
                "request_id": request_id,
                "axis": row.get("axis", ""),
                "symbol": row.get("symbol", ""),
                "missing_fields": missing,
                "rejected_markers": rejected,
                "blockers": blockers,
                "row": row,
            })
        else:
            valid_rows.append(wrapped)
            valid_by_request[request_id] += 1

    coverage_rows = []
    for request_id, required in required_by_request.items():
        valid_count = valid_by_request[request_id]
        coverage_rows.append({
            "request_id": request_id,
            "axis": axis_by_request.get(request_id, ""),
            "required_replacement_row_count": required,
            "valid_replacement_row_count": valid_count,
            "replacement_coverage_sufficient": valid_count >= required,
            "remaining_replacement_row_count": max(required - valid_count, 0),
        })
    insufficient = [row for row in coverage_rows if not row["replacement_coverage_sufficient"]]
    blockers = []
    if blocked_rows:
        blockers.append("blocked_response_rows_present")
    if not valid_rows:
        blockers.append("no_valid_axis_membership_rows")
    if insufficient:
        blockers.append("axis_replacement_coverage_insufficient")
    replacement_coverage_sufficient = not insufficient
    status = "READY_AXIS_WIDE_MEMBERSHIP_IMPORT_REVIEW" if not blockers else "BLOCK_AXIS_WIDE_MEMBERSHIP_RESPONSE"

    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "universe_id": "KIS_COMBINED_KRW",
        "status": status,
        "operation_ready": False,
        "response_path": str(response_path),
        "request_count": int(package.get("request_count", len(package.get("request_rows", []))) or 0),
        "response_row_count": len(response_rows),
        "valid_row_count": len(valid_rows),
        "blocked_row_count": len(blocked_rows),
        "replacement_coverage_rows": coverage_rows,
        "replacement_coverage_sufficient": replacement_coverage_sufficient,
        "insufficient_replacement_coverage_rows": insufficient,
        "valid_rows": valid_rows,
        "blocked_rows": blocked_rows,
        "blockers": sorted(set(blockers)),
        "next_safe_action": "Fill enough axis-wide membership response rows with authoritative/licensed evidence to replace current caveated rows before import review.",
        "non_goals": [
            "does_not_import_rows",
            "does_not_mark_membership_operation_ready",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
        "source_files": {
            "handoff_package": str(PACKAGE_JSON),
            "response_template": str(response_path),
        },
        "response_input_files": response_input_files(package, response_path),
    }


def render_md(report: dict) -> str:
    return "\n".join([
        "# KIS Axis-Wide Membership Response Validator",
        "",
        f"- Status: `{report['status']}`",
        f"- Valid rows: `{report['valid_row_count']}`",
        f"- Blocked rows: `{report['blocked_row_count']}`",
        f"- Replacement coverage sufficient: `{report['replacement_coverage_sufficient']}`",
    ]) + "\n"


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "valid_row_count": report["valid_row_count"],
        "blocked_row_count": report["blocked_row_count"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
