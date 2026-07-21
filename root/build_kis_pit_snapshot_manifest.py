from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_kis_axis_wide_source_export_intake_contract as intake_contract
import build_kis_pit_membership_verifier as membership_verifier


KST = ZoneInfo("Asia/Seoul")
MANIFEST_DIR = ROOT / "data_snapshots/manifests"
LATEST_MANIFEST = MANIFEST_DIR / "kis_combined_pit_membership_manifest_latest.json"
OP_READY_LATEST = MANIFEST_DIR / "kis_combined_operation_ready_manifest_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_pit_snapshot_manifest_latest.md"
SAFETY = intake_contract.SAFETY


def default_membership_files() -> dict[str, Path]:
    return membership_verifier.default_files()


def default_report_files() -> dict[str, Path]:
    return {
        "current_snapshot_caveat": ROOT / "reports/operations/kis_current_snapshot_membership_caveat_latest.json",
        "membership_verifier": ROOT / "reports/operations/kis_pit_membership_verifier_latest.json",
        "delisting_event_verifier": ROOT / "reports/operations/kis_delisting_event_verifier_latest.json",
        "delisting_no_event_coverage_verifier": ROOT / "reports/operations/kis_delisting_no_event_coverage_verifier_latest.json",
        "delisting_replay_verifier": ROOT / "reports/operations/kis_delisting_replay_verifier_latest.json",
        "delisting_symbol_policy": ROOT / "reports/operations/kis_delisting_symbol_change_policy_latest.json",
        "rebalance_membership_filter_audit": ROOT / "reports/operations/kis_pit_rebalance_membership_filter_audit_latest.json",
        "upgrade_plan": ROOT / "reports/operations/kis_pit_survivorship_upgrade_plan_latest.json",
    }


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _file_info(label: str, path: Path, csv_like: bool = False) -> dict:
    exists = path.exists()
    line_count = 0
    if exists:
        with path.open("r", encoding="utf-8-sig", errors="replace") as f:
            line_count = sum(1 for _ in f)
    return {
        "label": label,
        "path": str(path),
        "exists": exists,
        "sha256": _sha256(path),
        "line_count": line_count if exists else 0,
        "data_row_count": max(line_count - 1, 0) if exists and csv_like else None,
        "size_bytes": path.stat().st_size if exists else 0,
    }


def _statuses(report_files: dict[str, Path]) -> dict[str, str | None]:
    return {label: _read_json(path).get("status") for label, path in report_files.items()}


def _blockers(component_status: dict[str, str | None]) -> list[str]:
    blockers = []
    if component_status.get("membership_verifier") != "PASS_MEMBERSHIP_FILES_VERIFIED":
        blockers.append("membership_verifier_not_operation_ready")
    event_ready = component_status.get("delisting_event_verifier") == "PASS_DELISTING_EVENT_FILE_VERIFIED"
    no_event_ready = component_status.get("delisting_no_event_coverage_verifier") == "PASS_DELISTING_NO_EVENT_COVERAGE_VERIFIED"
    if not (event_ready or no_event_ready):
        blockers.append("delisting_event_file_or_no_event_coverage_not_operation_ready")
    if component_status.get("delisting_replay_verifier") != "PASS_DELISTING_REPLAY_VERIFIED":
        blockers.append("delisting_replay_not_operation_ready")
    if component_status.get("delisting_symbol_policy") != "PASS_DELISTING_SYMBOL_POLICY_VERIFIED":
        blockers.append("delisting_symbol_policy_not_operation_ready")
    if component_status.get("rebalance_membership_filter_audit") != "PASS_REBALANCE_MEMBERSHIP_FILTER_PROOF":
        blockers.append("rebalance_membership_filter_not_operation_ready")
    if component_status.get("upgrade_plan") != "READY_FOR_REGISTRY_REVIEW":
        blockers.append("upgrade_plan_not_ready_for_registry_review")
    return blockers


def build_manifest(
    generated_at: str | None = None,
    membership_files: dict[str, Path] | None = None,
    report_files: dict[str, Path] | None = None,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    membership_files = membership_files or default_membership_files()
    report_files = report_files or default_report_files()
    component_status = _statuses(report_files)
    blockers = _blockers(component_status)
    operation_ready = not blockers
    manifest_id = "kis_combined_pit_membership_" + datetime.now(tz=KST).strftime("%Y%m%d_%H%M%S")
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "universe_id": "KIS_COMBINED_KRW",
        "manifest_id": manifest_id,
        "status": "PASS_OPERATION_READY_MANIFEST" if operation_ready else "BLOCK_OPERATION_READY_MANIFEST",
        "operation_ready": operation_ready,
        "membership_files": [
            _file_info(label, Path(path), csv_like=True)
            for label, path in membership_files.items()
        ],
        "report_files": [
            _file_info(label, Path(path), csv_like=False)
            for label, path in report_files.items()
        ],
        "component_status": component_status,
        "blockers": blockers,
        "residual_caveats": [] if operation_ready else [
            "current_snapshot_caveated_rows_are_not_historical_pit_membership",
            "authoritative_historical_membership_intervals_missing",
            "delisting_symbol_change_event_replay_missing",
        ],
        "safety": SAFETY,
    }


def render_md(manifest: dict) -> str:
    lines = [
        "# KIS PIT Snapshot Manifest",
        "",
        f"- Status: `{manifest['status']}`",
        f"- Operation ready: `{manifest['operation_ready']}`",
        f"- Blockers: `{', '.join(manifest['blockers'])}`",
    ]
    return "\n".join(lines) + "\n"


def write_manifest(manifest: dict) -> Path:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    timestamped = MANIFEST_DIR / f"{manifest['manifest_id']}_manifest.json"
    timestamped.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    LATEST_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    OP_READY_LATEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(render_md(manifest), encoding="utf-8")
    return timestamped


def main() -> int:
    manifest = build_manifest()
    path = write_manifest(manifest)
    print(json.dumps({
        "status": manifest["status"],
        "operation_ready": manifest["operation_ready"],
        "blockers": manifest["blockers"],
        "latest_json": str(OP_READY_LATEST),
        "timestamped_json": str(path),
        "safety": manifest["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
