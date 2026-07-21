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
WORKLIST_DIR = ROOT / "data_snapshots/kis_pit_membership/axis_wide_handoff/replacement_worklists"
COMBINED_WORKLIST = WORKLIST_DIR / "kis_axis_wide_membership_replacement_worklist_latest.csv"
REPORT_JSON = ROOT / "reports/operations/kis_axis_wide_source_exports_to_replacement_worklist_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_axis_wide_source_exports_to_replacement_worklist_latest.md"
APPLY_CONFIRMATION = "APPLY KIS AXIS WIDE SOURCE EXPORTS TO WORKLIST REVIEWED NO_TRADING"
SAFETY = intake_contract.SAFETY


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _valid_export_paths(contract_report: dict) -> list[Path]:
    paths = []
    for report in contract_report.get("export_reports", []):
        if not report.get("valid_for_operation_ready_intake"):
            continue
        path = report.get("file_info", {}).get("path")
        if path:
            paths.append(Path(path))
    return paths


def _index_exports(paths: list[Path]) -> tuple[dict[tuple[str, str, str], dict[str, str]], list[dict[str, str]]]:
    index: dict[tuple[str, str, str], dict[str, str]] = {}
    duplicates = []
    for path in paths:
        for row in _read_csv(path):
            key = (row.get("axis", ""), row.get("symbol", ""), row.get("asset_type", ""))
            if key in index:
                duplicates.append({"axis": key[0], "symbol": key[1], "asset_type": key[2]})
                continue
            index[key] = row
    return index, duplicates


def _apply_export_to_worklist_row(row: dict[str, str], export_row: dict[str, str]) -> dict[str, str]:
    updated = dict(row)
    mapping = {
        "replacement_symbol": "symbol",
        "replacement_asset_type": "asset_type",
        "replacement_active_from": "active_from",
        "replacement_active_to": "active_to",
        "replacement_listed_date": "listed_date",
        "replacement_delisted_date": "delisted_date",
        "replacement_source": "source",
        "replacement_snapshot_id": "snapshot_id",
        "replacement_evidence_quality": "evidence_quality",
        "replacement_notes": "notes",
    }
    for target, source in mapping.items():
        updated[target] = export_row.get(source, "")
    return updated


def _axis_worklist_path(axis: str) -> Path:
    safe_axis = axis.replace("/", "_").replace("\\", "_")
    return WORKLIST_DIR / f"{safe_axis}_replacement_worklist_latest.csv"


