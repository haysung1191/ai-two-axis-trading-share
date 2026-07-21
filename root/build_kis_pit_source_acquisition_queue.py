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
REQUIREMENTS_JSON = ROOT / "reports/operations/kis_pit_data_requirements_latest.json"
GAP_MATRIX_JSON = ROOT / "reports/operations/kis_historical_pit_survivorship_gap_matrix_latest.json"
LOCAL_SOURCE_AUDIT_JSON = ROOT / "reports/operations/kis_provider_response_local_source_audit_latest.json"
PUBLIC_PROBE_JSON = ROOT / "reports/operations/kis_provider_public_source_probe_latest.json"
INTAKE_WORK_ORDER_JSON = ROOT / "reports/operations/kis_pit_intake_work_order_latest.json"
INTAKE_PREFLIGHT_JSON = ROOT / "reports/operations/kis_pit_intake_import_preflight_latest.json"
REPORT_JSON = ROOT / "reports/operations/kis_pit_source_acquisition_queue_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_pit_source_acquisition_queue_latest.md"
SAFETY = intake_contract.SAFETY


def _generated_at_utc(generated_at: str) -> str:
    parsed = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(ZoneInfo("UTC")).isoformat()


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _public_probe_rejected(public_probe: dict, symbol: str) -> bool:
    for probe in public_probe.get("probes", []):
        if symbol in probe.get("symbols", []) and str(probe.get("decision", "")).startswith("REJECT"):
            return True
    return False


def _minimal_complete(intake_work_order: dict | None, intake_preflight: dict | None) -> bool:
    if not intake_work_order or not intake_preflight:
        return False
    return (
        int(intake_work_order.get("minimal_cand022_task_count", 0) or 0) > 0
        and int(intake_work_order.get("minimal_cand022_blocked_task_count", 0) or 0) == 0
        and int(intake_preflight.get("ready_row_count", 0) or 0) > 0
        and int(intake_preflight.get("blocked_row_count", 0) or 0) == 0
    )


def _minimal_items(requirements: dict, public_probe: dict, minimal_complete: bool) -> list[dict]:
    if minimal_complete:
        return []
    items = []
    for requirement in requirements.get("membership_requirements", []):
        blockers = requirement.get("current_blockers", [])
        if blockers:
            items.append({
                "queue_id": f"KIS_SRC_{len(items) + 1:03d}",
                "lane": "minimal_cand022_unblock",
                "evidence_type": "membership_interval",
                "axis": requirement.get("axis", ""),
                "symbol": requirement.get("symbol", ""),
                "rebalance_date_to_cover": requirement.get("rebalance_date_to_cover", ""),
                "target_file": requirement.get("target_file", ""),
                "required_source_quality": "authoritative|exchange_official|licensed_vendor",
                "public_probe_rejected": _public_probe_rejected(public_probe, requirement.get("symbol", "")),
                "blocking_reason": ";".join(blockers),
                "trading_enabled": False,
            })
    for key, evidence_type in [
        ("delisting_event_requirements", "delisting_event_history"),
        ("delisting_replay_requirements", "delisting_replay_policy"),
    ]:
        requirement = requirements.get(key, {})
        blockers = requirement.get("current_blockers", [])
        if blockers:
            items.append({
                "queue_id": f"KIS_SRC_{len(items) + 1:03d}",
                "lane": "minimal_cand022_unblock",
                "evidence_type": evidence_type,
                "axis": "kis_combined",
                "symbol": "*",
                "target_file": requirement.get("target_file", ""),
                "required_source_quality": "authoritative|exchange_official|licensed_vendor",
                "public_probe_rejected": False,
                "blocking_reason": ";".join(blockers),
                "required_scenarios": requirement.get("required_scenarios", []),
                "trading_enabled": False,
            })
    if requirements.get("delisting_replay_requirements", {}).get("required_scenarios"):
        scenarios = requirements["delisting_replay_requirements"].get("required_scenarios", [])
        items.append({
            "queue_id": f"KIS_SRC_{len(items) + 1:03d}",
            "lane": "minimal_cand022_unblock",
            "evidence_type": "delisting_replay_scenario_review",
            "axis": "kis_combined",
            "symbol": "*",
            "target_file": requirements["delisting_replay_requirements"].get("target_file", ""),
            "required_source_quality": "authoritative|exchange_official|licensed_vendor",
            "public_probe_rejected": False,
            "blocking_reason": "required_scenarios:" + "|".join(scenarios),
            "trading_enabled": False,
        })
    return items


