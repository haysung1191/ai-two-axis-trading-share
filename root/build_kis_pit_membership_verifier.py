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
REPORT_JSON = ROOT / "reports/operations/kis_pit_membership_verifier_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_pit_membership_verifier_latest.md"
PREFLIGHT_JSON = ROOT / "reports/operations/kis_pit_intake_import_preflight_latest.json"
SOURCE_ARTIFACT_REGISTRY_JSON = ROOT / "reports/operations/kis_pit_source_artifact_registry_verifier_latest.json"
SOURCE_PROVENANCE_JSON = ROOT / "reports/operations/kis_pit_intake_source_provenance_verifier_latest.json"
SAFETY = intake_contract.SAFETY
AXES = ["kis_us_stocks", "kis_us_etfs", "kis_korea_stocks", "kis_korea_etfs"]
REQUIRED_COLUMNS = [
    "symbol",
    "asset_type",
    "axis",
    "active_from",
    "active_to",
    "listed_date",
    "delisted_date",
    "source",
    "snapshot_id",
    "evidence_quality",
    "notes",
]
OPERATION_READY_EVIDENCE = {"authoritative", "exchange_official", "licensed_vendor"}


def default_files() -> dict[str, Path]:
    return {
        axis: ROOT / f"data_snapshots/kis_pit_membership/{axis}_membership_intervals.csv"
        for axis in AXES
    }


def _read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), list(reader.fieldnames or [])


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _axis_report(axis: str, path: Path) -> dict:
    rows, headers = _read_rows(path)
    schema_ok = all(col in headers for col in REQUIRED_COLUMNS)
    caveated_rows = [row for row in rows if row.get("evidence_quality") == "current_snapshot_caveated"]
    ready_rows = [row for row in rows if row.get("evidence_quality") in OPERATION_READY_EVIDENCE]
    evidence_quality_counts = Counter(row.get("evidence_quality") or "missing" for row in rows)
    source_counts = Counter(row.get("source") or "missing" for row in rows)
    replacement_remaining_count = len(rows) - len(ready_rows)
    verified = path.exists() and schema_ok and bool(rows) and len(ready_rows) == len(rows)
    return {
        "axis": axis,
        "path": str(path),
        "exists": path.exists(),
        "schema_ok": schema_ok,
        "has_rows": bool(rows),
        "row_count": len(rows),
        "caveated_row_count": len(caveated_rows),
        "operation_ready_quality_row_count": len(ready_rows),
        "replacement_remaining_count": replacement_remaining_count,
        "operation_ready_coverage": (len(ready_rows) / len(rows)) if rows else 0.0,
        "evidence_quality_counts": dict(sorted(evidence_quality_counts.items())),
        "source_counts": dict(source_counts.most_common(10)),
        "verified": verified,
    }


def _next_evidence_targets(
    remediation_priority: list[dict],
    membership_ready_rows_by_axis: Counter,
    event_ready_rows_by_axis: Counter,
) -> list[dict]:
    targets = []
    for rank, row in enumerate(remediation_priority, start=1):
        gap = int(row.get("source_verified_membership_gap_after_ready_rows") or 0)
        if gap <= 0:
            continue
        axis = str(row.get("axis") or "unknown")
        membership_ready = int(membership_ready_rows_by_axis.get(axis, 0))
        event_ready = int(event_ready_rows_by_axis.get(axis, 0))
        reason = "largest_source_verified_membership_gap" if rank == 1 else "remaining_source_verified_membership_gap"
        if membership_ready == 0:
            reason = "zero_source_verified_membership_rows"
        targets.append(
            {
                "rank": rank,
                "axis": axis,
                "missing_membership_rows": gap,
                "source_verified_membership_ready_rows": membership_ready,
                "source_verified_event_ready_rows": event_ready,
                "ready_coverage_of_remaining": row.get("source_verified_membership_ready_coverage_of_remaining"),
                "recommended_source_class": "exchange_official_or_licensed_vendor_pit_membership_history",
                "recommended_artifact_kind": "membership_interval_source_package",
                "reason": reason,
            }
        )
    return targets