def build_report(
    generated_at: str | None = None,
    worklist_rows: list[dict[str, str]] | None = None,
    contract_report: dict | None = None,
    apply: bool = False,
    confirmation: str = "",
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    worklist_rows = worklist_rows if worklist_rows is not None else _read_csv(COMBINED_WORKLIST)
    contract_report = contract_report or _read_json(intake_contract.REPORT_JSON)

    blockers: list[str] = []
    if contract_report.get("status") != "READY_SOURCE_EXPORTS_FOR_REPLACEMENT_MAPPING":
        blockers.append("source_export_intake_not_ready")

    export_paths = _valid_export_paths(contract_report)
    if not export_paths:
        blockers.append("no_valid_source_export_files")

    export_index, duplicate_export_keys = _index_exports(export_paths)
    if duplicate_export_keys:
        blockers.append("duplicate_export_keys")

    matched = []
    unmatched = []
    updated_rows = []
    for row_number, row in enumerate(worklist_rows, start=2):
        key = (row.get("axis", ""), row.get("symbol", ""), row.get("asset_type", ""))
        export_row = export_index.get(key)
        if export_row:
            matched.append({"row_number": row_number, "axis": key[0], "symbol": key[1], "asset_type": key[2]})
            updated_rows.append(_apply_export_to_worklist_row(row, export_row))
        else:
            unmatched.append({"row_number": row_number, "axis": key[0], "symbol": key[1], "asset_type": key[2]})
            updated_rows.append(dict(row))

    if apply and confirmation != APPLY_CONFIRMATION:
        blockers.append("apply_confirmation_phrase_missing")

    matched_count = len(matched)
    row_count = len(worklist_rows)
    coverage_ratio = round(matched_count / row_count, 6) if row_count else 0.0
    full_coverage_ready = row_count > 0 and matched_count == row_count
    write_results = []
    mutated = False

    if blockers:
        status = "BLOCK_SOURCE_EXPORTS_TO_REPLACEMENT_WORKLIST"
    elif full_coverage_ready:
        status = "DRY_RUN_READY_TO_APPLY_FULL_SOURCE_EXPORTS_TO_WORKLIST"
    else:
        status = "DRY_RUN_READY_TO_APPLY_SOURCE_EXPORTS_TO_WORKLIST"

    if apply and not blockers:
        fieldnames = list(worklist_rows[0].keys()) if worklist_rows else []
        _write_csv(COMBINED_WORKLIST, updated_rows, fieldnames)
        write_results.append({"path": str(COMBINED_WORKLIST), "row_count": len(updated_rows)})
        for axis in sorted({row.get("axis", "") for row in updated_rows if row.get("axis")}):
            axis_rows = [row for row in updated_rows if row.get("axis") == axis]
            axis_path = _axis_worklist_path(axis)
            _write_csv(axis_path, axis_rows, fieldnames)
            write_results.append({"path": str(axis_path), "row_count": len(axis_rows)})
        mutated = True
        status = "APPLIED_FULL_SOURCE_EXPORTS_TO_REPLACEMENT_WORKLIST_REVIEWED" if full_coverage_ready else "APPLIED_SOURCE_EXPORTS_TO_REPLACEMENT_WORKLIST_REVIEWED"

    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "universe_id": "KIS_COMBINED_KRW",
        "status": status,
        "dry_run": not apply,
        "apply_requested": apply,
        "apply_confirmation_valid": confirmation == APPLY_CONFIRMATION,
        "worklist_mutated": mutated,
        "worklist_row_count": row_count,
        "source_export_file_count": len(export_paths),
        "indexed_export_key_count": len(export_index),
        "matched_worklist_row_count": matched_count,
        "unmatched_worklist_row_count": len(unmatched),
        "coverage_ratio": coverage_ratio,
        "full_coverage_ready": full_coverage_ready,
        "duplicate_export_key_count": len(duplicate_export_keys),
        "write_results": write_results,
        "blockers": sorted(set(blockers)),
        "matched_sample": matched[:20],
        "unmatched_sample": unmatched[:20],
        "duplicate_export_key_sample": duplicate_export_keys[:20],
        "required_confirmation_phrase": APPLY_CONFIRMATION,
        "single_next_action": "Provide a valid axis-wide source export intake before mapping exports into replacement worklists." if blockers else "Review the dry-run mapping coverage, then apply with the exact no-trading confirmation phrase.",
        "non_goals": [
            "does_not_write_response_shards",
            "does_not_import_canonical_membership_rows",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
        "source_files": {
            "replacement_worklist": str(COMBINED_WORKLIST),
            "source_export_intake_contract": str(intake_contract.REPORT_JSON),
        },
    }


def render_md(report: dict) -> str:
    return "\n".join([
        "# KIS Axis-Wide Source Exports To Replacement Worklist",
        "",
        f"- Status: `{report['status']}`",
        f"- Worklist rows: `{report['worklist_row_count']}`",
        f"- Matched rows: `{report['matched_worklist_row_count']}`",
        f"- Unmatched rows: `{report['unmatched_worklist_row_count']}`",
        f"- Coverage ratio: `{report['coverage_ratio']}`",
        f"- Mutated: `{report['worklist_mutated']}`",
        f"- Single next action: {report['single_next_action']}",
    ]) + "\n"


def write_report(report: dict) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--i-understand-source-exports-to-worklist", default="")
    args = parser.parse_args()
    report = build_report(
        apply=args.apply,
        confirmation=args.i_understand_source_exports_to_worklist,
    )
    write_report(report)
    print(json.dumps({
        "status": report["status"],
        "matched_worklist_row_count": report["matched_worklist_row_count"],
        "unmatched_worklist_row_count": report["unmatched_worklist_row_count"],
        "worklist_mutated": report["worklist_mutated"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
