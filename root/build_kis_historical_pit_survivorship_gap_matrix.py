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
import build_kis_pit_membership_verifier as membership_verifier


KST = ZoneInfo("Asia/Seoul")
REPORT_JSON = ROOT / "reports/operations/kis_historical_pit_survivorship_gap_matrix_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_historical_pit_survivorship_gap_matrix_latest.md"
SAFETY = intake_contract.SAFETY


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _pass_status(report: dict, expected: str) -> bool:
    return report.get("status") == expected


def build_gap_matrix(
    generated_at: str | None = None,
    membership: dict | None = None,
    event: dict | None = None,
    no_event: dict | None = None,
    replay: dict | None = None,
    policy: dict | None = None,
    rebalance: dict | None = None,
    manifest: dict | None = None,
    official_route: dict | None = None,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    membership = membership or membership_verifier.build_report(generated_at)
    event = event or _read_json(ROOT / "reports/operations/kis_delisting_event_file_verifier_latest.json")
    no_event = no_event or _read_json(ROOT / "reports/operations/kis_delisting_no_event_coverage_latest.json")
    replay = replay or _read_json(ROOT / "reports/operations/kis_delisting_replay_verifier_latest.json")
    policy = policy or _read_json(ROOT / "reports/operations/kis_delisting_symbol_policy_latest.json")
    rebalance = rebalance or _read_json(ROOT / "reports/operations/kis_rebalance_membership_filter_proof_latest.json")
    manifest = manifest or _read_json(ROOT / "reports/operations/kis_operation_ready_manifest_latest.json")
    official_route = official_route or _read_json(ROOT / "reports/operations/kis_official_open_trading_api_route_latest.json")

    gates = [
        {
            "gate_id": "G1_MEMBERSHIP_INTERVALS_OPERATION_READY",
            "passed": bool(membership.get("all_verified")),
            "blockers": membership.get("blockers", []),
        },
        {
            "gate_id": "G2_DELISTING_EVENTS_OPERATION_READY",
            "passed": _pass_status(event, "PASS_DELISTING_EVENT_FILE_VERIFIED") or _pass_status(no_event, "PASS_DELISTING_NO_EVENT_COVERAGE_VERIFIED"),
            "blockers": event.get("blockers", []) + no_event.get("blockers", []),
        },
        {
            "gate_id": "G3_DELISTING_REPLAY_POLICY_VERIFIED",
            "passed": _pass_status(replay, "PASS_DELISTING_REPLAY_VERIFIED") and _pass_status(policy, "PASS_DELISTING_SYMBOL_POLICY_VERIFIED"),
            "blockers": replay.get("blockers", []) + policy.get("blockers", []),
        },
        {
            "gate_id": "G4_REBALANCE_MEMBERSHIP_FILTER_PROVEN",
            "passed": _pass_status(rebalance, "PASS_REBALANCE_MEMBERSHIP_FILTER_PROOF"),
            "blockers": rebalance.get("blockers", []),
        },
        {
            "gate_id": "G5_OPERATION_READY_MANIFEST_VERIFIED",
            "passed": bool(manifest.get("operation_ready")) or _pass_status(manifest, "PASS_OPERATION_READY_MANIFEST"),
            "blockers": manifest.get("blockers", []),
        },
    ]
    passed_count = sum(1 for gate in gates if gate["passed"])
    first_blocked = next((gate for gate in gates if not gate["passed"]), None)
    remaining_blockers = sorted({blocker for gate in gates if not gate["passed"] for blocker in gate["blockers"]})
    operation_ready = passed_count == len(gates)
    axis_membership_gap_matrix = [
        {
            "axis": row.get("axis", ""),
            "row_count": row.get("row_count", 0),
            "caveated_row_count": row.get("caveated_row_count", 0),
            "operation_ready_quality_row_count": row.get("operation_ready_quality_row_count", 0),
            "verified": row.get("verified", False),
            "blockers": [] if row.get("verified") else ["operation_ready_quality_incomplete" if row.get("operation_ready_quality_row_count", 0) else "operation_ready_quality_rows_missing"],
        }
        for row in membership.get("axis_reports", [])
    ]
    official_current = bool(official_route.get("pipeline_decision", {}).get("retire_default_external_provider_dispatch"))
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "universe_id": "KIS_COMBINED_KRW",
        "status": "PASS_HISTORICAL_PIT_SURVIVORSHIP_READY" if operation_ready else "BLOCK_HISTORICAL_PIT_SURVIVORSHIP_GAPS",
        "operation_ready": operation_ready,
        "official_kis_current_readiness_active": official_current,
        "gate_summary": {
            "total_count": len(gates),
            "passed_count": passed_count,
            "first_blocked_gate_id": first_blocked["gate_id"] if first_blocked else None,
        },
        "gates": gates,
        "axis_membership_gap_matrix": axis_membership_gap_matrix,
        "remaining_blockers": remaining_blockers,
        "single_next_action": "Replace caveated current-snapshot membership rows with authoritative or licensed historical membership intervals for all four KIS axes.",
        "non_goals": [
            "does_not_enable_paper_live_broker_submit_or_order_intent",
            "does_not_submit_orders",
        ],
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    return "\n".join([
        "# KIS Historical PIT Survivorship Gap Matrix",
        "",
        f"- Status: `{report['status']}`",
        f"- First blocked gate: `{report['gate_summary']['first_blocked_gate_id']}`",
        f"- Passed gates: `{report['gate_summary']['passed_count']}/{report['gate_summary']['total_count']}`",
    ]) + "\n"


def main() -> int:
    report = build_gap_matrix()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "operation_ready": report["operation_ready"],
        "first_blocked_gate_id": report["gate_summary"]["first_blocked_gate_id"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
