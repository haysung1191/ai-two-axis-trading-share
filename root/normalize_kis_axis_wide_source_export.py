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
SAFETY = intake_contract.SAFETY


def resolve_export_path(value: str) -> tuple[Path, list[str]]:
    path = Path(value)
    if not path.is_absolute():
        path = EXPORT_DIR / path
    path = path.resolve()
    try:
        path.relative_to(EXPORT_DIR.resolve())
    except ValueError:
        return path, ["path_outside_axis_wide_source_exports"]
    return path, []


def _read_raw(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), list(reader.fieldnames or [])


def build_report(
    generated_at: str,
    *,
    raw_file: Path,
    output_file: Path,
    write: bool,
    column_map: dict[str, str],
    defaults: dict[str, str],
    assignment_blockers: list[str],
) -> dict:
    blockers = list(assignment_blockers)
    rows, headers = _read_raw(raw_file)
    missing = sorted({source for source in column_map.values() if source not in headers})
    if missing:
        blockers.append("mapped_raw_columns_missing")
    normalized = []
    if not blockers:
        for row in rows:
            out = {col: defaults.get(col, "") for col in intake_contract.NORMALIZED_COLUMNS}
            for dest, source in column_map.items():
                out[dest] = row.get(source, "")
            normalized.append(out)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = output_file.with_suffix(output_file.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=intake_contract.NORMALIZED_COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(normalized)
        validation = intake_contract.validate_normalized_rows(
            tmp,
            defaults.get("snapshot_id", ""),
            defaults.get("evidence_quality", ""),
            [defaults.get("axis", "")],
        )
        tmp.unlink(missing_ok=True)
        if validation["invalid_row_count"]:
            blockers.append("normalized_projection_not_operation_ready")
    else:
        validation = {}
    files_mutated = False
    if not blockers and write:
        with output_file.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=intake_contract.NORMALIZED_COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(normalized)
        files_mutated = True
    status = "BLOCK_SOURCE_EXPORT_NORMALIZATION" if blockers else ("WROTE_NORMALIZED_SOURCE_EXPORT" if write else "DRY_RUN_READY_TO_WRITE_NORMALIZED_SOURCE_EXPORT")
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "raw_file": str(raw_file),
        "output_file": str(output_file),
        "files_mutated": files_mutated,
        "normalized_row_count": len(normalized),
        "projected_validation": validation,
        "blockers": sorted(set(blockers)),
        "safety": SAFETY,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--map", action="append", default=[])
    parser.add_argument("--axis", required=True)
    parser.add_argument("--asset-type", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--evidence-quality", required=True)
    parser.add_argument("--license-scope", required=True)
    parser.add_argument("--exchange", default="")
    args = parser.parse_args()
    raw, raw_blockers = resolve_export_path(args.raw_file)
    out, out_blockers = resolve_export_path(args.output_file)
    column_map = dict(item.split("=", 1) for item in args.map)
    defaults = {
        "axis": args.axis,
        "asset_type": args.asset_type,
        "source": args.source,
        "snapshot_id": args.snapshot_id,
        "evidence_quality": args.evidence_quality,
        "source_artifact_path": str(raw),
        "license_scope": args.license_scope,
        "exchange": args.exchange,
    }
    report = build_report(
        datetime.now(tz=KST).isoformat(timespec="seconds"),
        raw_file=raw,
        output_file=out,
        write=args.write,
        column_map=column_map,
        defaults=defaults,
        assignment_blockers=raw_blockers + out_blockers,
    )
    print(json.dumps(report, indent=2))
    return 0 if not report["blockers"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
