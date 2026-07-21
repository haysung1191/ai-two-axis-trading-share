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
REPORT_JSON = ROOT / "reports/operations/kis_axis_wide_membership_import_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_axis_wide_membership_import_latest.md"
VALIDATOR_JSON = ROOT / "reports/operations/kis_axis_wide_membership_response_validator_latest.json"
PACKAGE_JSON = ROOT / "reports/operations/kis_axis_wide_membership_handoff_package_latest.json"
APPLY_CONFIRMATION = "APPLY KIS AXIS WIDE MEMBERSHIP IMPORT REVIEWED NO_TRADING"
SAFETY = intake_contract.SAFETY
MEMBERSHIP_CANONICAL_HEADERS = [
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
        writer = csv.DictWriter(f, fieldnames=MEMBERSHIP_CANONICAL_HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{col: row.get(col, "") for col in MEMBERSHIP_CANONICAL_HEADERS} for row in rows])


def _target_by_request(package: dict) -> dict[str, str]:
    return {
        row.get("request_id", ""): row.get("canonical_target_file", "")
        for row in package.get("request_rows", [])
        if row.get("request_id") and row.get("canonical_target_file")
    }


def _canonical_row(row: dict[str, str]) -> dict[str, str]:
    return {col: row.get(col, "") for col in MEMBERSHIP_CANONICAL_HEADERS}


def _row_key(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(row.get(col, "") for col in MEMBERSHIP_CANONICAL_HEADERS)


def build_report(
    generated_at: str | None = None,
    validator: dict | None = None,
    package: dict | None = None,
    apply: bool = False,
    confirmation: str = "",
    replace_caveated_axis: bool = False,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    validator = validator or _read_json(VALIDATOR_JSON)
    package = package or _read_json(PACKAGE_JSON)
    blockers: list[str] = []

    if validator.get("status") != "READY_AXIS_WIDE_MEMBERSHIP_IMPORT_REVIEW":
        blockers.append("axis_wide_response_validator_not_ready")
    blockers.extend(validator.get("blockers", []))
    if apply and confirmation != APPLY_CONFIRMATION:
        blockers.append("apply_confirmation_phrase_missing")

    target_map = _target_by_request(package)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for valid in validator.get("valid_rows", []):
        row = _canonical_row(valid.get("row", {}))
        target = target_map.get(valid.get("request_id", ""))
        if not target:
            blockers.append("canonical_target_file_missing_for_request")
            continue
        grouped[target].append(row)

    append_plan = []
    for target, rows in sorted(grouped.items()):
        path = Path(target)
        existing = _read_csv(path)
        axis_set = {row.get("axis", "") for row in rows}
        caveated = [
            row for row in existing
            if row.get("axis", "") in axis_set and row.get("evidence_quality") == "current_snapshot_caveated"
        ]
        if replace_caveated_axis and len(rows) < len(caveated):
            blockers.append(f"replacement_rows_less_than_caveated_rows:{target}")
        existing_keys = {_row_key(_canonical_row(row)) for row in existing}
        append_rows = [row for row in rows if _row_key(row) not in existing_keys]
        append_plan.append({
            "target_file": target,
            "row_count": len(rows),
            "existing_row_count": len(existing),
            "append_row_count": len(append_rows),
            "appended_row_count": 0,
            "removed_caveated_row_count": 0,
        })

    mutated = False
    if blockers:
        status = "BLOCK_AXIS_WIDE_MEMBERSHIP_IMPORT"
    else:
        status = "DRY_RUN_READY_FOR_AXIS_WIDE_MEMBERSHIP_IMPORT"

    if apply and not blockers:
        for plan in append_plan:
            target = plan["target_file"]
            rows = grouped[target]
            path = Path(target)
            existing = _read_csv(path)
            axis_set = {row.get("axis", "") for row in rows}
            removed_count = 0
            if replace_caveated_axis:
                kept = []
                for row in existing:
                    if row.get("axis", "") in axis_set and row.get("evidence_quality") == "current_snapshot_caveated":
                        removed_count += 1
                    else:
                        kept.append(_canonical_row(row))
                existing = kept
            else:
                existing = [_canonical_row(row) for row in existing]
            existing_keys = {_row_key(row) for row in existing}
            append_rows = [row for row in rows if _row_key(row) not in existing_keys]
            _write_csv(path, existing + append_rows)
            plan["appended_row_count"] = len(append_rows)
            plan["removed_caveated_row_count"] = removed_count
            mutated = mutated or bool(append_rows or removed_count)
        status = (
            "APPLIED_AXIS_WIDE_MEMBERSHIP_REPLACE_CAVEATED_IMPORT_REVIEWED"
            if replace_caveated_axis
            else "APPLIED_AXIS_WIDE_MEMBERSHIP_IMPORT_REVIEWED"
        )

    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "apply_requested": apply,
        "apply_confirmation_valid": confirmation == APPLY_CONFIRMATION,
        "replace_caveated_axis": replace_caveated_axis,
        "canonical_files_mutated": mutated,
        "valid_row_count": int(validator.get("valid_row_count", len(validator.get("valid_rows", []))) or 0),
        "blocked_row_count": int(validator.get("blocked_row_count", 0) or 0),
        "append_plan": append_plan,
        "blockers": sorted(set(blockers)),
        "required_confirmation_phrase": APPLY_CONFIRMATION,
        "single_next_action": "Validate axis-wide response shards before import." if blockers else "Review import dry-run, then apply with the exact no-trading confirmation phrase.",
        "non_goals": [
            "does_not_enable_paper_live_broker_submit_or_order_intent",
            "does_not_submit_orders",
        ],
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    return "\n".join([
        "# KIS Axis-Wide Membership Import",
        "",
        f"- Status: `{report['status']}`",
        f"- Valid rows: `{report['valid_row_count']}`",
        f"- Blocked rows: `{report['blocked_row_count']}`",
        f"- Mutated: `{report['canonical_files_mutated']}`",
        f"- Single next action: {report['single_next_action']}",
    ]) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--replace-caveated-axis", action="store_true")
    parser.add_argument("--i-understand-axis-wide-membership-import", default="")
    args = parser.parse_args()
    report = build_report(
        apply=args.apply,
        confirmation=args.i_understand_axis_wide_membership_import,
        replace_caveated_axis=args.replace_caveated_axis,
    )
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "valid_row_count": report["valid_row_count"],
        "blocked_row_count": report["blocked_row_count"],
        "canonical_files_mutated": report["canonical_files_mutated"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
