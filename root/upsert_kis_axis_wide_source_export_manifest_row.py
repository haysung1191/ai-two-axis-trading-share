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
EXPORT_DIR = ROOT / "data_snapshots/kis_pit_membership/axis_wide_source_exports"
MANIFEST = EXPORT_DIR / "axis_wide_source_export_manifest.csv"
REPORT_JSON = ROOT / "reports/operations/kis_axis_wide_source_export_manifest_row_upsert_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_axis_wide_source_export_manifest_row_upsert_latest.md"
SAFETY = intake_contract.SAFETY


def read_manifest(path: Path = MANIFEST) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=intake_contract.MANIFEST_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_manifest_row(**kwargs) -> dict[str, str]:
    return {col: str(kwargs.get(col, "")) for col in intake_contract.MANIFEST_COLUMNS}


def resolve_export_relative_path(value: str) -> tuple[str, Path, list[str]]:
    path = Path(value)
    if path.is_absolute():
        resolved = path.resolve()
        try:
            rel = str(resolved.relative_to(EXPORT_DIR.resolve()))
        except ValueError:
            return value, resolved, ["local_file_outside_export_dir"]
    else:
        rel = value
        resolved = (EXPORT_DIR / value).resolve()
    return rel, resolved, []


def _row_ready(row: dict[str, str]) -> tuple[bool, list[str]]:
    blockers = []
    rel, path, path_blockers = resolve_export_relative_path(row.get("local_file", ""))
    blockers.extend(path_blockers)
    if not path.exists():
        blockers.append("local_file_missing_on_disk")
    else:
        validation = intake_contract.validate_normalized_rows(
            path,
            row.get("snapshot_id", ""),
            row.get("evidence_quality", ""),
            [axis for axis in row.get("covered_axes", "").split("|") if axis],
        )
        if validation["invalid_row_count"]:
            blockers.append("normalized_export_rows_not_ready")
    if not row.get("export_id") or row.get("export_id", "").startswith("EXAMPLE_"):
        blockers.append("export_id_missing_or_example")
    return not blockers, sorted(set(blockers))


def build_report(
    generated_at: str,
    *,
    row: dict[str, str],
    write: bool,
    replace_example: bool,
    path_blockers: list[str],
    manifest_path: Path = MANIFEST,
) -> dict:
    ready, blockers = _row_ready(row)
    blockers = sorted(set(blockers + path_blockers))
    rows = read_manifest(manifest_path)
    merge_action = "appended_row"
    if replace_example and rows and rows[0].get("export_id", "").startswith("EXAMPLE_"):
        new_rows = [row, *rows[1:]]
        merge_action = "replaced_example_row"
    else:
        new_rows = [r for r in rows if r.get("export_id") != row.get("export_id")] + [row]
    mutated = False
    if ready and write:
        _write_manifest(manifest_path, new_rows)
        mutated = True
    status = "BLOCK_SOURCE_EXPORT_MANIFEST_ROW_UPSERT" if blockers else ("WROTE_SOURCE_EXPORT_MANIFEST_ROW" if write else "DRY_RUN_READY_TO_WRITE_SOURCE_EXPORT_MANIFEST_ROW")
    report = {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "merge_action": merge_action,
        "manifest_mutated": mutated,
        "blockers": blockers,
        "row": row,
        "safety": SAFETY,
    }
    return report


def build_status_report(generated_at: str, *, manifest_path: Path = MANIFEST) -> dict:
    rows = read_manifest(manifest_path)
    valid = 0
    blockers = []
    for row in rows:
        ready, row_blockers = _row_ready(row)
        if ready:
            valid += 1
        blockers.extend(row_blockers)
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": "READY_MANIFEST_HAS_VALID_SOURCE_EXPORT_ROWS" if valid else "BLOCK_SOURCE_EXPORT_MANIFEST_ROW_UPSERT",
        "status_only": True,
        "manifest_mutated": False,
        "merge_action": "status_only_current_manifest_audit",
        "valid_manifest_row_count": valid,
        "blocked_manifest_row_count": len(rows) - valid,
        "blockers": sorted(set(blockers)),
        "safety": SAFETY,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-id")
    parser.add_argument("--source-family")
    parser.add_argument("--source-name")
    parser.add_argument("--source-url", default="")
    parser.add_argument("--local-file")
    parser.add_argument("--snapshot-id")
    parser.add_argument("--license-scope")
    parser.add_argument("--evidence-quality")
    parser.add_argument("--covered-axes")
    parser.add_argument("--notes", default="")
    parser.add_argument("--replace-example", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    generated_at = datetime.now(tz=KST).isoformat(timespec="seconds")
    if args.export_id:
        row = build_manifest_row(
            export_id=args.export_id,
            source_family=args.source_family,
            source_name=args.source_name,
            source_url=args.source_url,
            local_file=args.local_file,
            snapshot_id=args.snapshot_id,
            license_scope=args.license_scope,
            evidence_quality=args.evidence_quality,
            covered_axes=args.covered_axes,
            notes=args.notes,
        )
        report = build_report(generated_at, row=row, write=args.write, replace_example=args.replace_example, path_blockers=[])
    else:
        report = build_status_report(generated_at)
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(f"# KIS Source Export Manifest Upsert\n\n- Status: `{report['status']}`\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not report.get("blockers") else 1


if __name__ == "__main__":
    raise SystemExit(main())
