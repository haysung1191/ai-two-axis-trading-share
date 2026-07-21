from __future__ import annotations

import html
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_btc_1d_research_stack_health import (
    check_research_stack_health,
    render_research_stack_health_line,
)
from scripts.btc_1d_handoff_constants import (
    ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
)

ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load_json(path)


def _latest_path(analysis_dir: Path, name: str) -> Path:
    return analysis_dir / name


def _replace_research_segment(line: str, fresh_research_line: str) -> str:
    if not line or not fresh_research_line:
        return line
    segments = line.split(" || ")
    replaced = False
    refreshed_segments: list[str] = []
    for segment in segments:
        if segment.startswith("BTC 1d research stack |"):
            refreshed_segments.append(fresh_research_line)
            replaced = True
        else:
            refreshed_segments.append(segment)
    if replaced:
        return " || ".join(refreshed_segments)
    return line


def build_dashboard(analysis_dir: Path = ANALYSIS_DIR) -> dict[str, Any]:
    latest_summary_path = _latest_path(analysis_dir, "btc_1d_latest_summary_latest.json")
    operating_index_path = _latest_path(analysis_dir, "btc_1d_operating_index_latest.json")
    operating_brief_path = _latest_path(analysis_dir, "btc_1d_operating_brief_latest.json")
    quick_read_contract_path = _latest_path(
        analysis_dir, "btc_1d_quick_read_contract_screen_latest.json"
    )
    execution_contract_path = _latest_path(
        analysis_dir, "btc_1d_execution_contract_screen_latest.json"
    )
    paper_nightly_path = _latest_path(
        analysis_dir, "btc_1d_paper_nightly_summary_latest.json"
    )
    hold36_local_ceiling_path = _latest_path(
        analysis_dir, "btc_1d_hold36_local_ceiling_handoff_latest.json"
    )

    latest_summary = _load_json(latest_summary_path)
    operating_index = _load_json(operating_index_path)
    operating_brief = _load_json(operating_brief_path)
    quick_read_contract = _load_json(quick_read_contract_path)
    execution_contract = _load_json(execution_contract_path)
    paper_nightly = _load_json(paper_nightly_path)
    hold36_local_ceiling = _load_optional_json(hold36_local_ceiling_path)
    research_stack_brief_path = _latest_path(
        analysis_dir, "btc_1d_research_stack_operating_brief_latest.json"
    )

    quick_read_summary = quick_read_contract.get("contract_summary", {})
    quick_read_verdict = quick_read_contract.get("contract_verdict", {})
    execution_contract_summary = execution_contract.get("execution_contract_summary", {})
    execution_contract_verdict = execution_contract.get("execution_contract_verdict", {})
    hold36_local_ceiling_status = hold36_local_ceiling.get("local_ceiling_status", {})
    hold36_handoff_reference = hold36_local_ceiling.get("handoff_reference", {})
    hold36_handoff_metrics = hold36_local_ceiling.get("handoff_metrics", {})
    fresh_research_stack_status = operating_index.get("research_stack_status", "")
    if research_stack_brief_path.exists():
        fresh_research_stack_status = render_research_stack_health_line(
            check_research_stack_health(analysis_dir=analysis_dir)
        )
    combined_health_line = _replace_research_segment(
        str(operating_index.get("combined_health_line", "")),
        fresh_research_stack_status,
    )
    execution_contract_health_line = _replace_research_segment(
        str(
            operating_index.get(
                "execution_contract_health_line",
                execution_contract_summary.get("execution_contract_health_line", ""),
            )
        ),
        fresh_research_stack_status,
    )

    quick_read_partitioned = bool(
        quick_read_verdict.get("contracts_are_well_partitioned", False)
    )
    contract_health_aligned = bool(
        operating_index.get(
            "contract_health_aligned",
            quick_read_summary.get("contract_health_aligned", False),
        )
    )
    execution_contract_aligned = bool(
        execution_contract_verdict.get(
            "execution_contract_aligned",
            operating_index.get("execution_contract_aligned", False),
        )
    )
    paper_ledger_consistent = bool(
        operating_index.get(
            "paper_ledger_consistent",
            paper_nightly.get("paper_ledger_consistent", False),
        )
    )
    paper_execution_contract_aligned = bool(
        operating_index.get(
            "paper_execution_contract_aligned",
            paper_nightly.get("paper_execution_contract_aligned", False),
        )
    )
    paper_exit_duplicate_run = bool(
        operating_index.get(
            "paper_exit_duplicate_run",
            paper_nightly.get("paper_exit_duplicate_run", False),
        )
    )
    attack_challenger_candidate = str(
        operating_index.get("attack_challenger_candidate", "")
    )
    attack_challenger_role_assignment = str(
        operating_index.get("attack_challenger_role_assignment", "")
    )
    attack_challenger_promotion_ready = bool(
        operating_index.get("attack_challenger_promotion_ready", False)
    )
    attack_challenger_next_step = str(
        operating_index.get("attack_challenger_next_step", "")
    )
    attack_challenger_bridge_entry_ready = bool(
        operating_index.get("attack_challenger_bridge_entry_ready", False)
    )
    attack_challenger_bridge_queue_lane = str(
        operating_index.get("attack_challenger_bridge_queue_lane", "")
    )
    attack_challenger_execution_contract_entry_ready = bool(
        operating_index.get("attack_challenger_execution_contract_entry_ready", False)
    )
    attack_challenger_execution_contract_queue_lane = str(
        operating_index.get("attack_challenger_execution_contract_queue_lane", "")
    )
    attack_challenger_operator_stack_handoff_ready = bool(
        operating_index.get("attack_challenger_operator_stack_handoff_ready", False)
    )
    attack_challenger_operator_stack_handoff_lane = str(
        operating_index.get("attack_challenger_operator_stack_handoff_lane", "")
    )
    attack_challenger_operator_runbook_candidate_entry_ready = bool(
        operating_index.get(
            "attack_challenger_operator_runbook_candidate_entry_ready", False
        )
    )
    attack_challenger_operator_runbook_candidate_entry_lane = str(
        operating_index.get(
            "attack_challenger_operator_runbook_candidate_entry_lane", ""
        )
    )
    attack_challenger_operator_runbook_execution_entry_ready = bool(
        operating_index.get(
            "attack_challenger_operator_runbook_execution_entry_ready", False
        )
    )
    attack_challenger_operator_runbook_execution_entry_lane = str(
        operating_index.get(
            "attack_challenger_operator_runbook_execution_entry_lane", ""
        )
    )
    attack_challenger_live_readiness_review_ready = bool(
        operating_index.get("attack_challenger_live_readiness_review_ready", False)
    )
    attack_challenger_live_readiness_review_lane = str(
        operating_index.get("attack_challenger_live_readiness_review_lane", "")
    )
    attack_challenger_live_shadow_activation_review_ready = bool(
        operating_index.get(
            "attack_challenger_live_shadow_activation_review_ready", False
        )
    )
    attack_challenger_live_shadow_activation_review_lane = str(
        operating_index.get("attack_challenger_live_shadow_activation_review_lane", "")
    )
    attack_challenger_live_candidate_entry_ready = bool(
        operating_index.get("attack_challenger_live_candidate_entry_ready", False)
    )
    attack_challenger_live_candidate_entry_lane = str(
        operating_index.get("attack_challenger_live_candidate_entry_lane", "")
    )
    attack_challenger_live_operator_paper_entry_ready = bool(
        operating_index.get("attack_challenger_live_operator_paper_entry_ready", False)
    )
    attack_challenger_live_operator_paper_entry_lane = str(
        operating_index.get("attack_challenger_live_operator_paper_entry_lane", "")
    )
    attack_challenger_live_shadow_governance_review_ready = bool(
        operating_index.get("attack_challenger_live_shadow_governance_review_ready", False)
    )
    attack_challenger_live_shadow_governance_review_lane = str(
        operating_index.get("attack_challenger_live_shadow_governance_review_lane", "")
    )
    attack_challenger_live_governed_shadow_entry_ready = bool(
        operating_index.get("attack_challenger_live_governed_shadow_entry_ready", False)
    )
    attack_challenger_live_governed_shadow_entry_lane = str(
        operating_index.get("attack_challenger_live_governed_shadow_entry_lane", "")
    )
    attack_challenger_live_shadow_candidate_paper_review_ready = bool(
        operating_index.get("attack_challenger_live_shadow_candidate_paper_review_ready", False)
    )
    attack_challenger_live_shadow_candidate_paper_review_lane = str(
        operating_index.get("attack_challenger_live_shadow_candidate_paper_review_lane", "")
    )
    attack_challenger_live_shadow_candidate_governance_lock_ready = bool(
        operating_index.get(
            "attack_challenger_live_shadow_candidate_governance_lock_ready", False
        )
    )
    attack_challenger_live_shadow_candidate_governance_lock_lane = str(
        operating_index.get(
            "attack_challenger_live_shadow_candidate_governance_lock_lane", ""
        )
    )
    attack_challenger_live_shadow_locked_entry_ready = bool(
        operating_index.get("attack_challenger_live_shadow_locked_entry_ready", False)
    )
    attack_challenger_live_shadow_locked_entry_lane = str(
        operating_index.get("attack_challenger_live_shadow_locked_entry_lane", "")
    )
    attack_challenger_live_shadow_locked_candidate_review_ready = bool(
        operating_index.get(
            "attack_challenger_live_shadow_locked_candidate_review_ready", False
        )
    )
    attack_challenger_live_shadow_locked_candidate_review_lane = str(
        operating_index.get(
            "attack_challenger_live_shadow_locked_candidate_review_lane", ""
        )
    )
    attack_challenger_live_shadow_locked_candidate_release_review_ready = bool(
        operating_index.get(
            "attack_challenger_live_shadow_locked_candidate_release_review_ready",
            False,
        )
    )
    attack_challenger_live_shadow_locked_candidate_release_review_lane = str(
        operating_index.get(
            "attack_challenger_live_shadow_locked_candidate_release_review_lane",
            "",
        )
    )
    attack_challenger_live_shadow_locked_release_entry_ready = bool(
        operating_index.get("attack_challenger_live_shadow_locked_release_entry_ready", False)
    )
    attack_challenger_live_shadow_locked_release_entry_lane = str(
        operating_index.get("attack_challenger_live_shadow_locked_release_entry_lane", "")
    )
    attack_challenger_live_shadow_locked_release_candidate_review_ready = bool(
        operating_index.get(
            "attack_challenger_live_shadow_locked_release_candidate_review_ready",
            False,
        )
    )
    attack_challenger_live_shadow_locked_release_candidate_review_lane = str(
        operating_index.get(
            "attack_challenger_live_shadow_locked_release_candidate_review_lane",
            "",
        )
    )
    attack_challenger_live_shadow_locked_release_governance_check_ready = bool(
        operating_index.get(
            "attack_challenger_live_shadow_locked_release_governance_check_ready",
            False,
        )
    )
    attack_challenger_live_shadow_locked_release_governance_check_lane = str(
        operating_index.get(
            "attack_challenger_live_shadow_locked_release_governance_check_lane",
            "",
        )
    )
    attack_challenger_live_shadow_locked_release_governance_entry_ready = bool(
        operating_index.get(
            "attack_challenger_live_shadow_locked_release_governance_entry_ready",
            False,
        )
    )
    attack_challenger_live_shadow_locked_release_governance_entry_lane = str(
        operating_index.get(
            "attack_challenger_live_shadow_locked_release_governance_entry_lane",
            "",
        )
    )
    attack_challenger_remote_monitoring_deployment_handoff_ready = bool(
        operating_index.get(
            "attack_challenger_remote_monitoring_deployment_handoff_ready",
            False,
        )
    )
    attack_challenger_remote_monitoring_deployment_handoff_lane = str(
        operating_index.get(
            "attack_challenger_remote_monitoring_deployment_handoff_lane",
            "",
        )
    )
    attack_challenger_paper_validation_cagr = operating_index.get(
        "attack_challenger_paper_validation_cagr"
    )
    attack_challenger_paper_validation_max_drawdown = operating_index.get(
        "attack_challenger_paper_validation_max_drawdown"
    )
    attack_challenger_walk_forward_sensitivity_max_drift = operating_index.get(
        "attack_challenger_walk_forward_sensitivity_max_drift"
    )
    attack_challenger_friction_final_decision = str(
        operating_index.get("attack_challenger_friction_final_decision", "")
    )
    attack_challenger_bridge_report = str(
        operating_index.get("attack_challenger_bridge_report", "")
    )
    deployment_ready = all(
        [
            latest_summary.get("shadow_decision") == "ready",
            quick_read_partitioned,
            contract_health_aligned,
            execution_contract_aligned,
            paper_execution_contract_aligned,
            paper_ledger_consistent,
        ]
    )
    dashboard_ready = all(
        [
            latest_summary.get("shadow_decision")
            in {"ready", "shadow_ready_for_btc_only"},
            quick_read_partitioned,
            contract_health_aligned,
            execution_contract_aligned,
            paper_execution_contract_aligned,
            paper_ledger_consistent,
        ]
    )
    deployment_monitoring_active = all(
        [
            latest_summary.get("shadow_decision") == "shadow_ready_for_btc_only",
            dashboard_ready,
            attack_challenger_remote_monitoring_deployment_handoff_ready,
            attack_challenger_next_step
            == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
        ]
    )
    if deployment_ready:
        operator_verdict = "ready"
    elif (
        quick_read_partitioned
        and contract_health_aligned
        and execution_contract_aligned
        and paper_execution_contract_aligned
        and paper_ledger_consistent
        and latest_summary.get("shadow_decision") == "shadow_ready_for_btc_only"
    ):
        operator_verdict = "shadow_monitoring_ready"
    elif not (
        quick_read_partitioned
        and contract_health_aligned
        and execution_contract_aligned
        and paper_execution_contract_aligned
        and paper_ledger_consistent
    ):
        operator_verdict = "ops_repair_required"
    else:
        operator_verdict = "validation_in_progress"

    attention_flags: list[str] = []
    if latest_summary.get("shadow_decision") not in {"ready", "shadow_ready_for_btc_only"}:
        attention_flags.append(
            f"shadow_decision={latest_summary.get('shadow_decision', 'unknown')}"
        )
    if not quick_read_partitioned:
        attention_flags.append("quick_read_contract=drifted")
    if not contract_health_aligned:
        attention_flags.append("contract_health=drifted")
    if not execution_contract_aligned:
        attention_flags.append("execution_contract=drifted")
    if not paper_execution_contract_aligned:
        attention_flags.append("paper_execution_contract=drifted")
    if not paper_ledger_consistent:
        attention_flags.append("paper_ledger=inconsistent")
    carry = latest_summary.get("carry", {})
    survivability = latest_summary.get("survivability", {})
    walk_forward = latest_summary.get("walk_forward", {})
    friction = latest_summary.get("friction", {})
    eth_cross_check = latest_summary.get("eth_cross_check", {})

    current_work = [
        f"candidate={latest_summary.get('candidate', 'unknown')}",
        f"practical_status={operating_index.get('practical_status_label', 'unknown')}",
        f"shadow_decision={latest_summary.get('shadow_decision', 'unknown')}",
    ]
    if overview_research := fresh_research_stack_status:
        current_work.append(f"research_stack={overview_research}")
    if attack_challenger_candidate:
        current_work.append(f"attack_challenger={attack_challenger_candidate}")
    if hold36_handoff_reference.get("active_backup"):
        current_work.append(
            f"hold36_backup={hold36_handoff_reference.get('active_backup', '')}"
        )
    if hold36_local_ceiling_status.get("status_band"):
        current_work.append(
            "hold36_ceiling="
            f"{hold36_local_ceiling_status.get('status_band', '')}"
            "/"
            f"{hold36_local_ceiling_status.get('primary_blocker', '')}"
        )

    next_actions: list[str] = []
    if not contract_health_aligned:
        next_actions.append("contract_health drift recovery")
    if not paper_execution_contract_aligned:
        next_actions.append("paper execution contract alignment recovery")
    if not paper_ledger_consistent:
        next_actions.append("paper ledger consistency recovery")
    if (
        attack_challenger_next_step
        and (
            attack_challenger_promotion_ready
            or attack_challenger_remote_monitoring_deployment_handoff_ready
        )
    ):
        next_actions.append(attack_challenger_next_step)
    if not next_actions:
        next_actions.append("remote monitoring and deployment handoff")

    project_direction = (
        "ops hardening"
        if latest_summary.get("shadow_decision") == "shadow_ready_for_btc_only"
        else "model validation"
    )

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "dashboard_summary": {
            "dashboard_ready": dashboard_ready,
            "deployment_ready": deployment_ready,
            "deployment_monitoring_active": deployment_monitoring_active,
            "operator_verdict": operator_verdict,
            "candidate": latest_summary.get("candidate", "unknown"),
            "shadow_decision": latest_summary.get("shadow_decision", "unknown"),
            "practical_status_label": operating_index.get(
                "practical_status_label", "unknown"
            ),
            "quick_read_contract_partitioned": quick_read_partitioned,
            "contract_health_aligned": contract_health_aligned,
            "execution_contract_aligned": execution_contract_aligned,
            "paper_execution_contract_aligned": paper_execution_contract_aligned,
            "paper_ledger_consistent": paper_ledger_consistent,
            "paper_exit_duplicate_run": paper_exit_duplicate_run,
            "attack_challenger_candidate": attack_challenger_candidate,
            "attack_challenger_role_assignment": attack_challenger_role_assignment,
            "attack_challenger_promotion_ready": attack_challenger_promotion_ready,
            "attack_challenger_bridge_entry_ready": attack_challenger_bridge_entry_ready,
            "attack_challenger_bridge_queue_lane": attack_challenger_bridge_queue_lane,
            "attack_challenger_execution_contract_entry_ready": attack_challenger_execution_contract_entry_ready,
            "attack_challenger_execution_contract_queue_lane": attack_challenger_execution_contract_queue_lane,
            "attack_challenger_operator_stack_handoff_ready": attack_challenger_operator_stack_handoff_ready,
            "attack_challenger_operator_stack_handoff_lane": attack_challenger_operator_stack_handoff_lane,
            "attack_challenger_operator_runbook_candidate_entry_ready": attack_challenger_operator_runbook_candidate_entry_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": attack_challenger_operator_runbook_candidate_entry_lane,
            "attack_challenger_operator_runbook_execution_entry_ready": attack_challenger_operator_runbook_execution_entry_ready,
            "attack_challenger_operator_runbook_execution_entry_lane": attack_challenger_operator_runbook_execution_entry_lane,
            "attack_challenger_live_readiness_review_ready": attack_challenger_live_readiness_review_ready,
            "attack_challenger_live_readiness_review_lane": attack_challenger_live_readiness_review_lane,
            "attack_challenger_live_shadow_activation_review_ready": attack_challenger_live_shadow_activation_review_ready,
            "attack_challenger_live_shadow_activation_review_lane": attack_challenger_live_shadow_activation_review_lane,
            "attack_challenger_live_candidate_entry_ready": attack_challenger_live_candidate_entry_ready,
            "attack_challenger_live_candidate_entry_lane": attack_challenger_live_candidate_entry_lane,
            "attack_challenger_live_operator_paper_entry_ready": attack_challenger_live_operator_paper_entry_ready,
            "attack_challenger_live_operator_paper_entry_lane": attack_challenger_live_operator_paper_entry_lane,
            "attack_challenger_live_shadow_governance_review_ready": attack_challenger_live_shadow_governance_review_ready,
            "attack_challenger_live_shadow_governance_review_lane": attack_challenger_live_shadow_governance_review_lane,
            "attack_challenger_live_governed_shadow_entry_ready": attack_challenger_live_governed_shadow_entry_ready,
            "attack_challenger_live_governed_shadow_entry_lane": attack_challenger_live_governed_shadow_entry_lane,
            "attack_challenger_live_shadow_candidate_paper_review_ready": attack_challenger_live_shadow_candidate_paper_review_ready,
            "attack_challenger_live_shadow_candidate_paper_review_lane": attack_challenger_live_shadow_candidate_paper_review_lane,
            "attack_challenger_live_shadow_candidate_governance_lock_ready": attack_challenger_live_shadow_candidate_governance_lock_ready,
            "attack_challenger_live_shadow_candidate_governance_lock_lane": attack_challenger_live_shadow_candidate_governance_lock_lane,
            "attack_challenger_live_shadow_locked_entry_ready": attack_challenger_live_shadow_locked_entry_ready,
            "attack_challenger_live_shadow_locked_entry_lane": attack_challenger_live_shadow_locked_entry_lane,
            "attack_challenger_live_shadow_locked_candidate_review_ready": attack_challenger_live_shadow_locked_candidate_review_ready,
            "attack_challenger_live_shadow_locked_candidate_review_lane": attack_challenger_live_shadow_locked_candidate_review_lane,
            "attack_challenger_live_shadow_locked_candidate_release_review_ready": attack_challenger_live_shadow_locked_candidate_release_review_ready,
            "attack_challenger_live_shadow_locked_candidate_release_review_lane": attack_challenger_live_shadow_locked_candidate_release_review_lane,
            "attack_challenger_live_shadow_locked_release_entry_ready": attack_challenger_live_shadow_locked_release_entry_ready,
            "attack_challenger_live_shadow_locked_release_entry_lane": attack_challenger_live_shadow_locked_release_entry_lane,
            "attack_challenger_live_shadow_locked_release_candidate_review_ready": attack_challenger_live_shadow_locked_release_candidate_review_ready,
            "attack_challenger_live_shadow_locked_release_candidate_review_lane": attack_challenger_live_shadow_locked_release_candidate_review_lane,
            "attack_challenger_live_shadow_locked_release_governance_check_ready": attack_challenger_live_shadow_locked_release_governance_check_ready,
            "attack_challenger_live_shadow_locked_release_governance_check_lane": attack_challenger_live_shadow_locked_release_governance_check_lane,
            "attack_challenger_live_shadow_locked_release_governance_entry_ready": attack_challenger_live_shadow_locked_release_governance_entry_ready,
            "attack_challenger_live_shadow_locked_release_governance_entry_lane": attack_challenger_live_shadow_locked_release_governance_entry_lane,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": attack_challenger_remote_monitoring_deployment_handoff_ready,
            "attack_challenger_remote_monitoring_deployment_handoff_lane": attack_challenger_remote_monitoring_deployment_handoff_lane,
            "attack_challenger_next_step": attack_challenger_next_step,
            "attention_flags": attention_flags,
        },
        "development": {
            "project_direction": project_direction,
            "current_work": current_work,
            "next_actions": next_actions,
        },
        "promotion_bridge": {
            "attack_challenger_candidate": attack_challenger_candidate,
            "attack_challenger_role_assignment": attack_challenger_role_assignment,
            "attack_challenger_promotion_ready": attack_challenger_promotion_ready,
            "attack_challenger_bridge_entry_ready": attack_challenger_bridge_entry_ready,
            "attack_challenger_bridge_queue_lane": attack_challenger_bridge_queue_lane,
            "attack_challenger_execution_contract_entry_ready": attack_challenger_execution_contract_entry_ready,
            "attack_challenger_execution_contract_queue_lane": attack_challenger_execution_contract_queue_lane,
            "attack_challenger_operator_stack_handoff_ready": attack_challenger_operator_stack_handoff_ready,
            "attack_challenger_operator_stack_handoff_lane": attack_challenger_operator_stack_handoff_lane,
            "attack_challenger_operator_runbook_candidate_entry_ready": attack_challenger_operator_runbook_candidate_entry_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": attack_challenger_operator_runbook_candidate_entry_lane,
            "attack_challenger_operator_runbook_execution_entry_ready": attack_challenger_operator_runbook_execution_entry_ready,
            "attack_challenger_operator_runbook_execution_entry_lane": attack_challenger_operator_runbook_execution_entry_lane,
            "attack_challenger_live_readiness_review_ready": attack_challenger_live_readiness_review_ready,
            "attack_challenger_live_readiness_review_lane": attack_challenger_live_readiness_review_lane,
            "attack_challenger_live_shadow_activation_review_ready": attack_challenger_live_shadow_activation_review_ready,
            "attack_challenger_live_shadow_activation_review_lane": attack_challenger_live_shadow_activation_review_lane,
            "attack_challenger_live_candidate_entry_ready": attack_challenger_live_candidate_entry_ready,
            "attack_challenger_live_candidate_entry_lane": attack_challenger_live_candidate_entry_lane,
            "attack_challenger_live_operator_paper_entry_ready": attack_challenger_live_operator_paper_entry_ready,
            "attack_challenger_live_operator_paper_entry_lane": attack_challenger_live_operator_paper_entry_lane,
            "attack_challenger_live_shadow_governance_review_ready": attack_challenger_live_shadow_governance_review_ready,
            "attack_challenger_live_shadow_governance_review_lane": attack_challenger_live_shadow_governance_review_lane,
            "attack_challenger_live_governed_shadow_entry_ready": attack_challenger_live_governed_shadow_entry_ready,
            "attack_challenger_live_governed_shadow_entry_lane": attack_challenger_live_governed_shadow_entry_lane,
            "attack_challenger_live_shadow_candidate_paper_review_ready": attack_challenger_live_shadow_candidate_paper_review_ready,
            "attack_challenger_live_shadow_candidate_paper_review_lane": attack_challenger_live_shadow_candidate_paper_review_lane,
            "attack_challenger_live_shadow_candidate_governance_lock_ready": attack_challenger_live_shadow_candidate_governance_lock_ready,
            "attack_challenger_live_shadow_candidate_governance_lock_lane": attack_challenger_live_shadow_candidate_governance_lock_lane,
            "attack_challenger_live_shadow_locked_entry_ready": attack_challenger_live_shadow_locked_entry_ready,
            "attack_challenger_live_shadow_locked_entry_lane": attack_challenger_live_shadow_locked_entry_lane,
            "attack_challenger_live_shadow_locked_candidate_review_ready": attack_challenger_live_shadow_locked_candidate_review_ready,
            "attack_challenger_live_shadow_locked_candidate_review_lane": attack_challenger_live_shadow_locked_candidate_review_lane,
            "attack_challenger_live_shadow_locked_candidate_release_review_ready": attack_challenger_live_shadow_locked_candidate_release_review_ready,
            "attack_challenger_live_shadow_locked_candidate_release_review_lane": attack_challenger_live_shadow_locked_candidate_release_review_lane,
            "attack_challenger_live_shadow_locked_release_entry_ready": attack_challenger_live_shadow_locked_release_entry_ready,
            "attack_challenger_live_shadow_locked_release_entry_lane": attack_challenger_live_shadow_locked_release_entry_lane,
            "attack_challenger_live_shadow_locked_release_candidate_review_ready": attack_challenger_live_shadow_locked_release_candidate_review_ready,
            "attack_challenger_live_shadow_locked_release_candidate_review_lane": attack_challenger_live_shadow_locked_release_candidate_review_lane,
            "attack_challenger_live_shadow_locked_release_governance_check_ready": attack_challenger_live_shadow_locked_release_governance_check_ready,
            "attack_challenger_live_shadow_locked_release_governance_check_lane": attack_challenger_live_shadow_locked_release_governance_check_lane,
            "attack_challenger_live_shadow_locked_release_governance_entry_ready": attack_challenger_live_shadow_locked_release_governance_entry_ready,
            "attack_challenger_live_shadow_locked_release_governance_entry_lane": attack_challenger_live_shadow_locked_release_governance_entry_lane,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": attack_challenger_remote_monitoring_deployment_handoff_ready,
            "attack_challenger_remote_monitoring_deployment_handoff_lane": attack_challenger_remote_monitoring_deployment_handoff_lane,
            "attack_challenger_next_step": attack_challenger_next_step,
            "attack_challenger_paper_validation_cagr": attack_challenger_paper_validation_cagr,
            "attack_challenger_paper_validation_max_drawdown": attack_challenger_paper_validation_max_drawdown,
            "attack_challenger_walk_forward_sensitivity_max_drift": attack_challenger_walk_forward_sensitivity_max_drift,
            "attack_challenger_friction_final_decision": attack_challenger_friction_final_decision,
        },
        "hold36_local_ceiling": {
            "active": bool(hold36_local_ceiling),
            "attack_main": hold36_handoff_reference.get("attack_main", ""),
            "active_backup": hold36_handoff_reference.get("active_backup", ""),
            "monitoring_candidate": hold36_handoff_reference.get(
                "monitoring_candidate", ""
            ),
            "status_band": hold36_local_ceiling_status.get("status_band", ""),
            "ceiling_confirmed": hold36_local_ceiling_status.get(
                "ceiling_confirmed", False
            ),
            "primary_blocker": hold36_local_ceiling_status.get(
                "primary_blocker", ""
            ),
            "remaining_base_cagr_gap_to_open": hold36_local_ceiling_status.get(
                "remaining_base_cagr_gap_to_open"
            ),
            "remaining_cost20_cagr_gap_to_open": hold36_local_ceiling_status.get(
                "remaining_cost20_cagr_gap_to_open"
            ),
            "do_not_repeat_local_loop": hold36_local_ceiling_status.get(
                "do_not_repeat_local_loop", False
            ),
            "next_step_now": hold36_local_ceiling_status.get("next_step_now", ""),
            "closed_local_axes": hold36_local_ceiling_status.get(
                "closed_local_axes", []
            ),
            "base_cagr_gap_to_main": hold36_handoff_metrics.get(
                "base_cagr_gap_to_main"
            ),
            "cost20_cagr_gap_to_main": hold36_handoff_metrics.get(
                "cost20_cagr_gap_to_main"
            ),
            "sharpe_edge_vs_main": hold36_handoff_metrics.get("sharpe_edge_vs_main"),
            "mdd_improvement_vs_main": hold36_handoff_metrics.get(
                "mdd_improvement_vs_main"
            ),
            "drift_improvement_vs_main": hold36_handoff_metrics.get(
                "drift_improvement_vs_main"
            ),
        },
        "performance": {
            "carry_decision": carry.get("decision"),
            "carry_sharpe": carry.get("sharpe"),
            "carry_cagr": carry.get("cagr"),
            "carry_max_drawdown": carry.get("max_drawdown"),
            "survivability_decision": survivability.get("decision"),
            "survivability_sharpe": survivability.get("sharpe"),
            "survivability_cagr": survivability.get("cagr"),
            "survivability_max_drawdown": survivability.get("max_drawdown"),
            "walk_forward_passed": walk_forward.get("passed"),
            "walk_forward_oos_sharpe": walk_forward.get("oos_sharpe"),
            "walk_forward_oos_cagr": walk_forward.get("oos_cagr"),
            "walk_forward_oos_max_drawdown": walk_forward.get("oos_max_drawdown"),
            "friction_decision": friction.get("decision"),
            "friction_heaviest_level_bps": friction.get("heaviest_level_bps"),
            "friction_heaviest_level_sharpe": friction.get("heaviest_level_sharpe"),
            "eth_symbol": eth_cross_check.get("symbol"),
            "eth_pass_rate": eth_cross_check.get("pass_rate"),
        },
        "overview": {
            "combined_health_line": combined_health_line,
            "research_stack_status": fresh_research_stack_status,
            "contract_health_line": operating_brief.get("contract_health_line", ""),
            "execution_contract_health_line": execution_contract_health_line,
            "execution_contract_read": operating_index.get(
                "execution_contract_read",
                execution_contract_summary.get("execution_contract_read", ""),
            ),
        },
        "paper_execution": {
            "paper_execution_read": operating_index.get(
                "paper_execution_read", paper_nightly.get("paper_execution_read", "")
            ),
            "intent_count": paper_nightly.get("intent_count"),
            "signed_request_count": paper_nightly.get("signed_request_count"),
            "paper_applied_count": paper_nightly.get("paper_applied_count"),
            "paper_duplicate_count": paper_nightly.get("paper_duplicate_count"),
            "paper_closed_count": paper_nightly.get("paper_closed_count"),
            "paper_open_count": paper_nightly.get("paper_open_count"),
            "paper_ledger_snapshot_read": operating_index.get(
                "paper_ledger_snapshot_read",
                paper_nightly.get("paper_ledger_snapshot_read", ""),
            ),
        },
        "contracts": {
            "quick_read_operating_contract_aligned": quick_read_summary.get(
                "operating_contract_aligned", False
            ),
            "quick_read_paper_execution_contract_aligned": quick_read_summary.get(
                "paper_execution_contract_aligned", False
            ),
            "quick_read_contract_health_aligned": quick_read_summary.get(
                "contract_health_aligned", False
            ),
            "execution_contract_paper_ledger_snapshot_summary_aligned": (
                execution_contract_summary.get(
                    "paper_ledger_snapshot_summary_aligned", False
                )
            ),
            "execution_contract_paper_execution_contract_aligned_summary_aligned": (
                execution_contract_summary.get(
                    "paper_execution_contract_aligned_summary_aligned", False
                )
            ),
        },
        "artifacts": {
            "latest_summary_json": str(latest_summary_path),
            "operating_index_json": str(operating_index_path),
            "operating_brief_json": str(operating_brief_path),
            "quick_read_contract_json": str(quick_read_contract_path),
            "execution_contract_json": str(execution_contract_path),
            "paper_nightly_summary_json": str(paper_nightly_path),
            "attack_challenger_bridge_report_json": attack_challenger_bridge_report,
            "hold36_local_ceiling_json": str(hold36_local_ceiling_path),
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["dashboard_summary"]
    development = payload["development"]
    performance = payload["performance"]
    promotion_bridge = payload["promotion_bridge"]
    hold36_local_ceiling = payload["hold36_local_ceiling"]
    overview = payload["overview"]
    paper = payload["paper_execution"]
    contracts = payload["contracts"]
    artifacts = payload["artifacts"]
    attention_flags = summary.get("attention_flags", [])

    lines = [
        "# BTC 1d Operator Dashboard",
        "",
        f"- Dashboard ready: `{summary['dashboard_ready']}`",
        f"- Deployment monitoring active: `{summary.get('deployment_monitoring_active', False)}`",
        f"- Operator verdict: `{summary['operator_verdict']}`",
        f"- Candidate: `{summary['candidate']}`",
        f"- Shadow decision: `{summary['shadow_decision']}`",
        f"- Practical status: `{summary['practical_status_label']}`",
        f"- Quick-read contract partitioned: `{summary['quick_read_contract_partitioned']}`",
        f"- Contract health aligned: `{summary['contract_health_aligned']}`",
        f"- Execution contract aligned: `{summary['execution_contract_aligned']}`",
        f"- Paper execution contract aligned: `{summary['paper_execution_contract_aligned']}`",
        f"- Paper ledger consistent: `{summary['paper_ledger_consistent']}`",
        f"- Paper exit duplicate run: `{summary['paper_exit_duplicate_run']}`",
        "",
        "## Development",
        f"- Project direction: `{development['project_direction']}`",
        f"- Current work: `{' | '.join(development['current_work'])}`",
        f"- Next actions: `{' | '.join(development['next_actions'])}`",
        "",
        "## Promotion Bridge",
        f"- Attack challenger: `{promotion_bridge['attack_challenger_candidate']}`",
        f"- Role assignment: `{promotion_bridge['attack_challenger_role_assignment']}`",
        f"- Promotion ready: `{promotion_bridge['attack_challenger_promotion_ready']}`",
        f"- Bridge entry ready: `{promotion_bridge['attack_challenger_bridge_entry_ready']}`",
        f"- Queue lane: `{promotion_bridge['attack_challenger_bridge_queue_lane']}`",
        f"- Execution contract entry ready: `{promotion_bridge.get('attack_challenger_execution_contract_entry_ready', False)}`",
        f"- Execution contract queue lane: `{promotion_bridge.get('attack_challenger_execution_contract_queue_lane', '')}`",
        f"- Operator stack handoff ready: `{promotion_bridge.get('attack_challenger_operator_stack_handoff_ready', False)}`",
        f"- Operator stack handoff lane: `{promotion_bridge.get('attack_challenger_operator_stack_handoff_lane', '')}`",
        f"- Operator runbook candidate entry ready: `{promotion_bridge.get('attack_challenger_operator_runbook_candidate_entry_ready', False)}`",
        f"- Operator runbook candidate lane: `{promotion_bridge.get('attack_challenger_operator_runbook_candidate_entry_lane', '')}`",
        f"- Operator runbook execution entry ready: `{promotion_bridge.get('attack_challenger_operator_runbook_execution_entry_ready', False)}`",
        f"- Operator runbook execution lane: `{promotion_bridge.get('attack_challenger_operator_runbook_execution_entry_lane', '')}`",
        f"- Live readiness review ready: `{promotion_bridge.get('attack_challenger_live_readiness_review_ready', False)}`",
        f"- Live readiness review lane: `{promotion_bridge.get('attack_challenger_live_readiness_review_lane', '')}`",
        f"- Live shadow activation review ready: `{promotion_bridge.get('attack_challenger_live_shadow_activation_review_ready', False)}`",
        f"- Live shadow activation review lane: `{promotion_bridge.get('attack_challenger_live_shadow_activation_review_lane', '')}`",
        f"- Live candidate entry ready: `{promotion_bridge.get('attack_challenger_live_candidate_entry_ready', False)}`",
        f"- Live candidate entry lane: `{promotion_bridge.get('attack_challenger_live_candidate_entry_lane', '')}`",
        f"- Live operator paper entry ready: `{promotion_bridge.get('attack_challenger_live_operator_paper_entry_ready', False)}`",
        f"- Live operator paper entry lane: `{promotion_bridge.get('attack_challenger_live_operator_paper_entry_lane', '')}`",
        f"- Live shadow governance review ready: `{promotion_bridge.get('attack_challenger_live_shadow_governance_review_ready', False)}`",
        f"- Live shadow governance review lane: `{promotion_bridge.get('attack_challenger_live_shadow_governance_review_lane', '')}`",
        f"- Live governed shadow entry ready: `{promotion_bridge.get('attack_challenger_live_governed_shadow_entry_ready', False)}`",
        f"- Live governed shadow entry lane: `{promotion_bridge.get('attack_challenger_live_governed_shadow_entry_lane', '')}`",
        f"- Live shadow candidate paper review ready: `{promotion_bridge.get('attack_challenger_live_shadow_candidate_paper_review_ready', False)}`",
        f"- Live shadow candidate paper review lane: `{promotion_bridge.get('attack_challenger_live_shadow_candidate_paper_review_lane', '')}`",
        f"- Live shadow candidate governance lock ready: `{promotion_bridge.get('attack_challenger_live_shadow_candidate_governance_lock_ready', False)}`",
        f"- Live shadow candidate governance lock lane: `{promotion_bridge.get('attack_challenger_live_shadow_candidate_governance_lock_lane', '')}`",
        f"- Live shadow locked entry ready: `{promotion_bridge.get('attack_challenger_live_shadow_locked_entry_ready', False)}`",
        f"- Live shadow locked entry lane: `{promotion_bridge.get('attack_challenger_live_shadow_locked_entry_lane', '')}`",
        f"- Live shadow locked candidate review ready: `{promotion_bridge.get('attack_challenger_live_shadow_locked_candidate_review_ready', False)}`",
        f"- Live shadow locked candidate review lane: `{promotion_bridge.get('attack_challenger_live_shadow_locked_candidate_review_lane', '')}`",
        f"- Live shadow locked candidate release review ready: `{promotion_bridge.get('attack_challenger_live_shadow_locked_candidate_release_review_ready', False)}`",
        f"- Live shadow locked candidate release review lane: `{promotion_bridge.get('attack_challenger_live_shadow_locked_candidate_release_review_lane', '')}`",
        f"- Live shadow locked release entry ready: `{promotion_bridge.get('attack_challenger_live_shadow_locked_release_entry_ready', False)}`",
        f"- Live shadow locked release entry lane: `{promotion_bridge.get('attack_challenger_live_shadow_locked_release_entry_lane', '')}`",
        f"- Live shadow locked release candidate review ready: `{promotion_bridge.get('attack_challenger_live_shadow_locked_release_candidate_review_ready', False)}`",
        f"- Live shadow locked release candidate review lane: `{promotion_bridge.get('attack_challenger_live_shadow_locked_release_candidate_review_lane', '')}`",
        f"- Live shadow locked release governance check ready: `{promotion_bridge.get('attack_challenger_live_shadow_locked_release_governance_check_ready', False)}`",
        f"- Live shadow locked release governance check lane: `{promotion_bridge.get('attack_challenger_live_shadow_locked_release_governance_check_lane', '')}`",
        f"- Live shadow locked release governance entry ready: `{promotion_bridge.get('attack_challenger_live_shadow_locked_release_governance_entry_ready', False)}`",
        f"- Live shadow locked release governance entry lane: `{promotion_bridge.get('attack_challenger_live_shadow_locked_release_governance_entry_lane', '')}`",
        f"- Remote monitoring deployment handoff ready: `{promotion_bridge.get('attack_challenger_remote_monitoring_deployment_handoff_ready', False)}`",
        f"- Remote monitoring deployment handoff lane: `{promotion_bridge.get('attack_challenger_remote_monitoring_deployment_handoff_lane', '')}`",
        f"- Next step: `{promotion_bridge['attack_challenger_next_step']}`",
        (
            f"- Challenger profile: `cagr={promotion_bridge['attack_challenger_paper_validation_cagr']} | "
            f"mdd={promotion_bridge['attack_challenger_paper_validation_max_drawdown']} | "
            f"drift={promotion_bridge['attack_challenger_walk_forward_sensitivity_max_drift']} | "
            f"friction={promotion_bridge['attack_challenger_friction_final_decision']}`"
        ),
        "",
        "## Hold36 Local Ceiling",
        f"- Active: `{hold36_local_ceiling['active']}`",
        f"- Attack main: `{hold36_local_ceiling['attack_main']}`",
        f"- Active backup: `{hold36_local_ceiling['active_backup']}`",
        f"- Monitoring candidate: `{hold36_local_ceiling['monitoring_candidate']}`",
        f"- Status band: `{hold36_local_ceiling['status_band']}`",
        f"- Ceiling confirmed: `{hold36_local_ceiling['ceiling_confirmed']}`",
        f"- Primary blocker: `{hold36_local_ceiling['primary_blocker']}`",
        f"- Remaining base cagr gap to open: `{hold36_local_ceiling['remaining_base_cagr_gap_to_open']}`",
        f"- Remaining cost20 cagr gap to open: `{hold36_local_ceiling['remaining_cost20_cagr_gap_to_open']}`",
        f"- Do not repeat local loop: `{hold36_local_ceiling['do_not_repeat_local_loop']}`",
        f"- Next step now: `{hold36_local_ceiling['next_step_now']}`",
        f"- Closed local axes: `{' | '.join(hold36_local_ceiling['closed_local_axes'])}`",
        (
            f"- Relative edge vs main: `base_gap={hold36_local_ceiling['base_cagr_gap_to_main']} | "
            f"cost20_gap={hold36_local_ceiling['cost20_cagr_gap_to_main']} | "
            f"sharpe_edge={hold36_local_ceiling['sharpe_edge_vs_main']} | "
            f"mdd_improvement={hold36_local_ceiling['mdd_improvement_vs_main']} | "
            f"drift_improvement={hold36_local_ceiling['drift_improvement_vs_main']}`"
        ),
        "",
        "## Performance",
        f"- Carry: `{performance['carry_decision']}` | sharpe `{performance['carry_sharpe']}` | cagr `{performance['carry_cagr']}` | mdd `{performance['carry_max_drawdown']}`",
        f"- Survivability: `{performance['survivability_decision']}` | sharpe `{performance['survivability_sharpe']}` | cagr `{performance['survivability_cagr']}` | mdd `{performance['survivability_max_drawdown']}`",
        f"- Walk-forward: `passed={performance['walk_forward_passed']}` | oos_sharpe `{performance['walk_forward_oos_sharpe']}` | oos_cagr `{performance['walk_forward_oos_cagr']}` | oos_mdd `{performance['walk_forward_oos_max_drawdown']}`",
        f"- Friction: `{performance['friction_decision']}` | bps `{performance['friction_heaviest_level_bps']}` | sharpe `{performance['friction_heaviest_level_sharpe']}`",
        f"- ETH cross-check: `{performance['eth_symbol']}` | pass_rate `{performance['eth_pass_rate']}`",
        "",
        "## Overview",
        f"- Combined health: `{overview['combined_health_line']}`",
        f"- Research stack: `{overview['research_stack_status']}`",
        f"- Contract health line: `{overview['contract_health_line']}`",
        f"- Execution contract health: `{overview['execution_contract_health_line']}`",
        f"- Execution contract read: `{overview['execution_contract_read']}`",
        "",
        "## Paper Execution",
        f"- Paper execution read: `{paper['paper_execution_read']}`",
        f"- intent_count: `{paper['intent_count']}`",
        f"- signed_request_count: `{paper['signed_request_count']}`",
        f"- paper_applied_count: `{paper['paper_applied_count']}`",
        f"- paper_duplicate_count: `{paper['paper_duplicate_count']}`",
        f"- paper_closed_count: `{paper['paper_closed_count']}`",
        f"- paper_open_count: `{paper['paper_open_count']}`",
        f"- paper_ledger_snapshot_read: `{paper['paper_ledger_snapshot_read']}`",
        "",
        "## Contracts",
        f"- quick_read_operating_contract_aligned: `{contracts['quick_read_operating_contract_aligned']}`",
        f"- quick_read_paper_execution_contract_aligned: `{contracts['quick_read_paper_execution_contract_aligned']}`",
        f"- quick_read_contract_health_aligned: `{contracts['quick_read_contract_health_aligned']}`",
        (
            "- execution_contract_paper_ledger_snapshot_summary_aligned: "
            f"`{contracts['execution_contract_paper_ledger_snapshot_summary_aligned']}`"
        ),
        (
            "- execution_contract_paper_execution_contract_aligned_summary_aligned: "
            f"`{contracts['execution_contract_paper_execution_contract_aligned_summary_aligned']}`"
        ),
        "",
        "## Artifacts",
        f"- latest_summary_json: `{artifacts['latest_summary_json']}`",
        f"- operating_index_json: `{artifacts['operating_index_json']}`",
        f"- operating_brief_json: `{artifacts['operating_brief_json']}`",
        f"- quick_read_contract_json: `{artifacts['quick_read_contract_json']}`",
        f"- execution_contract_json: `{artifacts['execution_contract_json']}`",
        f"- paper_nightly_summary_json: `{artifacts['paper_nightly_summary_json']}`",
        f"- attack_challenger_bridge_report_json: `{artifacts['attack_challenger_bridge_report_json']}`",
        f"- hold36_local_ceiling_json: `{artifacts['hold36_local_ceiling_json']}`",
        "",
        "## Attention",
    ]
    if attention_flags:
        lines.extend(f"- {flag}" for flag in attention_flags)
    else:
        lines.append("- none")
    return "\n".join(lines)


def _badge(value: bool) -> str:
    return "ok" if value else "alert"


def _render_html_list(items: list[str]) -> str:
    if not items:
        return "<li>none</li>"
    return "".join(f"<li>{html.escape(item)}</li>" for item in items)


def render_html(payload: dict[str, Any]) -> str:
    summary = payload["dashboard_summary"]
    development = payload["development"]
    performance = payload["performance"]
    promotion_bridge = payload["promotion_bridge"]
    hold36_local_ceiling = payload["hold36_local_ceiling"]
    overview = payload["overview"]
    paper = payload["paper_execution"]
    contracts = payload["contracts"]
    artifacts = payload["artifacts"]
    attention_flags = summary.get("attention_flags", [])
    title = "BTC 1d Operator Dashboard"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --bg: #f4f1ea;
      --panel: #fffdf8;
      --ink: #1f2937;
      --muted: #6b7280;
      --line: #d6d3d1;
      --ok: #1d6b57;
      --ok-bg: #dff5ea;
      --alert: #9a3412;
      --alert-bg: #fde7d8;
      --accent: #0f4c5c;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "Noto Sans KR", sans-serif;
      background: linear-gradient(180deg, #efe9de 0%, var(--bg) 100%);
      color: var(--ink);
    }}
    .wrap {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px;
    }}
    .hero {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 24px;
      margin-bottom: 20px;
      box-shadow: 0 10px 30px rgba(15, 76, 92, 0.08);
    }}
    .title {{
      margin: 0 0 8px;
      font-size: 32px;
      line-height: 1.1;
    }}
    .subtitle {{
      margin: 0;
      color: var(--muted);
      font-size: 15px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
    }}
    h2 {{
      margin: 0 0 12px;
      font-size: 18px;
      color: var(--accent);
    }}
    .metric {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 8px 0;
      border-top: 1px solid #ece8e1;
    }}
    .metric:first-of-type {{ border-top: 0; }}
    .k {{ color: var(--muted); }}
    .v {{
      text-align: right;
      word-break: break-word;
      font-weight: 600;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.02em;
    }}
    .ok {{ color: var(--ok); background: var(--ok-bg); }}
    .alert {{ color: var(--alert); background: var(--alert-bg); }}
    ul {{
      margin: 0;
      padding-left: 18px;
    }}
    li {{
      margin: 6px 0;
    }}
    code {{
      font-family: Consolas, monospace;
      font-size: 12px;
      background: #f3f4f6;
      padding: 2px 6px;
      border-radius: 6px;
      word-break: break-all;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1 class="title">{html.escape(title)}</h1>
      <p class="subtitle">Candidate: <strong>{html.escape(str(summary['candidate']))}</strong> | Shadow decision: <strong>{html.escape(str(summary['shadow_decision']))}</strong></p>
      <div style="margin-top:14px;">
        <span class="badge {_badge(bool(summary['dashboard_ready']))}">dashboard_ready={html.escape(str(summary['dashboard_ready']))}</span>
        <span class="badge {_badge(bool(summary.get('deployment_monitoring_active', False)))}">deployment_monitoring_active={html.escape(str(summary.get('deployment_monitoring_active', False)))}</span>
        <span class="badge {_badge(str(summary['operator_verdict']) == 'ready' or str(summary['operator_verdict']) == 'shadow_monitoring_ready')}">operator_verdict={html.escape(str(summary['operator_verdict']))}</span>
      </div>
    </section>
    <section class="grid">
      <div class="card">
        <h2>Status</h2>
        <div class="metric"><span class="k">Practical status</span><span class="v">{html.escape(str(summary['practical_status_label']))}</span></div>
        <div class="metric"><span class="k">Quick-read partitioned</span><span class="v"><span class="badge {_badge(bool(summary['quick_read_contract_partitioned']))}">{html.escape(str(summary['quick_read_contract_partitioned']))}</span></span></div>
        <div class="metric"><span class="k">Contract health aligned</span><span class="v"><span class="badge {_badge(bool(summary['contract_health_aligned']))}">{html.escape(str(summary['contract_health_aligned']))}</span></span></div>
        <div class="metric"><span class="k">Execution contract aligned</span><span class="v"><span class="badge {_badge(bool(summary['execution_contract_aligned']))}">{html.escape(str(summary['execution_contract_aligned']))}</span></span></div>
      </div>
      <div class="card">
        <h2>Paper Execution</h2>
        <div class="metric"><span class="k">Paper execution contract aligned</span><span class="v"><span class="badge {_badge(bool(summary['paper_execution_contract_aligned']))}">{html.escape(str(summary['paper_execution_contract_aligned']))}</span></span></div>
        <div class="metric"><span class="k">Paper ledger consistent</span><span class="v"><span class="badge {_badge(bool(summary['paper_ledger_consistent']))}">{html.escape(str(summary['paper_ledger_consistent']))}</span></span></div>
        <div class="metric"><span class="k">Paper exit duplicate run</span><span class="v">{html.escape(str(summary['paper_exit_duplicate_run']))}</span></div>
        <div class="metric"><span class="k">Paper execution read</span><span class="v">{html.escape(str(paper['paper_execution_read']))}</span></div>
      </div>
      <div class="card">
        <h2>Development</h2>
        <div class="metric"><span class="k">Project direction</span><span class="v">{html.escape(str(development['project_direction']))}</span></div>
        <div class="metric"><span class="k">Current work</span><span class="v">{html.escape(" | ".join(development['current_work']))}</span></div>
        <div class="metric"><span class="k">Next actions</span><span class="v">{html.escape(" | ".join(development['next_actions']))}</span></div>
      </div>
      <div class="card">
        <h2>Promotion Bridge</h2>
        <div class="metric"><span class="k">Attack challenger</span><span class="v">{html.escape(str(promotion_bridge['attack_challenger_candidate']))}</span></div>
        <div class="metric"><span class="k">Role assignment</span><span class="v">{html.escape(str(promotion_bridge['attack_challenger_role_assignment']))}</span></div>
        <div class="metric"><span class="k">Promotion ready</span><span class="v">{html.escape(str(promotion_bridge['attack_challenger_promotion_ready']))}</span></div>
        <div class="metric"><span class="k">Bridge entry ready</span><span class="v">{html.escape(str(promotion_bridge['attack_challenger_bridge_entry_ready']))}</span></div>
        <div class="metric"><span class="k">Queue lane</span><span class="v">{html.escape(str(promotion_bridge['attack_challenger_bridge_queue_lane']))}</span></div>
        <div class="metric"><span class="k">Execution contract entry ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_execution_contract_entry_ready', False)))}</span></div>
        <div class="metric"><span class="k">Execution contract queue lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_execution_contract_queue_lane', '')))}</span></div>
        <div class="metric"><span class="k">Operator stack handoff ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_operator_stack_handoff_ready', False)))}</span></div>
        <div class="metric"><span class="k">Operator stack handoff lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_operator_stack_handoff_lane', '')))}</span></div>
        <div class="metric"><span class="k">Operator runbook candidate entry ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_operator_runbook_candidate_entry_ready', False)))}</span></div>
        <div class="metric"><span class="k">Operator runbook candidate lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_operator_runbook_candidate_entry_lane', '')))}</span></div>
        <div class="metric"><span class="k">Operator runbook execution entry ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_operator_runbook_execution_entry_ready', False)))}</span></div>
        <div class="metric"><span class="k">Operator runbook execution lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_operator_runbook_execution_entry_lane', '')))}</span></div>
        <div class="metric"><span class="k">Live readiness review ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_readiness_review_ready', False)))}</span></div>
        <div class="metric"><span class="k">Live readiness review lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_readiness_review_lane', '')))}</span></div>
        <div class="metric"><span class="k">Live shadow activation review ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_activation_review_ready', False)))}</span></div>
        <div class="metric"><span class="k">Live shadow activation review lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_activation_review_lane', '')))}</span></div>
        <div class="metric"><span class="k">Live candidate entry ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_candidate_entry_ready', False)))}</span></div>
        <div class="metric"><span class="k">Live candidate entry lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_candidate_entry_lane', '')))}</span></div>
        <div class="metric"><span class="k">Live operator paper entry ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_operator_paper_entry_ready', False)))}</span></div>
        <div class="metric"><span class="k">Live operator paper entry lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_operator_paper_entry_lane', '')))}</span></div>
        <div class="metric"><span class="k">Live shadow governance review ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_governance_review_ready', False)))}</span></div>
        <div class="metric"><span class="k">Live shadow governance review lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_governance_review_lane', '')))}</span></div>
        <div class="metric"><span class="k">Live governed shadow entry ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_governed_shadow_entry_ready', False)))}</span></div>
        <div class="metric"><span class="k">Live governed shadow entry lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_governed_shadow_entry_lane', '')))}</span></div>
        <div class="metric"><span class="k">Live shadow candidate paper review ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_candidate_paper_review_ready', False)))}</span></div>
        <div class="metric"><span class="k">Live shadow candidate paper review lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_candidate_paper_review_lane', '')))}</span></div>
        <div class="metric"><span class="k">Live shadow candidate governance lock ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_candidate_governance_lock_ready', False)))}</span></div>
        <div class="metric"><span class="k">Live shadow candidate governance lock lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_candidate_governance_lock_lane', '')))}</span></div>
        <div class="metric"><span class="k">Live shadow locked entry ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_locked_entry_ready', False)))}</span></div>
        <div class="metric"><span class="k">Live shadow locked entry lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_locked_entry_lane', '')))}</span></div>
        <div class="metric"><span class="k">Live shadow locked candidate review ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_locked_candidate_review_ready', False)))}</span></div>
        <div class="metric"><span class="k">Live shadow locked candidate review lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_locked_candidate_review_lane', '')))}</span></div>
        <div class="metric"><span class="k">Live shadow locked candidate release review ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_locked_candidate_release_review_ready', False)))}</span></div>
        <div class="metric"><span class="k">Live shadow locked candidate release review lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_locked_candidate_release_review_lane', '')))}</span></div>
        <div class="metric"><span class="k">Live shadow locked release entry ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_locked_release_entry_ready', False)))}</span></div>
        <div class="metric"><span class="k">Live shadow locked release entry lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_locked_release_entry_lane', '')))}</span></div>
        <div class="metric"><span class="k">Live shadow locked release candidate review ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_locked_release_candidate_review_ready', False)))}</span></div>
        <div class="metric"><span class="k">Live shadow locked release candidate review lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_locked_release_candidate_review_lane', '')))}</span></div>
        <div class="metric"><span class="k">Live shadow locked release governance check ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_locked_release_governance_check_ready', False)))}</span></div>
        <div class="metric"><span class="k">Live shadow locked release governance check lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_locked_release_governance_check_lane', '')))}</span></div>
        <div class="metric"><span class="k">Live shadow locked release governance entry ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_locked_release_governance_entry_ready', False)))}</span></div>
        <div class="metric"><span class="k">Live shadow locked release governance entry lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_live_shadow_locked_release_governance_entry_lane', '')))}</span></div>
        <div class="metric"><span class="k">Remote monitoring deployment handoff ready</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_remote_monitoring_deployment_handoff_ready', False)))}</span></div>
        <div class="metric"><span class="k">Remote monitoring deployment handoff lane</span><span class="v">{html.escape(str(promotion_bridge.get('attack_challenger_remote_monitoring_deployment_handoff_lane', '')))}</span></div>
        <div class="metric"><span class="k">Next step</span><span class="v">{html.escape(str(promotion_bridge['attack_challenger_next_step']))}</span></div>
        <div class="metric"><span class="k">Challenger profile</span><span class="v">cagr={html.escape(str(promotion_bridge['attack_challenger_paper_validation_cagr']))} | mdd={html.escape(str(promotion_bridge['attack_challenger_paper_validation_max_drawdown']))} | drift={html.escape(str(promotion_bridge['attack_challenger_walk_forward_sensitivity_max_drift']))} | friction={html.escape(str(promotion_bridge['attack_challenger_friction_final_decision']))}</span></div>
      </div>
      <div class="card">
        <h2>Performance</h2>
        <div class="metric"><span class="k">Carry</span><span class="v">{html.escape(str(performance['carry_decision']))} | sharpe={html.escape(str(performance['carry_sharpe']))} | cagr={html.escape(str(performance['carry_cagr']))}</span></div>
        <div class="metric"><span class="k">Survivability</span><span class="v">{html.escape(str(performance['survivability_decision']))} | sharpe={html.escape(str(performance['survivability_sharpe']))} | cagr={html.escape(str(performance['survivability_cagr']))}</span></div>
        <div class="metric"><span class="k">Walk-forward</span><span class="v">passed={html.escape(str(performance['walk_forward_passed']))} | oos_sharpe={html.escape(str(performance['walk_forward_oos_sharpe']))}</span></div>
        <div class="metric"><span class="k">Friction</span><span class="v">{html.escape(str(performance['friction_decision']))} | bps={html.escape(str(performance['friction_heaviest_level_bps']))}</span></div>
        <div class="metric"><span class="k">ETH cross-check</span><span class="v">{html.escape(str(performance['eth_symbol']))} | pass_rate={html.escape(str(performance['eth_pass_rate']))}</span></div>
      </div>
      <div class="card">
        <h2>Hold36 Local Ceiling</h2>
        <div class="metric"><span class="k">Active</span><span class="v">{html.escape(str(hold36_local_ceiling['active']))}</span></div>
        <div class="metric"><span class="k">Attack main</span><span class="v">{html.escape(str(hold36_local_ceiling['attack_main']))}</span></div>
        <div class="metric"><span class="k">Active backup</span><span class="v">{html.escape(str(hold36_local_ceiling['active_backup']))}</span></div>
        <div class="metric"><span class="k">Monitoring candidate</span><span class="v">{html.escape(str(hold36_local_ceiling['monitoring_candidate']))}</span></div>
        <div class="metric"><span class="k">Status band</span><span class="v">{html.escape(str(hold36_local_ceiling['status_band']))}</span></div>
        <div class="metric"><span class="k">Ceiling confirmed</span><span class="v">{html.escape(str(hold36_local_ceiling['ceiling_confirmed']))}</span></div>
        <div class="metric"><span class="k">Primary blocker</span><span class="v">{html.escape(str(hold36_local_ceiling['primary_blocker']))}</span></div>
        <div class="metric"><span class="k">Remaining base gap</span><span class="v">{html.escape(str(hold36_local_ceiling['remaining_base_cagr_gap_to_open']))}</span></div>
        <div class="metric"><span class="k">Remaining cost20 gap</span><span class="v">{html.escape(str(hold36_local_ceiling['remaining_cost20_cagr_gap_to_open']))}</span></div>
        <div class="metric"><span class="k">Do not repeat local loop</span><span class="v">{html.escape(str(hold36_local_ceiling['do_not_repeat_local_loop']))}</span></div>
        <div class="metric"><span class="k">Next step</span><span class="v">{html.escape(str(hold36_local_ceiling['next_step_now']))}</span></div>
        <div class="metric"><span class="k">Closed local axes</span><span class="v">{html.escape(" | ".join(hold36_local_ceiling['closed_local_axes']))}</span></div>
      </div>
      <div class="card">
        <h2>Overview</h2>
        <div class="metric"><span class="k">Combined health</span><span class="v">{html.escape(str(overview['combined_health_line']))}</span></div>
        <div class="metric"><span class="k">Research stack</span><span class="v">{html.escape(str(overview['research_stack_status']))}</span></div>
        <div class="metric"><span class="k">Contract health</span><span class="v">{html.escape(str(overview['contract_health_line']))}</span></div>
        <div class="metric"><span class="k">Execution contract read</span><span class="v">{html.escape(str(overview['execution_contract_read']))}</span></div>
      </div>
      <div class="card">
        <h2>Counts</h2>
        <div class="metric"><span class="k">intent_count</span><span class="v">{html.escape(str(paper['intent_count']))}</span></div>
        <div class="metric"><span class="k">signed_request_count</span><span class="v">{html.escape(str(paper['signed_request_count']))}</span></div>
        <div class="metric"><span class="k">paper_applied_count</span><span class="v">{html.escape(str(paper['paper_applied_count']))}</span></div>
        <div class="metric"><span class="k">paper_duplicate_count</span><span class="v">{html.escape(str(paper['paper_duplicate_count']))}</span></div>
        <div class="metric"><span class="k">paper_closed_count</span><span class="v">{html.escape(str(paper['paper_closed_count']))}</span></div>
        <div class="metric"><span class="k">paper_open_count</span><span class="v">{html.escape(str(paper['paper_open_count']))}</span></div>
      </div>
      <div class="card">
        <h2>Contracts</h2>
        <div class="metric"><span class="k">quick_read_operating_contract_aligned</span><span class="v">{html.escape(str(contracts['quick_read_operating_contract_aligned']))}</span></div>
        <div class="metric"><span class="k">quick_read_paper_execution_contract_aligned</span><span class="v">{html.escape(str(contracts['quick_read_paper_execution_contract_aligned']))}</span></div>
        <div class="metric"><span class="k">quick_read_contract_health_aligned</span><span class="v">{html.escape(str(contracts['quick_read_contract_health_aligned']))}</span></div>
        <div class="metric"><span class="k">execution_contract_paper_ledger_snapshot_summary_aligned</span><span class="v">{html.escape(str(contracts['execution_contract_paper_ledger_snapshot_summary_aligned']))}</span></div>
        <div class="metric"><span class="k">execution_contract_paper_execution_contract_aligned_summary_aligned</span><span class="v">{html.escape(str(contracts['execution_contract_paper_execution_contract_aligned_summary_aligned']))}</span></div>
      </div>
      <div class="card">
        <h2>Attention</h2>
        <ul>{_render_html_list(attention_flags)}</ul>
      </div>
    </section>
    <section class="card">
      <h2>Artifacts</h2>
      <ul>
        <li><code>{html.escape(str(artifacts['latest_summary_json']))}</code></li>
        <li><code>{html.escape(str(artifacts['operating_index_json']))}</code></li>
        <li><code>{html.escape(str(artifacts['operating_brief_json']))}</code></li>
        <li><code>{html.escape(str(artifacts['quick_read_contract_json']))}</code></li>
        <li><code>{html.escape(str(artifacts['execution_contract_json']))}</code></li>
        <li><code>{html.escape(str(artifacts['paper_nightly_summary_json']))}</code></li>
        <li><code>{html.escape(str(artifacts['attack_challenger_bridge_report_json']))}</code></li>
        <li><code>{html.escape(str(artifacts['hold36_local_ceiling_json']))}</code></li>
      </ul>
    </section>
  </div>
</body>
</html>"""


def _write_latest_aliases(json_path: Path, md_path: Path, html_path: Path) -> dict[str, str]:
    latest_json = json_path.with_name("btc_1d_operator_dashboard_latest.json")
    latest_md = md_path.with_name("btc_1d_operator_dashboard_md_latest.md")
    latest_html = html_path.with_name("btc_1d_operator_dashboard_html_latest.html")
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_html.write_text(html_path.read_text(encoding="utf-8"), encoding="utf-8")
    return {
        "btc_1d_operator_dashboard": str(latest_json),
        "btc_1d_operator_dashboard_md": str(latest_md),
        "btc_1d_operator_dashboard_html": str(latest_html),
    }


def main() -> int:
    report = build_dashboard(ANALYSIS_DIR)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_operator_dashboard_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_operator_dashboard_{stamp}.md"
    html_path = ANALYSIS_DIR / f"btc_1d_operator_dashboard_{stamp}.html"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    latest_aliases = _write_latest_aliases(json_path, md_path, html_path)
    print(
        json.dumps(
            {
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "report_html_path": str(html_path),
                "latest_aliases": latest_aliases,
                "report": report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
