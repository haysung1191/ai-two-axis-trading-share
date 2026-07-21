from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_kis_axis_wide_source_export_intake_contract as intake_contract


KST = ZoneInfo("Asia/Seoul")
WORKLIST = ROOT / "data_snapshots/kis_pit_membership/axis_wide_handoff/replacement_worklists/kis_axis_wide_membership_replacement_worklist_latest.csv"
REPORT_JSON = ROOT / "reports/operations/kis_axis_wide_membership_worklist_to_shards_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_axis_wide_membership_worklist_to_shards_latest.md"
APPLY_CONFIRMATION = "APPLY KIS AXIS WIDE WORKLIST TO SHARDS REVIEWED NO_TRADING"
SAFETY = intake_contract.SAFETY
REQUIRED_FIELDS = [
    "replacement_symbol",
    "replacement_asset_type",
    "replacement_active_from",
    "replacement_source",
    "replacement_snapshot_id",
    "replacement_evidence_quality",
]
RESPONSE_HEADERS = [
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


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESPONSE_HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _row_blockers(row: dict[str, str]) -> list[str]:
    if any(not row.get(field, "").strip() for field in REQUIRED_FIELDS):
        return ["replacement_required_fields_missing"]
    if row.get("replacement_evidence_quality") not in intake_contract.ACCEPTED_EVIDENCE:
        return ["replacement_evidence_quality_not_operation_ready"]
    if not row.get("target_response_shard", "").strip():
        return ["target_response_shard_missing"]
    return []


def _response_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "request_id": row.get("request_id", ""),
        "axis": row.get("axis", ""),
        "symbol": row.get("replacement_symbol", ""),
        "asset_type": row.get("replacement_asset_type", ""),
        "active_from": row.get("replacement_active_from", ""),
        "active_to": row.get("replacement_active_to", ""),
        "listed_date": row.get("replacement_listed_date", ""),
        "delisted_date": row.get("replacement_delisted_date", ""),
        "source": row.get("replacement_source", ""),
        "snapshot_id": row.get("replacement_snapshot_id", ""),
        "evidence_quality": row.get("replacement_evidence_quality", ""),
        "notes": row.get("replacement_notes", ""),
    }


def build_report(
    generated_at: str | None = None,
    worklist_rows: list[dict[str, str]] | None = None,
    apply: bool = False,
    confirmation: str = "",
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    worklist_rows = worklist_rows if worklist_rows is not None else _read_csv(WORKLIST)
    valid_rows = []
    blocked_rows = []
    shard_rows: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row_number, row in enumerate(worklist_rows, start=2):
        blockers = _row_blockers(row)
        if blockers:
            blocked_rows.append({
                "row_number": row_number,
                "axis": row.get("axis", ""),
                "symbol": row.get("symbol", ""),
                "blockers": blockers,
            })
            continue
        response = _response_row(row)
        valid_rows.append(response)
        shard_rows[row["target_response_shard"]].append(response)

    blockers = []
    if blocked_rows:
        blockers.append("blocked_worklist_rows_present")
    if apply and confirmation != APPLY_CONFIRMATION:
        blockers.append("apply_confirmation_phrase_missing")

    mutated = False
    write_results = []
    if blockers:
        status = "BLOCK_WORKLIST_TO_RESPONSE_SHARDS"
    else:
        status = "DRY_RUN_READY_TO_APPLY_WORKLIST_ROWS_TO_RESPONSE_SHARDS"

    if apply and not blockers:
        for target, rows in sorted(shard_rows.items()):
            path = Path(target)
            _write_csv(path, rows)
            write_results.append({"path": str(path), "row_count": len(rows)})
        mutated = True
        status = "APPLIED_WORKLIST_ROWS_TO_RESPONSE_SHARDS_REVIEWED"

    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "apply_requested": apply,
        "apply_confirmation_valid": confirmation == APPLY_CONFIRMATION,
        "response_shards_mutated": mutated,
        "worklist_row_count": len(worklist_rows),
        "valid_worklist_row_count": len(valid_rows),
        "blocked_worklist_row_count": len(blocked_rows),
        "target_shard_count": len(shard_rows),
        "write_results": write_results,
        "blockers": sorted(set(blockers)),
        "blocked_rows_sample": blocked_rows[:20],
        "required_confirmation_phrase": APPLY_CONFIRMATION,
        "single_next_action": "Fill all replacement worklist rows before writing response shards." if blockers else "Review shard dry-run output, then apply with the exact no-trading confirmation phrase.",
        "non_goals": [
            "does_not_import_canonical_membership_rows",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    return "\n".join([
        "# KIS Axis-Wide Membership Worklist To Shards",
        "",
        f"- Status: `{report['status']}`",
        f"- Valid rows: `{report['valid_worklist_row_count']}`",
        f"- Blocked rows: `{report['blocked_worklist_row_count']}`",
        f"- Mutated: `{report['response_shards_mutated']}`",
        f"- Single next action: {report['single_next_action']}",
    ]) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--i-understand-worklist-to-shards", default="")
    args = parser.parse_args()
    report = build_report(apply=args.apply, confirmation=args.i_understand_worklist_to_shards)
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "valid_worklist_row_count": report["valid_worklist_row_count"],
        "blocked_worklist_row_count": report["blocked_worklist_row_count"],
        "response_shards_mutated": report["response_shards_mutated"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
