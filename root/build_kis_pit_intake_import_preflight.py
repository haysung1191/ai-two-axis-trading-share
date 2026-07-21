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
INTAKE_DIR = ROOT / "data_snapshots/kis_pit_membership/intake"
REPORT_JSON = ROOT / "reports/operations/kis_pit_intake_import_preflight_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_pit_intake_import_preflight_latest.md"
SAFETY = intake_contract.SAFETY

MEMBERSHIP_HEADERS = [
    "symbol",
    "axis",
    "rebalance_date_to_cover",
    "active_from",
    "active_to",
    "listed_date",
    "delisted_date",
    "source",
    "snapshot_id",
    "evidence_quality",
    "notes",
]
EVENT_HEADERS = [
    "symbol",
    "axis",
    "coverage_start",
    "coverage_end",
    "coverage_status",
    "source",
    "snapshot_id",
    "evidence_quality",
    "notes",
]
REPLAY_HEADERS = [
    "scenario",
    "case_id",
    "symbol",
    "axis",
    "event_type",
    "event_date",
    "expected_blocked",
    "source",
    "snapshot_id",
    "evidence_quality",
    "notes",
]
READY_EVIDENCE = {"authoritative", "exchange_official", "licensed_vendor", "replay_test_authoritative"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _row_check(row: dict[str, str], required: list[str], kind: str, row_number: int) -> tuple[dict | None, dict | None]:
    missing = [field for field in required if not row.get(field, "").strip()]
    blockers = []
    if missing:
        blockers.append("required_fields_missing")
    if row.get("evidence_quality") not in READY_EVIDENCE:
        blockers.append("evidence_quality_not_operation_ready")
    payload = {
        "row_number": row_number,
        "kind": kind,
        "symbol": row.get("symbol", ""),
        "axis": row.get("axis", ""),
        "row": row,
    }
    if blockers:
        blocked = dict(payload)
        blocked["missing_fields"] = missing
        blocked["blockers"] = blockers
        return None, blocked
    ready = dict(payload)
    ready["action"] = "append_after_manual_review"
    return ready, None


def build_preflight(generated_at: str | None = None, intake_dir: Path = INTAKE_DIR) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    specs = [
        ("membership", intake_dir / "cand022_authoritative_membership_rows_template.csv", MEMBERSHIP_HEADERS, ["symbol", "axis", "active_from", "source", "snapshot_id", "evidence_quality"]),
        ("event_or_no_event", intake_dir / "cand022_delisting_event_coverage_template.csv", EVENT_HEADERS, ["symbol", "axis", "coverage_status", "source", "snapshot_id", "evidence_quality"]),
        ("replay", intake_dir / "cand022_delisting_replay_cases_template.csv", REPLAY_HEADERS, ["scenario", "case_id", "symbol", "event_date", "source", "snapshot_id", "evidence_quality"]),
    ]
    ready_rows = []
    blocked_rows = []
    for kind, path, _headers, required in specs:
        for row_number, row in enumerate(_read_csv(path), start=2):
            ready, blocked = _row_check(row, required, kind, row_number)
            if ready:
                ready_rows.append(ready)
            if blocked:
                blocked_rows.append(blocked)
    blockers = sorted({b for row in blocked_rows for b in row.get("blockers", [])})
    status = "READY_FOR_MANUAL_CANONICAL_IMPORT_REVIEW" if ready_rows and not blocked_rows else "BLOCK_INTAKE_IMPORT_PREFLIGHT"
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "canonical_files_mutated": False,
        "ready_row_count": len(ready_rows),
        "blocked_row_count": len(blocked_rows),
        "ready_rows": ready_rows,
        "blocked_rows": blocked_rows,
        "copy_plan": [{"kind": row["kind"], "row_number": row["row_number"], "action": "append_after_manual_review"} for row in ready_rows],
        "blockers": blockers,
        "single_next_action": "Fill blocked intake rows with reviewed operation-ready source evidence." if blocked_rows else "Manual review ready rows before canonical import.",
        "non_goals": [
            "does_not_mutate_canonical_files",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    return "\n".join([
        "# KIS PIT Intake Import Preflight",
        "",
        f"- Status: `{report['status']}`",
        f"- Ready rows: `{report['ready_row_count']}`",
        f"- Blocked rows: `{report['blocked_row_count']}`",
    ]) + "\n"


def main() -> int:
    report = build_preflight()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "ready_row_count": report["ready_row_count"],
        "blocked_row_count": report["blocked_row_count"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