def build_report(
    generated_at: str | None = None,
    files: dict[str, Path] | None = None,
    preflight: dict | None = None,
    source_artifact_registry: dict | None = None,
    source_provenance: dict | None = None,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    files = files or default_files()
    preflight = preflight if preflight is not None else _read_json(PREFLIGHT_JSON)
    source_artifact_registry = source_artifact_registry if source_artifact_registry is not None else _read_json(SOURCE_ARTIFACT_REGISTRY_JSON)
    source_provenance = source_provenance if source_provenance is not None else _read_json(SOURCE_PROVENANCE_JSON)
    axis_reports = [_axis_report(axis, Path(files[axis])) for axis in AXES]
    all_files_exist = all(row["exists"] for row in axis_reports)
    all_schema_ok = all(row["schema_ok"] for row in axis_reports)
    all_have_rows = all(row["has_rows"] for row in axis_reports)
    all_schema_verified = all_files_exist and all_schema_ok and all_have_rows
    any_caveated_rows = any(row["caveated_row_count"] > 0 for row in axis_reports)
    all_verified = all(row["verified"] for row in axis_reports)
    blockers = []
    if not all_files_exist:
        blockers.append("canonical_membership_files_missing")
    if not all_schema_ok:
        blockers.append("canonical_membership_schema_invalid")
    if not all_have_rows:
        blockers.append("canonical_membership_files_empty")
    if any_caveated_rows:
        blockers.append("canonical_membership_evidence_quality_caveated_not_operation_ready")
    if all_schema_verified and not all_verified:
        blockers.append("authoritative_pit_membership_history_missing_for_kis_combined")
    if all_verified:
        status = "PASS_MEMBERSHIP_FILES_VERIFIED"
        blockers = []
    elif all_schema_verified:
        status = "PASS_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE"
    else:
        status = "BLOCK_INCOMPLETE_MEMBERSHIP_DATA"

    total_replacement_remaining = sum(row["replacement_remaining_count"] for row in axis_reports)
    source_verified_ready_rows = int(source_provenance.get("passed_ready_row_count") or 0)
    source_verified_registry_rows = int(source_artifact_registry.get("passed_registry_row_count") or 0)
    source_verified_coverage_gap = max(total_replacement_remaining - source_verified_ready_rows, 0)
    ready_rows = preflight.get("ready_rows", []) if isinstance(preflight.get("ready_rows", []), list) else []
    ready_rows_by_kind = Counter(str(row.get("kind") or "unknown") for row in ready_rows)
    ready_rows_by_axis = Counter(str(row.get("axis") or "unknown") for row in ready_rows)
    membership_ready_rows_by_axis = Counter(
        str(row.get("axis") or "unknown") for row in ready_rows if row.get("kind") == "membership"
    )
    event_ready_rows_by_axis = Counter(
        str(row.get("axis") or "unknown") for row in ready_rows if row.get("kind") == "event_or_no_event"
    )
    for row in axis_reports:
        membership_ready_count = int(membership_ready_rows_by_axis.get(row["axis"], 0))
        replacement_remaining = int(row["replacement_remaining_count"] or 0)
        row["source_verified_membership_ready_row_count"] = membership_ready_count
        row["source_verified_membership_gap_after_ready_rows"] = max(replacement_remaining - membership_ready_count, 0)
        row["source_verified_membership_ready_coverage_of_remaining"] = (
            membership_ready_count / replacement_remaining if replacement_remaining else 1.0
        )
    remediation_priority = sorted(
        (
            {
                "axis": row["axis"],
                "replacement_remaining_count": row["replacement_remaining_count"],
                "row_count": row["row_count"],
                "operation_ready_coverage": row["operation_ready_coverage"],
                "source_verified_membership_ready_row_count": row["source_verified_membership_ready_row_count"],
                "source_verified_membership_gap_after_ready_rows": row["source_verified_membership_gap_after_ready_rows"],
                "source_verified_membership_ready_coverage_of_remaining": row[
                    "source_verified_membership_ready_coverage_of_remaining"
                ],
                "dominant_evidence_quality": next(iter(row["evidence_quality_counts"]), None),
                "dominant_source": next(iter(row["source_counts"]), None),
            }
            for row in axis_reports
        ),
        key=lambda row: row["source_verified_membership_gap_after_ready_rows"],
        reverse=True,
    )
    top_priority = remediation_priority[0] if remediation_priority else {}
    next_evidence_acquisition_targets = _next_evidence_targets(
        remediation_priority,
        membership_ready_rows_by_axis,
        event_ready_rows_by_axis,
    )
    intake_source_package = {
        "preflight_status": preflight.get("status"),
        "preflight_ready_row_count": len(ready_rows),
        "preflight_ready_rows_by_kind": dict(sorted(ready_rows_by_kind.items())),
        "preflight_ready_rows_by_axis": dict(sorted(ready_rows_by_axis.items())),
        "membership_ready_rows_by_axis": dict(sorted(membership_ready_rows_by_axis.items())),
        "event_ready_rows_by_axis": dict(sorted(event_ready_rows_by_axis.items())),
        "source_artifact_registry_status": source_artifact_registry.get("status"),
        "source_artifact_registry_generated_at": source_artifact_registry.get("generated_at"),
        "source_artifact_registry_passed_rows": source_verified_registry_rows,
        "source_artifact_registry_blockers": source_artifact_registry.get("blockers", []),
        "source_provenance_status": source_provenance.get("status"),
        "source_provenance_generated_at": source_provenance.get("generated_at"),
        "source_provenance_passed_ready_rows": source_verified_ready_rows,
        "source_provenance_blocked_ready_rows": source_provenance.get("blocked_ready_row_count"),
        "source_provenance_blockers": source_provenance.get("blockers", []),
        "total_replacement_remaining_count": total_replacement_remaining,
        "source_verified_coverage_gap": source_verified_coverage_gap,
        "covers_remaining_replacement": source_verified_ready_rows >= total_replacement_remaining and total_replacement_remaining == 0,
    }

    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "universe_id": "KIS_COMBINED_KRW",
        "status": status,
        "operation_ready": all_verified,
        "all_files_exist": all_files_exist,
        "all_schema_ok": all_schema_ok,
        "all_have_rows": all_have_rows,
        "all_schema_verified": all_schema_verified,
        "any_caveated_rows": any_caveated_rows,
        "all_verified": all_verified,
        "axis_reports": axis_reports,
        "remediation_priority": remediation_priority,
        "next_evidence_acquisition_targets": next_evidence_acquisition_targets,
        "intake_source_package": intake_source_package,
        "blockers": sorted(set(blockers)),
        "single_next_action": (
            f"Replace {top_priority.get('source_verified_membership_gap_after_ready_rows', 0)} still-uncovered membership rows for "
            f"{top_priority.get('axis', 'KIS_COMBINED_KRW')} first; source-verified ready rows cover "
            f"{source_verified_ready_rows}/{total_replacement_remaining} remaining rows."
            if remediation_priority and not all_verified
            else "No PIT membership replacement needed."
        ),
        "non_goals": [
            "does_not_fetch_external_data",
            "does_not_import_rows",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    lines = ["# KIS PIT Membership Verifier", "", f"- Status: `{report['status']}`", ""]
    lines.extend(["| Axis | Rows | Ready | Caveated | Verified |", "|---|---:|---:|---:|---|"])
    for row in report["axis_reports"]:
        lines.append(
            f"| {row['axis']} | {row['row_count']} | {row['operation_ready_quality_row_count']} | {row['caveated_row_count']} | {row['verified']} |"
        )
    lines.extend(["", "## Remediation Priority", "", "| Axis | Remaining | Ready Coverage | Dominant Source |", "|---|---:|---:|---|"])
    for row in report.get("remediation_priority", []):
        lines.append(
            f"| {row['axis']} | {row['replacement_remaining_count']} | {row['operation_ready_coverage']:.2%} | {row.get('dominant_source') or '-'} |"
        )
    lines.extend(
        [
            "",
            "## Next Evidence Acquisition Targets",
            "",
            "| Rank | Axis | Missing Membership Rows | Ready Membership Rows | Reason |",
            "|---:|---|---:|---:|---|",
        ]
    )
    for row in report.get("next_evidence_acquisition_targets", []):
        lines.append(
            f"| {row['rank']} | {row['axis']} | {row['missing_membership_rows']} | {row['source_verified_membership_ready_rows']} | {row['reason']} |"
        )
    source_package = report.get("intake_source_package", {})
    lines.extend(
        [
            "",
            "## Intake Source Package",
            "",
            f"- Source artifact registry: `{source_package.get('source_artifact_registry_status') or '-'}`; passed rows `{source_package.get('source_artifact_registry_passed_rows')}`.",
            f"- Source provenance: `{source_package.get('source_provenance_status') or '-'}`; passed ready rows `{source_package.get('source_provenance_passed_ready_rows')}`.",
            f"- Ready rows by kind: `{source_package.get('preflight_ready_rows_by_kind') or {}}`.",
            f"- Membership ready rows by axis: `{source_package.get('membership_ready_rows_by_axis') or {}}`.",
            f"- Coverage gap: `{source_package.get('source_verified_coverage_gap')}` remaining rows not source-verified.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "operation_ready": report["operation_ready"],
        "blockers": report["blockers"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
