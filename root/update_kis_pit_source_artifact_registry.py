from __future__ import annotations

import argparse
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
REGISTRY = ROOT / "data_snapshots/kis_pit_membership/source_artifact_registry.csv"
REPORT_JSON = ROOT / "reports/operations/kis_pit_source_artifact_registry_update_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_pit_source_artifact_registry_update_latest.md"
REGISTRY_HEADERS = ["source", "snapshot_id", "evidence_quality", "artifact_path", "sha256", "reviewed_at", "notes"]
SAFETY = intake_contract.SAFETY
CONFIRMATION_PHRASE = "APPLY SOURCE ARTIFACT REGISTRY UPDATE"


def _sha(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ensure_registry(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        csv.DictWriter(f, fieldnames=REGISTRY_HEADERS, lineterminator="\n").writeheader()


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REGISTRY_HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({header: row.get(header, "") for header in REGISTRY_HEADERS} for row in rows)


def _is_generic(value: str, generic_values: set[str]) -> bool:
    normalized = value.strip().lower()
    return not normalized or normalized in generic_values or len(normalized) < 8


def _upsert(rows: list[dict[str, str]], proposed_row: dict[str, str]) -> list[dict[str, str]]:
    key = (proposed_row["source"], proposed_row["snapshot_id"], proposed_row["evidence_quality"])
    updated = False
    out: list[dict[str, str]] = []
    for row in rows:
        row_key = (row.get("source", ""), row.get("snapshot_id", ""), row.get("evidence_quality", ""))
        if row_key == key:
            out.append(proposed_row)
            updated = True
        else:
            out.append(row)
    if not updated:
        out.append(proposed_row)
    return out


def build_report(
    generated_at: str | None = None,
    *,
    source: str,
    snapshot_id: str,
    evidence_quality: str,
    artifact_path: str,
    reviewed_at: str,
    notes: str,
    apply: bool,
    confirmation: str | None,
    registry_path: Path = REGISTRY,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    artifact = Path(artifact_path)
    sha256 = _sha(artifact)
    proposed_row = {
        "source": source.strip(),
        "snapshot_id": snapshot_id.strip(),
        "evidence_quality": evidence_quality.strip(),
        "artifact_path": str(artifact),
        "sha256": sha256 or "",
        "reviewed_at": reviewed_at.strip(),
        "notes": notes.strip(),
    }
    blockers: list[str] = []
    if _is_generic(source, {"source", "vendor", "manual", "unknown", "example"}):
        blockers.append("source_too_generic")
    if _is_generic(snapshot_id, {"snapshot", "snap", "manual", "unknown", "example"}):
        blockers.append("snapshot_id_too_generic")
    if evidence_quality.strip() not in {"authoritative", "licensed_vendor", "replay_test_authoritative"}:
        blockers.append("evidence_quality_not_allowed")
    if sha256 is None:
        blockers.append("artifact_file_missing")
    if apply and confirmation != CONFIRMATION_PHRASE:
        blockers.append("confirmation_phrase_missing")

    registry_file_mutated = False
    if apply and not blockers:
        _ensure_registry(registry_path)
        rows = _read_rows(registry_path)
        _write_rows(registry_path, _upsert(rows, proposed_row))
        registry_file_mutated = True

    if blockers:
        status = "BLOCK_SOURCE_ARTIFACT_REGISTRY_UPDATE"
    elif apply:
        status = "APPLIED_SOURCE_ARTIFACT_REGISTRY_UPDATE"
    else:
        status = "DRY_RUN_READY_FOR_SOURCE_ARTIFACT_REGISTRY_UPDATE"

    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "registry_path": str(registry_path),
        "registry_file_mutated": registry_file_mutated,
        "proposed_row": proposed_row,
        "blockers": sorted(set(blockers)),
        "confirmation_phrase_required": CONFIRMATION_PHRASE,
        "non_goals": [
            "does_not_enable_paper_live_broker_submit_or_order_intent",
            "does_not_import_canonical_membership_rows",
        ],
        "safety": SAFETY,
    }


def _write_report(report: dict) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(
        "# KIS PIT Source Artifact Registry Update\n\n"
        f"- Status: `{report['status']}`\n"
        f"- Registry mutated: `{str(report['registry_file_mutated']).lower()}`\n"
        f"- Blockers: `{', '.join(report['blockers']) if report['blockers'] else 'none'}`\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely upsert a reviewed KIS PIT source artifact registry row.")
    parser.add_argument("--source", required=True)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--evidence-quality", required=True)
    parser.add_argument("--artifact-path", required=True)
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument("--notes", default="")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirmation")
    parser.add_argument("--registry-path", default=str(REGISTRY))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        source=args.source,
        snapshot_id=args.snapshot_id,
        evidence_quality=args.evidence_quality,
        artifact_path=args.artifact_path,
        reviewed_at=args.reviewed_at,
        notes=args.notes,
        apply=args.apply,
        confirmation=args.confirmation,
        registry_path=Path(args.registry_path),
    )
    _write_report(report)
    print(json.dumps({"status": report["status"], "blockers": report["blockers"], "latest_json": str(REPORT_JSON), "safety": SAFETY}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
