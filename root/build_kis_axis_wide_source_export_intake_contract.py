from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
EXPORT_DIR = ROOT / "data_snapshots/kis_pit_membership/axis_wide_source_exports"
MANIFEST = EXPORT_DIR / "axis_wide_source_export_manifest.csv"
NORMALIZED_TEMPLATE = EXPORT_DIR / "axis_wide_membership_export_normalized_template.csv"
REPORT_JSON = ROOT / "reports/operations/kis_axis_wide_source_export_intake_contract_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_axis_wide_source_export_intake_contract_latest.md"

MANIFEST_COLUMNS = [
    "export_id",
    "source_family",
    "source_name",
    "source_url",
    "local_file",
    "snapshot_id",
    "license_scope",
    "evidence_quality",
    "covered_axes",
    "notes",
]
NORMALIZED_COLUMNS = [
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
    "source_artifact_path",
    "license_scope",
    "exchange",
    "issuer_name",
    "security_id",
    "notes",
]
ACCEPTED_EVIDENCE = {"authoritative", "exchange_official", "licensed_vendor"}
SAFETY = {
    "paper_enabled": False,
    "live_enabled": False,
    "broker_submit_allowed": False,
    "private_submit_used": False,
    "real_orders": 0,
    "order_intent_created": False,
    "pretrade_firewall_default_decision": "BLOCK",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def ensure_contract_files() -> None:
    if not MANIFEST.exists():
        _write_csv(
            MANIFEST,
            MANIFEST_COLUMNS,
            [
                {
                    "export_id": "EXAMPLE_KRX_LISTED_DELISTED_YYYYMMDD",
                    "source_family": "exchange_official",
                    "source_name": "KRX Data Marketplace",
                    "source_url": "https://data.krx.co.kr/",
                    "local_file": "exports\\example_krx_membership.csv",
                    "snapshot_id": "krx_export_YYYYMMDD",
                    "license_scope": "reviewed_internal_research",
                    "evidence_quality": "exchange_official",
                    "covered_axes": "kis_korea_stocks|kis_korea_etfs",
                    "notes": "Replace this example row with reviewed export metadata before validation.",
                }
            ],
        )
    if not NORMALIZED_TEMPLATE.exists():
        _write_csv(NORMALIZED_TEMPLATE, NORMALIZED_COLUMNS, [])


def _valid_date(value: str) -> bool:
    if not value:
        return True
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _date_tuple(value: str):
    return datetime.strptime(value, "%Y-%m-%d") if value else None


def _safe_date_tuple(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def validate_normalized_rows(
    path: Path,
    expected_snapshot_id: str,
    expected_evidence_quality: str,
    covered_axes: list[str] | None = None,
) -> dict:
    rows = _read_csv(path)
    blocked = []
    seen_keys = set()
    seen_intervals = set()
    covered = set(covered_axes or [])
    for index, row in enumerate(rows, start=2):
        blockers = []
        for col in ["axis", "symbol", "asset_type", "active_from", "source", "snapshot_id", "evidence_quality"]:
            if not row.get(col, "").strip():
                blockers.append(f"{col}_missing")
        if row.get("snapshot_id") != expected_snapshot_id:
            blockers.append("snapshot_id_mismatch")
        if row.get("evidence_quality") != expected_evidence_quality:
            blockers.append("evidence_quality_mismatch")
        if row.get("evidence_quality") not in ACCEPTED_EVIDENCE:
            blockers.append("evidence_quality_not_operation_ready")
        if not row.get("source_artifact_path", "").strip():
            blockers.append("source_artifact_path_missing")
        if not row.get("license_scope", "").strip():
            blockers.append("license_scope_missing")
        if covered and row.get("axis") not in covered:
            blockers.append("axis_not_declared_in_manifest_covered_axes")
        for col in ["active_from", "active_to", "listed_date", "delisted_date"]:
            if not _valid_date(row.get(col, "")):
                blockers.append(f"{col}_invalid_iso_date")
        active_from = _safe_date_tuple(row.get("active_from", ""))
        active_to = _safe_date_tuple(row.get("active_to", ""))
        listed = _safe_date_tuple(row.get("listed_date", ""))
        delisted = _safe_date_tuple(row.get("delisted_date", ""))
        if active_from and active_to and active_to < active_from:
            blockers.append("active_to_before_active_from")
        if listed and delisted and delisted < listed:
            blockers.append("delisted_date_before_listed_date")
        key = (row.get("axis"), row.get("symbol"), row.get("asset_type"))
        interval = (*key, row.get("active_from"), row.get("active_to"))
        if key in seen_keys:
            blockers.append("duplicate_axis_symbol_asset_type")
        if interval in seen_intervals:
            blockers.append("duplicate_membership_interval")
        seen_keys.add(key)
        seen_intervals.add(interval)
        if blockers:
            blocked.append({"row_number": index, "symbol": row.get("symbol", ""), "blockers": sorted(set(blockers))})
    return {
        "row_count": len(rows),
        "valid_row_count": len(rows) - len(blocked),
        "invalid_row_count": len(blocked),
        "sample_valid_row_count": min(50, len(rows) - len(blocked)),
        "blocked_rows_sample": blocked[:20],
        "sample_blockers": blocked[:20],
    }


def _export_report(row: dict[str, str]) -> dict:
    blockers = []
    export_id = row.get("export_id", "")
    if not export_id or export_id.startswith("EXAMPLE_"):
        blockers.append("export_id_missing_or_example")
    local_file = row.get("local_file", "")
    local_path = EXPORT_DIR / local_file
    if not local_file or not local_path.exists():
        blockers.append("local_file_missing_on_disk")
        validation = {}
    else:
        axes = [item for item in row.get("covered_axes", "").split("|") if item]
        validation = validate_normalized_rows(
            local_path,
            row.get("snapshot_id", ""),
            row.get("evidence_quality", ""),
            axes,
        )
        if validation["invalid_row_count"]:
            blockers.append("normalized_export_rows_not_ready")
    return {
        "export_id": export_id,
        "source_family": row.get("source_family", ""),
        "covered_axes": row.get("covered_axes", ""),
        "valid_for_operation_ready_intake": not blockers,
        "blockers": sorted(set(blockers)),
        "file_info": {"path": str(local_path)} if local_file and local_path.exists() else {},
        "normalized_validation": validation,
    }


def build_report(generated_at: str | None = None, *, ensure_contract_files: bool = True) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    if ensure_contract_files:
        globals()["ensure_contract_files"]()
    rows = _read_csv(MANIFEST)
    reports = [_export_report(row) for row in rows]
    blockers = sorted({b for report in reports for b in report["blockers"]})
    valid_count = sum(1 for report in reports if report["valid_for_operation_ready_intake"])
    status = "READY_SOURCE_EXPORTS_FOR_REPLACEMENT_MAPPING" if valid_count and not blockers else "BLOCK_SOURCE_EXPORT_INTAKE"
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "universe_id": "KIS_COMBINED_KRW",
        "status": status,
        "operation_ready": status.startswith("READY_"),
        "manifest_path": str(MANIFEST),
        "normalized_template_path": str(NORMALIZED_TEMPLATE),
        "created_files": [],
        "manifest_row_count": len(rows),
        "valid_export_count": valid_count,
        "blocked_export_count": len(rows) - valid_count,
        "required_manifest_columns": MANIFEST_COLUMNS,
        "required_normalized_columns": NORMALIZED_COLUMNS,
        "export_reports": reports,
        "blockers": blockers,
        "single_next_action": "Place reviewed KRX/vendor normalized export CSVs under axis_wide_source_exports and replace the example manifest row with source/snapshot/license metadata.",
        "non_goals": ["does_not_fill_replacement_worklists", "does_not_enable_paper_live_broker_submit_or_order_intent"],
        "safety": SAFETY,
    }


def render_markdown(report: dict) -> str:
    return f"# KIS Axis-wide Source Export Intake\n\n- Status: `{report['status']}`\n- Valid exports: `{report['valid_export_count']}`\n"


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "latest_json": str(REPORT_JSON), "blockers": report["blockers"], "safety": SAFETY}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
