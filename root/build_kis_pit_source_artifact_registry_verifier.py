from __future__ import annotations

import csv
import hashlib
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
REGISTRY = ROOT / "data_snapshots/kis_pit_membership/source_artifact_registry.csv"
REPORT_JSON = ROOT / "reports/operations/kis_pit_source_artifact_registry_verifier_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_pit_source_artifact_registry_verifier_latest.md"
SAFETY = intake_contract.SAFETY
REGISTRY_HEADERS = ["source", "snapshot_id", "evidence_quality", "artifact_path", "sha256", "reviewed_at", "notes"]


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _ensure_registry(path: Path) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        csv.DictWriter(f, fieldnames=REGISTRY_HEADERS, lineterminator="\n").writeheader()
    return True


def _read_registry(path: Path) -> list[dict[str, str]]:
    _ensure_registry(path)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _sha(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_report(generated_at: str | None = None, preflight: dict | None = None, registry_path: Path = REGISTRY) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    preflight = preflight or _read_json(PREFLIGHT_JSON)
    registry_created = _ensure_registry(registry_path)
    registry_rows = _read_registry(registry_path)
    blockers = []
    if preflight.get("status") != "READY_FOR_MANUAL_CANONICAL_IMPORT_REVIEW":
        blockers.append("intake_preflight_not_ready")
    ready_rows = preflight.get("ready_rows", [])
    if not ready_rows:
        blockers.append("no_ready_rows_to_match_artifacts")
    passed = []
    for ready in ready_rows:
        row = ready.get("row", {})
        matches = [
            reg for reg in registry_rows
            if reg.get("source") == row.get("source")
            and reg.get("snapshot_id") == row.get("snapshot_id")
            and reg.get("evidence_quality") == row.get("evidence_quality")
        ]
        verified = False
        for reg in matches:
            artifact = Path(reg.get("artifact_path", ""))
            actual = _sha(artifact)
            if actual and actual == reg.get("sha256"):
                verified = True
                passed.append(reg)
            elif actual:
                blockers.append("artifact_sha256_mismatch")
        if not verified:
            blockers.append("ready_row_source_artifact_not_verified")
    status = "PASS_SOURCE_ARTIFACT_REGISTRY_VERIFIED" if not blockers else "BLOCK_SOURCE_ARTIFACT_REGISTRY"
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "registry_created": registry_created,
        "registry_path": str(registry_path),
        "registry_row_count": len(registry_rows),
        "ready_row_count": len(ready_rows),
        "passed_registry_row_count": len(passed),
        "blockers": sorted(set(blockers)),
        "safety": SAFETY,
    }


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(f"# KIS PIT Source Artifact Registry Verifier\n\n- Status: `{report['status']}`\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "blockers": report["blockers"], "latest_json": str(REPORT_JSON), "safety": SAFETY}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
