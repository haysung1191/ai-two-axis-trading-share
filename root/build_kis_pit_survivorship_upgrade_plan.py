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
import build_kis_pit_membership_verifier as membership_verifier


KST = ZoneInfo("Asia/Seoul")
REPORT_JSON = ROOT / "reports/operations/kis_pit_survivorship_upgrade_plan_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_pit_survivorship_upgrade_plan_latest.md"
SAFETY = intake_contract.SAFETY


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _axis_evidence_from_files(files: dict[str, Path]) -> list[dict]:
    evidence = []
    for axis, path in files.items():
        rows = []
        headers = []
        if path.exists():
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                headers = list(reader.fieldnames or [])
                rows = list(reader)
        evidence.append({
            "axis": axis,
            "exists": path.exists(),
            "has_authoritative_membership_intervals": bool(rows) and all(
                row.get("evidence_quality") in membership_verifier.OPERATION_READY_EVIDENCE
                for row in rows
            ),
            "membership_interval_columns_found": [col for col in ["active_from", "active_to"] if col in headers],
        })
    return evidence


def _registry_universe(data_registry: dict) -> dict:
    for universe in data_registry.get("universes", []):
        if universe.get("universe_id") == "KIS_COMBINED_KRW":
            return universe
    return {}


def build_plan(
    generated_at: str | None = None,
    pit_audit: dict | None = None,
    operation_decision: dict | None = None,
    data_registry: dict | None = None,
    axis_evidence: list[dict] | None = None,
    membership: dict | None = None,
    delisting_policy: dict | None = None,
    rebalance: dict | None = None,
    snapshot_manifest: dict | None = None,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    pit_audit = pit_audit or _read_json(ROOT / "reports/operations/kis_historical_pit_survivorship_gap_matrix_latest.json")
    operation_decision = operation_decision or {"decision": {"operation_ready": False}}
    data_registry = data_registry or _read_json(ROOT / "data_registry.json")
    axis_evidence = axis_evidence or _axis_evidence_from_files(membership_verifier.default_files())
    membership = membership or _read_json(membership_verifier.REPORT_JSON)
    delisting_policy = delisting_policy or _read_json(ROOT / "reports/operations/kis_delisting_symbol_change_policy_latest.json")
    rebalance = rebalance or _read_json(ROOT / "reports/operations/kis_pit_rebalance_membership_filter_audit_latest.json")
    snapshot_manifest = snapshot_manifest or _read_json(ROOT / "data_snapshots/manifests/kis_combined_operation_ready_manifest_latest.json")

    all_axis_authoritative = bool(axis_evidence) and all(row.get("has_authoritative_membership_intervals") for row in axis_evidence)
    canonical_schema_ok = bool(membership.get("all_schema_ok"))
    canonical_has_rows = bool(membership.get("all_have_rows"))
    canonical_has_caveated = bool(membership.get("any_caveated_rows"))
    membership_verified = membership.get("status") == "PASS_MEMBERSHIP_FILES_VERIFIED"
    delisting_verified = delisting_policy.get("status") == "PASS_DELISTING_SYMBOL_POLICY_VERIFIED"
    rebalance_verified = rebalance.get("status") == "PASS_REBALANCE_MEMBERSHIP_FILTER_PROOF"
    snapshot_ready = bool(snapshot_manifest.get("operation_ready")) or snapshot_manifest.get("status") == "PASS_OPERATION_READY_MANIFEST"
    blockers = []
    if not membership_verified:
        blockers.append("authoritative_pit_membership_history_missing_for_kis_combined")
    if not delisting_verified:
        blockers.append("delisting_return_treatment_not_verified")
    if not rebalance_verified:
        blockers.append("strategy_manifest_does_not_prove_rebalance_membership_filter")
    if membership_verified and delisting_verified and rebalance_verified:
        blockers = []
    status = "READY_FOR_REGISTRY_REVIEW" if not blockers else "BLOCKED_DATA_UPGRADE_REQUIRED"
    safe_next_action = "Populate the four canonical PIT membership CSV files with authoritative historical membership intervals."
    if canonical_has_caveated:
        safe_next_action = (
            "Replace caveated rows with authoritative historical membership intervals, "
            "then verify delisting/symbol-change policy and rebalance membership filter evidence."
        )
    if status == "READY_FOR_REGISTRY_REVIEW":
        safe_next_action = "Review registry promotion for KIS_COMBINED_KRW after confirming no trading flags changed."
    universe = _registry_universe(data_registry)
    operation_ready_now = bool(operation_decision.get("decision", {}).get("operation_ready")) or bool(universe.get("operation_ready"))
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "universe_id": "KIS_COMBINED_KRW",
        "status": status,
        "operation_ready_now": operation_ready_now,
        "canonical_membership_schema_ok": canonical_schema_ok,
        "canonical_membership_has_rows": canonical_has_rows,
        "canonical_membership_has_caveated_rows": canonical_has_caveated,
        "axis_evidence": axis_evidence,
        "all_axis_authoritative_membership_intervals": all_axis_authoritative,
        "delisting_symbol_policy_status": delisting_policy.get("status"),
        "rebalance_membership_filter_status": rebalance.get("status"),
        "snapshot_manifest_status": snapshot_manifest.get("status"),
        "snapshot_manifest_operation_ready": snapshot_ready,
        "delisting_return_treatment_verified_now": delisting_verified,
        "rebalance_membership_filter_verified_now": rebalance_verified,
        "data_registry_universe": universe,
        "remaining_blockers": blockers,
        "safe_next_action": safe_next_action,
        "non_goals": [
            "does_not_modify_data_registry",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
    }


def render_md(plan: dict) -> str:
    return "\n".join([
        "# KIS PIT Survivorship Upgrade Plan",
        "",
        f"- Status: `{plan['status']}`",
        f"- Remaining blockers: `{', '.join(plan['remaining_blockers'])}`",
        f"- Safe next action: {plan['safe_next_action']}",
    ]) + "\n"


def main() -> int:
    plan = build_plan()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(plan), encoding="utf-8")
    print(json.dumps({
        "status": plan["status"],
        "remaining_blockers": plan["remaining_blockers"],
        "latest_json": str(REPORT_JSON),
        "safety": plan["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
