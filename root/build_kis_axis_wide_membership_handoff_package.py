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
QUEUE_JSON = ROOT / "reports/operations/kis_pit_source_acquisition_queue_latest.json"
MEMBERSHIP_VERIFIER_JSON = ROOT / "reports/operations/kis_pit_membership_verifier_latest.json"
GAP_MATRIX_JSON = ROOT / "reports/operations/kis_historical_pit_survivorship_gap_matrix_latest.json"
HANDOFF_DIR = ROOT / "data_snapshots/kis_pit_membership/axis_wide_handoff"
RESPONSE_TEMPLATE = HANDOFF_DIR / "kis_axis_wide_membership_response_template.csv"
RESPONSE_SHARD_DIR = HANDOFF_DIR / "response_shards"
RESPONSE_SHARD_MANIFEST = HANDOFF_DIR / "kis_axis_wide_membership_response_shard_manifest_latest.csv"
REPORT_JSON = ROOT / "reports/operations/kis_axis_wide_membership_handoff_package_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_axis_wide_membership_handoff_package_latest.md"
SAFETY = intake_contract.SAFETY
AXES = ["kis_us_stocks", "kis_us_etfs", "kis_korea_stocks", "kis_korea_etfs"]
RESPONSE_COLUMNS = [
    "request_id",
    "axis",
    "symbol",
    "asset_type",
    "active_from",
    "active_to",
    "listed_date",
    "delisted_date",
    "source",
    "snapshot_id",
    "evidence_quality",
    "notes",
]
SHARD_MANIFEST_COLUMNS = [
    "request_id",
    "axis",
    "path",
    "required_replacement_row_count",
    "source_verified_ready_row_count",
    "source_verified_gap_after_ready_rows",
    "preserved_response_row_count",
    "blank_seed_response_row_count",
    "remaining_replacement_row_count",
    "remaining_source_acquisition_row_count",
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


def _generated_at_utc(generated_at: str) -> str:
    parsed = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(ZoneInfo("UTC")).isoformat()


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{col: row.get(col, "") for col in fieldnames} for row in rows])


def response_shard_path(request: dict[str, str]) -> Path:
    request_id = request.get("request_id", "")
    axis = request.get("axis", "")
    return RESPONSE_SHARD_DIR / f"{request_id}_{axis}_response.csv"


def _blank_response_row(request: dict[str, str]) -> dict[str, str]:
    return {col: "" for col in RESPONSE_COLUMNS} | {
        "request_id": request.get("request_id", ""),
        "axis": request.get("axis", ""),
    }


def _is_nonblank_response(row: dict[str, str]) -> bool:
    return any(row.get(field, "").strip() for field in ["symbol", "asset_type", "active_from", "source", "snapshot_id", "evidence_quality"])


