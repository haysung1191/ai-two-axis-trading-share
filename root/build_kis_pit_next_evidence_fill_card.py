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
WORK_ORDER_JSON = ROOT / "reports/operations/kis_pit_intake_work_order_latest.json"
REPORT_JSON = ROOT / "reports/operations/kis_pit_next_evidence_fill_card_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_pit_next_evidence_fill_card_latest.md"
SAFETY = intake_contract.SAFETY


def _generated_at_utc(generated_at: str) -> str:
    parsed = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(ZoneInfo("UTC")).isoformat()


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _editable_file(task: dict) -> str:
    if task.get("evidence_type") == "membership_interval":
        return r"C:\AI\data_snapshots\kis_pit_membership\intake\cand022_authoritative_membership_rows_template.csv"
    if "event" in str(task.get("evidence_type")):
        return r"C:\AI\data_snapshots\kis_pit_membership\intake\cand022_delisting_event_coverage_template.csv"
    return r"C:\AI\data_snapshots\kis_pit_membership\intake\cand022_delisting_replay_cases_template.csv"


def build_fill_card(generated_at: str | None = None, work_order: dict | None = None) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    work_order = work_order or _read_json(WORK_ORDER_JSON)
    task = next(
        (
            row for row in work_order.get("tasks", [])
            if row.get("lane") == "minimal_cand022_unblock" and row.get("blockers")
        ),
        None,
    )
    if not task:
        axis_target = work_order.get("axis_wide_next_target") or next(
            (
                row for row in work_order.get("tasks", [])
                if row.get("lane") == "axis_wide_operation_ready" and row.get("blockers")
            ),
            None,
        )
        if axis_target:
            return {
                "schema_version": "1.0.0",
                "generated_at": generated_at,
                "generated_at_utc": _generated_at_utc(generated_at),
                "status": "BLOCK_AXIS_WIDE_EVIDENCE_ACQUISITION_REQUIRED",
                "queue_id": axis_target.get("queue_id"),
                "symbol": axis_target.get("symbol"),
                "axis": axis_target.get("axis"),
                "evidence_type": axis_target.get("evidence_type"),
                "rebalance_date_to_cover": axis_target.get("rebalance_date_to_cover"),
                "editable_intake_file": "",
                "missing_fields": axis_target.get("missing_fields", []),
                "accepted_evidence_quality": axis_target.get("accepted_evidence_quality", ""),
                "pit_missing_membership_rows": axis_target.get("pit_missing_membership_rows"),
                "pit_source_verified_membership_ready_rows": axis_target.get(
                    "pit_source_verified_membership_ready_rows"
                ),
                "pit_recommended_source_class": axis_target.get("pit_recommended_source_class"),
                "pit_priority_rank": axis_target.get("pit_priority_rank"),
                "must_not_use_source_values": ["vendor", "unknown", "manual_guess"],
                "must_not_use_snapshot_values": ["snap", "placeholder", "example"],
                "must_not_contain_markers": ["current_snapshot_caveated", "historical_replay_only"],
                "after_fill_commands": [
                    "python .\\build_kis_pit_intake_import_preflight.py",
                    "python .\\build_kis_pit_membership_verifier.py",
                    "python .\\build_kis_pit_intake_work_order.py",
                    "python .\\build_kis_pit_next_evidence_fill_card.py",
                ],
                "trading_enabled": False,
                "single_next_action": work_order.get("single_next_action")
                or "Acquire reviewed PIT membership-history source evidence for the axis-wide target.",
                "non_goals": [
                    "does_not_mutate_files",
                    "does_not_enable_paper_live_broker_submit_or_order_intent",
                ],
                "safety": SAFETY,
            }
        return {
            "schema_version": "1.0.0",
            "generated_at": generated_at,
            "generated_at_utc": _generated_at_utc(generated_at),
            "status": "READY_NO_BLOCKED_MINIMAL_TASK",
            "queue_id": None,
            "symbol": None,
            "trading_enabled": False,
            "single_next_action": "Continue axis-wide source acquisition.",
            "non_goals": ["does_not_enable_paper_live_broker_submit_or_order_intent"],
            "safety": SAFETY,
        }
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "generated_at_utc": _generated_at_utc(generated_at),
        "status": "BLOCK_NEXT_EVIDENCE_FILL_REQUIRED",
        "queue_id": task.get("queue_id"),
        "symbol": task.get("symbol"),
        "axis": task.get("axis"),
        "evidence_type": task.get("evidence_type"),
        "rebalance_date_to_cover": task.get("rebalance_date_to_cover"),
        "editable_intake_file": _editable_file(task),
        "missing_fields": task.get("missing_fields", []),
        "accepted_evidence_quality": task.get("accepted_evidence_quality", ""),
        "must_not_use_source_values": ["vendor", "unknown", "manual_guess"],
        "must_not_use_snapshot_values": ["snap", "placeholder", "example"],
        "must_not_contain_markers": ["current_snapshot_caveated", "historical_replay_only"],
        "after_fill_commands": [
            "python .\\build_kis_pit_intake_import_preflight.py",
            "python .\\build_kis_pit_intake_work_order.py",
            "python .\\build_kis_pit_next_evidence_fill_card.py",
        ],
        "trading_enabled": False,
        "single_next_action": "Fill the editable intake row with reviewed source-backed evidence.",
        "non_goals": [
            "does_not_mutate_files",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    return "\n".join([
        "# KIS PIT Next Evidence Fill Card",
        "",
        f"- Status: `{report['status']}`",
        f"- Queue ID: `{report.get('queue_id')}`",
        f"- Editable file: `{report.get('editable_intake_file', '')}`",
    ]) + "\n"


def main() -> int:
    report = build_fill_card()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "queue_id": report.get("queue_id"),
        "symbol": report.get("symbol"),
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
