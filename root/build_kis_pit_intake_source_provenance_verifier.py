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
PREFLIGHT_JSON = ROOT / "reports/operations/kis_pit_intake_import_preflight_latest.json"
REGISTRY_JSON = ROOT / "reports/operations/kis_pit_source_artifact_registry_verifier_latest.json"
REPORT_JSON = ROOT / "reports/operations/kis_pit_intake_source_provenance_verifier_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_pit_intake_source_provenance_verifier_latest.md"
SAFETY = intake_contract.SAFETY
GENERIC_SOURCES = {"vendor", "source", "unknown", "manual"}
GENERIC_SNAPSHOTS = {"snap", "snapshot", "example", "placeholder"}
REJECTED_MARKERS = ["current_snapshot_caveated", "historical_replay_only"]


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def build_report(generated_at: str | None = None, preflight: dict | None = None, source_artifact_registry: dict | None = None) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    preflight = preflight or _read_json(PREFLIGHT_JSON)
    source_artifact_registry = source_artifact_registry or _read_json(REGISTRY_JSON)
    blockers = []
    if preflight.get("status") != "READY_FOR_MANUAL_CANONICAL_IMPORT_REVIEW":
        blockers.append("intake_preflight_not_ready")
    if source_artifact_registry.get("status") != "PASS_SOURCE_ARTIFACT_REGISTRY_VERIFIED":
        blockers.append("source_artifact_registry_not_verified")
        blockers.extend(source_artifact_registry.get("blockers", []))
    ready_rows = preflight.get("ready_rows", [])
    if not ready_rows:
        blockers.append("no_ready_rows_to_verify")
    passed = 0
    blocked_rows = 0
    for ready in ready_rows:
        row = ready.get("row", {})
        row_blockers = []
        source = str(row.get("source", ""))
        snapshot = str(row.get("snapshot_id", ""))
        if source.lower() in GENERIC_SOURCES:
            row_blockers.append("source_too_generic")
        if snapshot.lower() in GENERIC_SNAPSHOTS:
            row_blockers.append("snapshot_id_too_generic")
        if any(marker in source for marker in REJECTED_MARKERS):
            row_blockers.append("rejected_source_marker_present")
        if row_blockers:
            blocked_rows += 1
            blockers.extend(row_blockers)
        else:
            passed += 1
    status = "PASS_INTAKE_SOURCE_PROVENANCE_VERIFIED" if not blockers else "BLOCK_INTAKE_SOURCE_PROVENANCE"
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "ready_row_count": len(ready_rows),
        "passed_ready_row_count": passed if status.startswith("PASS") else 0,
        "blocked_ready_row_count": blocked_rows,
        "blockers": sorted(set(blockers)),
        "safety": SAFETY,
    }


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(f"# KIS PIT Intake Source Provenance Verifier\n\n- Status: `{report['status']}`\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "blockers": report["blockers"], "latest_json": str(REPORT_JSON), "safety": SAFETY}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
