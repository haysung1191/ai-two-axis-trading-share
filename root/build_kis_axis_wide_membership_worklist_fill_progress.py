from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_kis_axis_wide_source_export_intake_contract as intake_contract


KST = ZoneInfo("Asia/Seoul")
WORKLIST = ROOT / "data_snapshots/kis_pit_membership/axis_wide_handoff/replacement_worklists/kis_axis_wide_membership_replacement_worklist_latest.csv"
REPORT_JSON = ROOT / "reports/operations/kis_axis_wide_membership_worklist_fill_progress_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_axis_wide_membership_worklist_fill_progress_latest.md"
SAFETY = intake_contract.SAFETY
ACCEPTED_EVIDENCE = intake_contract.ACCEPTED_EVIDENCE
REQUIRED_REPLACEMENT_FIELDS = [
    "replacement_symbol",
    "replacement_asset_type",
    "replacement_active_from",
    "replacement_source",
    "replacement_snapshot_id",
    "replacement_evidence_quality",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _row_blockers(row: dict[str, str]) -> list[str]:
    blockers = []
    for field in REQUIRED_REPLACEMENT_FIELDS:
        if not row.get(field, "").strip():
            blockers.append(field)
    evidence = row.get("replacement_evidence_quality", "")
    if evidence and evidence not in ACCEPTED_EVIDENCE:
        blockers.append("replacement_evidence_quality_not_operation_ready")
    return blockers


def build_report(generated_at: str | None = None, rows: list[dict[str, str]] | None = None) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    rows = rows if rows is not None else _read_csv(WORKLIST)
    complete_rows = []
    blocked_rows = []
    axis_missing: dict[str, Counter] = defaultdict(Counter)
    axis_samples: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row_number, row in enumerate(rows, start=2):
        blockers = _row_blockers(row)
        axis = row.get("axis", "")
        if blockers:
            blocked = {
                "row_number": row_number,
                "axis": axis,
                "symbol": row.get("symbol", ""),
                "asset_type": row.get("asset_type", ""),
                "blockers": blockers,
            }
            blocked_rows.append(blocked)
            for blocker in blockers:
                axis_missing[axis][blocker] += 1
            if len(axis_samples[axis]) < 10:
                axis_samples[axis].append(blocked)
        else:
            complete_rows.append(row)

    axis_reports = []
    for axis in sorted({row.get("axis", "") for row in rows} | set(axis_missing)):
        axis_rows = [row for row in rows if row.get("axis", "") == axis]
        source_required = max(
            (int(row.get("request_required_source_acquisition_row_count") or 0) for row in axis_rows),
            default=0,
        )
        source_ready = max(
            (int(row.get("request_source_verified_ready_row_count") or 0) for row in axis_rows),
            default=0,
        )
        source_gap = max(
            (int(row.get("request_source_verified_gap_after_ready_rows") or 0) for row in axis_rows),
            default=source_required,
        )
        complete_axis_count = len([row for row in axis_rows if not _row_blockers(row)])
        blocked_count = sum(axis_missing[axis].values())
        axis_reports.append({
            "axis": axis,
            "row_count": len(axis_rows),
            "complete_row_count": complete_axis_count,
            "blocked_row_count": len([row for row in axis_rows if _row_blockers(row)]),
            "source_verified_ready_row_count": source_ready,
            "source_verified_gap_after_ready_rows": source_gap,
            "required_source_acquisition_row_count": source_required,
            "complete_source_acquisition_row_count": min(complete_axis_count, source_required),
            "remaining_source_acquisition_row_count": max(source_required - complete_axis_count, 0),
            "missing_field_counts": dict(axis_missing[axis]),
            "blocked_samples": axis_samples[axis],
        })

    row_count = len(rows)
    complete_count = len(complete_rows)
    source_required_total = sum(row.get("required_source_acquisition_row_count", 0) or 0 for row in axis_reports)
    source_complete_total = sum(row.get("complete_source_acquisition_row_count", 0) or 0 for row in axis_reports)
    source_remaining_total = sum(row.get("remaining_source_acquisition_row_count", 0) or 0 for row in axis_reports)
    completion_ratio = round(complete_count / row_count, 6) if row_count else 0.0
    source_acquisition_completion_ratio = (
        round(source_complete_total / source_required_total, 6) if source_required_total else 1.0 if row_count else 0.0
    )
    status = "READY_WORKLIST_FILLED_FOR_SHARD_DRY_RUN" if row_count and not blocked_rows else "BLOCK_WORKLIST_FILL_PROGRESS"

    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "worklist_path": str(WORKLIST),
        "row_count": row_count,
        "complete_row_count": complete_count,
        "blocked_row_count": len(blocked_rows),
        "completion_ratio": completion_ratio,
        "source_acquisition_required_row_count": source_required_total,
        "source_acquisition_complete_row_count": source_complete_total,
        "source_acquisition_remaining_row_count": source_remaining_total,
        "source_acquisition_completion_ratio": source_acquisition_completion_ratio,
        "axis_reports": axis_reports,
        "blocked_rows_sample": blocked_rows[:20],
        "single_next_action": "Apply reviewed source exports to fill replacement fields before shard dry-run." if blocked_rows or not row_count else "Run the worklist-to-response-shards dry-run.",
        "non_goals": [
            "does_not_write_response_shards",
            "does_not_import_canonical_membership_rows",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    return "\n".join([
        "# KIS Axis-Wide Membership Worklist Fill Progress",
        "",
        f"- Status: `{report['status']}`",
        f"- Complete rows: `{report['complete_row_count']}`",
        f"- Blocked rows: `{report['blocked_row_count']}`",
        f"- Completion ratio: `{report['completion_ratio']}`",
        f"- Source acquisition remaining rows: `{report.get('source_acquisition_remaining_row_count', 0)}`",
        f"- Single next action: {report['single_next_action']}",
    ]) + "\n"


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "complete_row_count": report["complete_row_count"],
        "blocked_row_count": report["blocked_row_count"],
        "completion_ratio": report["completion_ratio"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
