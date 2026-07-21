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
QUEUE_JSON = ROOT / "reports/operations/kis_pit_source_acquisition_queue_latest.json"
PREFLIGHT_JSON = ROOT / "reports/operations/kis_pit_intake_import_preflight_latest.json"
PIT_VERIFIER_JSON = ROOT / "reports/operations/kis_pit_membership_verifier_latest.json"
REPORT_JSON = ROOT / "reports/operations/kis_pit_intake_work_order_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_pit_intake_work_order_latest.md"
SAFETY = intake_contract.SAFETY


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _blocked_for_item(item: dict, blocked_rows: list[dict]) -> list[dict]:
    kind_map = {
        "membership_interval": "membership",
        "event_or_no_event_coverage": "event_or_no_event",
        "delisting_replay_case": "replay",
        "delisting_replay_policy": "replay",
    }
    expected = kind_map.get(item.get("evidence_type"))
    rows = []
    for row in blocked_rows:
        if expected and row.get("kind") != expected:
            continue
        if item.get("symbol") and row.get("symbol") and item.get("symbol") != row.get("symbol"):
            continue
        if item.get("axis") and row.get("axis") and item.get("axis") != row.get("axis"):
            continue
        rows.append(row)
    return rows


def build_work_order(
    generated_at: str | None = None,
    queue_report: dict | None = None,
    preflight: dict | None = None,
    pit_verifier: dict | None = None,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    queue_report = queue_report or _read_json(QUEUE_JSON)
    preflight = preflight or _read_json(PREFLIGHT_JSON)
    pit_verifier = pit_verifier or _read_json(PIT_VERIFIER_JSON)
    blocked_rows = preflight.get("blocked_rows", [])
    pit_targets = pit_verifier.get("next_evidence_acquisition_targets", [])
    pit_target_by_axis = {
        row.get("axis"): row
        for row in pit_targets
        if isinstance(row, dict) and row.get("axis")
    }
    pit_single_next_action = pit_verifier.get("single_next_action")
    tasks = []
    for item in queue_report.get("queue", []):
        rows = _blocked_for_item(item, blocked_rows)
        blockers = sorted({b for row in rows for b in row.get("blockers", [])})
        missing = sorted({m for row in rows for m in row.get("missing_fields", [])})
        pit_target = pit_target_by_axis.get(item.get("axis")) or {}
        pit_missing_rows = int(pit_target.get("missing_membership_rows") or 0)
        if item.get("lane") == "axis_wide_operation_ready" and pit_missing_rows > 0:
            blockers = sorted(set(blockers + ["axis_wide_pit_membership_history_missing"]))
        tasks.append({
            "queue_id": item.get("queue_id"),
            "lane": item.get("lane"),
            "evidence_type": item.get("evidence_type"),
            "symbol": item.get("symbol", ""),
            "axis": item.get("axis", ""),
            "rebalance_date_to_cover": item.get("rebalance_date_to_cover", ""),
            "target_file": item.get("target_file", ""),
            "accepted_evidence_quality": item.get("required_source_quality", ""),
            "intake_row_numbers": [row.get("row_number") for row in rows],
            "missing_fields": missing,
            "blockers": blockers,
            "pit_missing_membership_rows": pit_missing_rows,
            "pit_source_verified_membership_ready_rows": pit_target.get("source_verified_membership_ready_rows"),
            "pit_ready_coverage_of_remaining": pit_target.get("ready_coverage_of_remaining"),
            "pit_recommended_source_class": pit_target.get("recommended_source_class"),
            "pit_priority_rank": pit_target.get("rank"),
        })
    minimal = [task for task in tasks if task.get("lane") == "minimal_cand022_unblock"]
    blocked = [task for task in minimal if task.get("blockers")]
    axis_wide = [task for task in tasks if task.get("lane") == "axis_wide_operation_ready"]
    axis_wide_blocked = [task for task in axis_wide if task.get("blockers")]
    if blocked:
        status = "BLOCK_INTAKE_WORK_ORDER_OPEN"
    elif axis_wide_blocked:
        status = "BLOCK_AXIS_WIDE_SOURCE_ACQUISITION_REQUIRED"
    else:
        status = "READY_FOR_PREFLIGHT_RECHECK"
    first_axis_target = sorted(
        axis_wide_blocked,
        key=lambda row: int(row.get("pit_priority_rank") or 999999),
    )
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "minimal_cand022_task_count": len(minimal),
        "minimal_cand022_ready_task_count": len(minimal) - len(blocked),
        "minimal_cand022_blocked_task_count": len(blocked),
        "axis_wide_task_count": len(axis_wide),
        "axis_wide_blocked_task_count": len(axis_wide_blocked),
        "axis_wide_next_target": first_axis_target[0] if first_axis_target else None,
        "pit_next_evidence_acquisition_targets": pit_targets,
        "tasks": tasks,
        "single_next_action": (
            "Fill the first blocked minimal intake task."
            if blocked
            else (
                pit_single_next_action
                if axis_wide_blocked and pit_single_next_action
                else "Rerun intake preflight or continue axis-wide source acquisition."
            )
        ),
        "non_goals": [
            "does_not_mutate_intake_or_canonical_files",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    return "\n".join([
        "# KIS PIT Intake Work Order",
        "",
        f"- Status: `{report['status']}`",
        f"- Minimal tasks: `{report['minimal_cand022_task_count']}`",
        f"- Blocked: `{report['minimal_cand022_blocked_task_count']}`",
        f"- Axis-wide tasks: `{report.get('axis_wide_task_count', 0)}`",
        f"- Axis-wide blocked: `{report.get('axis_wide_blocked_task_count', 0)}`",
        f"- Axis-wide next target: `{(report.get('axis_wide_next_target') or {}).get('axis') or '-'}`",
    ]) + "\n"


def main() -> int:
    report = build_work_order()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "minimal_cand022_task_count": report["minimal_cand022_task_count"],
        "minimal_cand022_blocked_task_count": report["minimal_cand022_blocked_task_count"],
        "axis_wide_blocked_task_count": report["axis_wide_blocked_task_count"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