def merge_existing_response_rows(request_rows: list[dict[str, str]], existing_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    request_by_axis = {row.get("axis", ""): row for row in request_rows}
    merged = []
    axes_with_content = set()
    for row in existing_rows:
        axis = row.get("axis", "")
        request = request_by_axis.get(axis)
        if not request:
            continue
        updated = {col: row.get(col, "") for col in RESPONSE_COLUMNS}
        updated["request_id"] = request.get("request_id", "")
        updated["axis"] = axis
        if _is_nonblank_response(updated):
            axes_with_content.add(axis)
            merged.append(updated)
    for request in request_rows:
        if request.get("axis", "") not in axes_with_content:
            merged.append(_blank_response_row(request))
    return merged


def build_shard_manifest_rows(shards: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{col: row.get(col, "") for col in SHARD_MANIFEST_COLUMNS} for row in shards]


def _membership_by_axis(membership_verifier: dict) -> dict[str, dict]:
    return {row.get("axis", ""): row for row in membership_verifier.get("axis_reports", [])}


def _target_file(axis: str) -> str:
    return str(ROOT / f"data_snapshots/kis_pit_membership/{axis}_membership_intervals.csv")


def _request_rows(queue: dict, membership_verifier: dict) -> list[dict[str, str]]:
    axis_items = [row for row in queue.get("queue", []) if row.get("lane") == "axis_wide_operation_ready" and row.get("axis") in AXES]
    axis_set = {row.get("axis") for row in axis_items}
    verifier = _membership_by_axis(membership_verifier)
    rows = []
    for index, axis in enumerate(AXES, start=1):
        if axis not in axis_set:
            continue
        v = verifier.get(axis, {})
        request_id = f"KIS_AXIS_{index:03d}"
        current_caveated = int(v.get("caveated_row_count", 0) or 0)
        source_verified_ready = int(v.get("source_verified_membership_ready_row_count", 0) or 0)
        source_verified_gap = int(
            v.get("source_verified_membership_gap_after_ready_rows", current_caveated) or 0
        )
        request = {
            "request_id": request_id,
            "axis": axis,
            "canonical_target_file": v.get("path", _target_file(axis)),
            "current_row_count": int(v.get("row_count", 0) or 0),
            "current_caveated_row_count": current_caveated,
            "current_operation_ready_row_count": int(v.get("operation_ready_quality_row_count", 0) or 0),
            "source_verified_ready_row_count": source_verified_ready,
            "source_verified_gap_after_ready_rows": source_verified_gap,
            "accepted_evidence_quality": "authoritative|exchange_official|licensed_vendor",
            "rejected_shortcuts": "current_snapshot_caveated|historical_replay_only|unsourced_current_master",
            "required_fields": "symbol|asset_type|active_from|source|snapshot_id|evidence_quality",
        }
        request["path"] = str(response_shard_path(request))
        request["target_response_shard"] = request["path"]
        request["required_replacement_row_count"] = current_caveated
        request["required_source_acquisition_row_count"] = source_verified_gap
        rows.append(request)
    return rows


def build_report(
    generated_at: str | None = None,
    queue: dict | None = None,
    membership_verifier: dict | None = None,
    gap_matrix: dict | None = None,
    write_files: bool = False,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    queue = queue or _read_json(QUEUE_JSON)
    membership_verifier = membership_verifier or _read_json(MEMBERSHIP_VERIFIER_JSON)
    gap_matrix = gap_matrix or _read_json(GAP_MATRIX_JSON)
    request_rows = _request_rows(queue, membership_verifier)
    blockers = []
    has_four = len(request_rows) == 4
    broad_queue_ok = queue.get("queue_counts", {}).get("axis_wide_operation_ready") == 4
    if queue.get("status") != "BLOCK_AXIS_WIDE_SOURCE_ACQUISITION_REQUIRED" and not broad_queue_ok:
        blockers.append("axis_wide_source_queue_not_active")
    if not has_four:
        blockers.append("expected_four_axis_wide_requests")

    existing_rows = _read_csv(RESPONSE_TEMPLATE)
    response_template_rows = merge_existing_response_rows(request_rows, existing_rows)
    shards = []
    for request in request_rows:
        preserved = [
            row for row in response_template_rows
            if row.get("request_id") == request.get("request_id") and _is_nonblank_response(row)
        ]
        blank = [
            row for row in response_template_rows
            if row.get("request_id") == request.get("request_id") and not _is_nonblank_response(row)
        ]
        remaining = max(int(request.get("required_replacement_row_count", 0) or 0) - len(preserved), 0)
        remaining_after_ready = max(
            int(request.get("required_source_acquisition_row_count", 0) or 0) - len(preserved),
            0,
        )
        shards.append({
            "request_id": request.get("request_id", ""),
            "axis": request.get("axis", ""),
            "path": str(response_shard_path(request)),
            "required_replacement_row_count": int(request.get("required_replacement_row_count", 0) or 0),
            "source_verified_ready_row_count": int(request.get("source_verified_ready_row_count", 0) or 0),
            "source_verified_gap_after_ready_rows": int(
                request.get("source_verified_gap_after_ready_rows", request.get("required_replacement_row_count", 0)) or 0
            ),
            "preserved_response_row_count": len(preserved),
            "blank_seed_response_row_count": len(blank),
            "remaining_replacement_row_count": remaining,
            "remaining_source_acquisition_row_count": remaining_after_ready,
        })

    report = {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "generated_at_utc": _generated_at_utc(generated_at),
        "universe_id": "KIS_COMBINED_KRW",
        "status": "READY_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE" if not blockers else "BLOCK_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE",
        "operation_ready": False,
        "request_count": len(request_rows),
        "axis_count": len({row.get("axis", "") for row in request_rows}),
        "request_rows": request_rows,
        "response_template_rows": response_template_rows,
        "response_shards": shards,
        "response_shard_manifest_rows": build_shard_manifest_rows(shards),
        "blockers": sorted(set(blockers)),
        "single_next_action": "Fill enough axis-wide membership response rows with authoritative/licensed evidence.",
        "non_goals": [
            "does_not_fetch_external_data",
            "does_not_import_rows",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
        "source_files": {
            "source_acquisition_queue": str(QUEUE_JSON),
            "membership_verifier": str(MEMBERSHIP_VERIFIER_JSON),
            "gap_matrix": str(GAP_MATRIX_JSON),
        },
        "output_files": {
            "response_template": str(RESPONSE_TEMPLATE),
            "response_shard_manifest": str(RESPONSE_SHARD_MANIFEST),
            "latest_json": str(REPORT_JSON),
            "latest_md": str(REPORT_MD),
        },
    }
    if write_files:
        write_report(report)
    return report


def render_md(report: dict) -> str:
    lines = [
        "# KIS Axis-Wide Membership Handoff Package",
        "",
        f"- Status: `{report['status']}`",
        f"- Requests: `{report['request_count']}`",
        "",
        "| Request | Axis | Required replacements |",
        "|---|---|---:|",
    ]
    for row in report.get("request_rows", []):
        lines.append(
            f"| {row['request_id']} | {row['axis']} | "
            f"{row['required_replacement_row_count']} "
            f"(source gap {row.get('required_source_acquisition_row_count', row['required_replacement_row_count'])}) |"
        )
    return "\n".join(lines) + "\n"


def write_report(report: dict) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    _write_csv(RESPONSE_TEMPLATE, report["response_template_rows"], RESPONSE_COLUMNS)
    _write_csv(RESPONSE_SHARD_MANIFEST, report["response_shard_manifest_rows"], SHARD_MANIFEST_COLUMNS)
    for shard in report["response_shards"]:
        path = Path(shard["path"])
        rows = [
            row for row in report["response_template_rows"]
            if row.get("request_id") == shard["request_id"]
        ]
        _write_csv(path, rows, RESPONSE_COLUMNS)


def main() -> int:
    report = build_report(write_files=True)
    print(json.dumps({
        "status": report["status"],
        "request_count": report["request_count"],
        "axis_count": report["axis_count"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
