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
EXPORT_DIR = ROOT / "data_snapshots/kis_pit_membership/axis_wide_source_exports"
RAW_DIR = EXPORT_DIR / "raw"
NORMALIZED_EXPORT_DIR = EXPORT_DIR / "exports"
MANIFEST = EXPORT_DIR / "axis_wide_source_export_manifest.csv"
NORMALIZED_TEMPLATE = EXPORT_DIR / "axis_wide_membership_export_normalized_template.csv"
REPORT_JSON = ROOT / "reports/operations/kis_axis_wide_source_export_inbox_status_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_axis_wide_source_export_inbox_status_latest.md"
SAFETY = intake_contract.SAFETY


def _headers(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f).fieldnames or [])


def _manifest_refs() -> set[str]:
    refs = set()
    if MANIFEST.exists():
        with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("local_file"):
                    refs.add(row["local_file"].replace("/", "\\"))
    return refs


def _rel(path: Path) -> str:
    return str(path.relative_to(EXPORT_DIR)).replace("/", "\\")


def build_report(generated_at: str | None = None) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    created = []
    for directory in [RAW_DIR, NORMALIZED_EXPORT_DIR]:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory))
    refs = _manifest_refs()
    files = []
    normalized = 0
    raw = 0
    for path in sorted(EXPORT_DIR.rglob("*.csv")):
        rel = _rel(path)
        headers = _headers(path)
        normalized_shape = headers == intake_contract.NORMALIZED_COLUMNS
        if path == MANIFEST or path == NORMALIZED_TEMPLATE:
            role = "contract_file"
        elif rel in refs:
            role = "manifest_referenced_export"
        elif normalized_shape:
            role = "unreferenced_normalized_export"
            normalized += 1
        else:
            role = "unreferenced_raw_or_unknown_export"
            raw += 1
        files.append(
            {
                "path": str(path),
                "relative_path": rel,
                "size_bytes": path.stat().st_size,
                "header_count": len(headers),
                "headers": headers,
                "role": role,
                "manifest_referenced": rel in refs,
                "normalized_shape": normalized_shape,
            }
        )
    actionable = normalized + raw
    if normalized:
        status = "READY_UNREFERENCED_NORMALIZED_EXPORTS_FOUND"
        action = "Run upsert_kis_axis_wide_source_export_manifest_row.py for the reviewed normalized export."
    elif raw:
        status = "READY_UNREFERENCED_RAW_EXPORTS_FOUND"
        action = "Run normalize_kis_axis_wide_source_export.py for the reviewed raw export."
    else:
        status = "BLOCK_NO_SOURCE_EXPORT_FILES_IN_INBOX"
        action = "Place a reviewed raw or normalized KRX/licensed vendor CSV under axis_wide_source_exports."
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "export_dir": str(EXPORT_DIR),
        "raw_drop_dir": str(RAW_DIR),
        "normalized_export_dir": str(NORMALIZED_EXPORT_DIR),
        "created_dirs": created,
        "csv_file_count": len(files),
        "actionable_file_count": actionable,
        "unreferenced_normalized_export_count": normalized,
        "unreferenced_raw_or_unknown_export_count": raw,
        "files": files,
        "single_next_action": action,
        "non_goals": ["does_not_normalize_files", "does_not_edit_manifest", "does_not_enable_paper_live_broker_submit_or_order_intent"],
        "safety": SAFETY,
    }


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(f"# KIS Source Export Inbox Status\n\n- Status: `{report['status']}`\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "latest_json": str(REPORT_JSON), "actionable_file_count": report["actionable_file_count"], "safety": SAFETY}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
