from __future__ import annotations

import argparse
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
PREFLIGHT_JSON = ROOT / "reports/operations/kis_pit_intake_import_preflight_latest.json"
PROVENANCE_JSON = ROOT / "reports/operations/kis_pit_intake_source_provenance_verifier_latest.json"
REPORT_JSON = ROOT / "reports/operations/kis_pit_intake_canonical_import_apply_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_pit_intake_canonical_import_apply_latest.md"
APPLY_CONFIRMATION = "APPLY KIS PIT INTAKE CANONICAL IMPORT REVIEWED NO_TRADING"
SAFETY = intake_contract.SAFETY
MEMBERSHIP_HEADERS = ["symbol", "asset_type", "axis", "active_from", "active_to", "listed_date", "delisted_date", "source", "snapshot_id", "evidence_quality", "notes"]


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MEMBERSHIP_HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{col: row.get(col, "") for col in MEMBERSHIP_HEADERS} for row in rows])


def _key(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(row.get(col, "") for col in MEMBERSHIP_HEADERS)


def build_report(generated_at: str | None = None, preflight: dict | None = None, provenance: dict | None = None, apply: bool = False, confirmation: str | None = None) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    preflight = preflight or _read_json(PREFLIGHT_JSON)
    provenance = provenance or _read_json(PROVENANCE_JSON)
    blockers = []
    if preflight.get("status") != "READY_FOR_MANUAL_CANONICAL_IMPORT_REVIEW":
        blockers.append("intake_preflight_not_ready")
    if provenance.get("status") != "PASS_INTAKE_SOURCE_PROVENANCE_VERIFIED":
        blockers.append("source_provenance_not_verified")
        blockers.extend(provenance.get("blockers", []))
    if apply and confirmation != APPLY_CONFIRMATION:
        blockers.append("apply_confirmation_phrase_missing")
    grouped: dict[str, list[dict[str, str]]] = {}
    for ready in preflight.get("ready_rows", []):
        if ready.get("kind") != "membership":
            continue
        target = ready.get("target_file") or ready.get("row", {}).get("target_file")
        if not target:
            target = str(ROOT / f"data_snapshots/kis_pit_membership/{ready.get('axis', 'kis_us_stocks')}_membership_intervals.csv")
        grouped.setdefault(target, []).append(ready.get("row", {}))
    append_plan = []
    mutated = False
    for target, rows in grouped.items():
        existing = _read_csv(Path(target))
        existing_keys = {_key(row) for row in existing}
        append_rows = [row for row in rows if _key(row) not in existing_keys]
        append_plan.append({"target_file": target, "row_count": len(rows), "append_row_count": len(append_rows), "appended_row_count": 0})
        if apply and not blockers:
            _write_csv(Path(target), existing + append_rows)
            append_plan[-1]["appended_row_count"] = len(append_rows)
            mutated = mutated or bool(append_rows)
    if blockers:
        status = "BLOCK_CANONICAL_IMPORT_APPLY"
    elif apply:
        status = "APPLIED_CANONICAL_IMPORT_REVIEWED"
    else:
        status = "DRY_RUN_READY_FOR_CANONICAL_IMPORT"
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "canonical_files_mutated": mutated,
        "append_plan": append_plan,
        "blockers": sorted(set(blockers)),
        "required_confirmation_phrase": APPLY_CONFIRMATION,
        "safety": SAFETY,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--i-understand-canonical-import", default=None)
    args = parser.parse_args()
    report = build_report(apply=args.apply, confirmation=args.i_understand_canonical_import)
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(f"# KIS PIT Intake Canonical Import Apply\n\n- Status: `{report['status']}`\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "canonical_files_mutated": report["canonical_files_mutated"], "latest_json": str(REPORT_JSON), "safety": SAFETY}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