def _axis_items(gap_matrix: dict, start_index: int) -> list[dict]:
    items = []
    for row in gap_matrix.get("axis_membership_gap_matrix", []):
        blockers = row.get("blockers", [])
        if not blockers:
            continue
        axis = row.get("axis", "")
        items.append({
            "queue_id": f"KIS_SRC_{start_index + len(items):03d}",
            "lane": "axis_wide_operation_ready",
            "evidence_type": "axis_membership_history",
            "axis": axis,
            "symbol": "*",
            "rebalance_date_to_cover": "full_backtest_window",
            "target_file": "",
            "required_source_quality": "authoritative|exchange_official|licensed_vendor",
            "current_local_quality": "current_snapshot_caveated",
            "public_probe_rejected": "",
            "accepted_public_probe_available": False,
            "blocking_reason": ";".join(blockers),
            "next_action": f"replace caveated rows for {axis}",
            "trading_enabled": False,
        })
    return items


def build_queue(
    generated_at: str | None = None,
    requirements: dict | None = None,
    gap_matrix: dict | None = None,
    local_source_audit: dict | None = None,
    public_probe: dict | None = None,
    intake_work_order: dict | None = None,
    intake_preflight: dict | None = None,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    using_default_files = all(
        value is None
        for value in [requirements, gap_matrix, local_source_audit, public_probe, intake_work_order, intake_preflight]
    )
    requirements = requirements if requirements is not None else _read_json(REQUIREMENTS_JSON)
    gap_matrix = gap_matrix if gap_matrix is not None else _read_json(GAP_MATRIX_JSON)
    local_source_audit = local_source_audit if local_source_audit is not None else _read_json(LOCAL_SOURCE_AUDIT_JSON)
    public_probe = public_probe if public_probe is not None else _read_json(PUBLIC_PROBE_JSON)
    if using_default_files:
        intake_work_order = _read_json(INTAKE_WORK_ORDER_JSON)
        intake_preflight = _read_json(INTAKE_PREFLIGHT_JSON)

    minimal_complete = _minimal_complete(intake_work_order, intake_preflight)
    queue = _minimal_items(requirements, public_probe, minimal_complete)
    queue.extend(_axis_items(gap_matrix, len(queue) + 1))
    minimal_count = sum(1 for row in queue if row.get("lane") == "minimal_cand022_unblock")
    axis_count = sum(1 for row in queue if row.get("lane") == "axis_wide_operation_ready")
    status = "PASS_NO_SOURCE_ACQUISITION_REQUIRED"
    if minimal_count:
        status = "BLOCK_SOURCE_ACQUISITION_REQUIRED"
    elif axis_count:
        status = "BLOCK_AXIS_WIDE_SOURCE_ACQUISITION_REQUIRED"

    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "generated_at_utc": _generated_at_utc(generated_at),
        "status": status,
        "minimal_cand022_intake_complete": minimal_complete,
        "queue_counts": {
            "total": len(queue),
            "minimal_cand022_unblock": minimal_count,
            "axis_wide_operation_ready": axis_count,
        },
        "first_queue_item": queue[0] if queue else None,
        "queue": queue,
        "single_next_action": "Replace caveated current-snapshot membership rows with authoritative or licensed historical membership intervals for all four KIS axes." if axis_count and not minimal_count else "Collect source-backed KIS PIT evidence for the first blocked queue item.",
        "non_goals": [
            "does_not_fetch_external_data",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    return "\n".join([
        "# KIS PIT Source Acquisition Queue",
        "",
        f"- Status: `{report['status']}`",
        f"- Total: `{report['queue_counts']['total']}`",
        f"- Minimal CAND-022: `{report['queue_counts']['minimal_cand022_unblock']}`",
        f"- Axis-wide: `{report['queue_counts']['axis_wide_operation_ready']}`",
        f"- Single next action: {report['single_next_action']}",
    ]) + "\n"


def main() -> int:
    report = build_queue()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "queue_counts": report["queue_counts"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
