from __future__ import annotations

import json
from pathlib import Path

from scripts.btc_1d_handoff_constants import (
    ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE,
)
from scripts.build_btc_1d_operator_dashboard import (
    _write_latest_aliases,
    build_dashboard,
    render_html,
    render_markdown,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_build_dashboard_collects_latest_operator_artifacts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"

    _write_json(
        analysis_dir / "btc_1d_latest_summary_latest.json",
        {
            "candidate": "btc_1d_prod_candidate",
            "shadow_decision": "ready",
            "carry": {
                "decision": "pass",
                "sharpe": 1.25,
                "cagr": 0.31,
                "max_drawdown": 0.12,
            },
            "survivability": {
                "decision": "pass",
                "sharpe": 1.11,
                "cagr": 0.24,
                "max_drawdown": 0.13,
            },
            "walk_forward": {
                "passed": True,
                "oos_sharpe": 0.88,
                "oos_cagr": 0.17,
                "oos_max_drawdown": 0.15,
            },
            "friction": {
                "decision": "pass",
                "heaviest_level_bps": 16,
                "heaviest_level_sharpe": 0.77,
            },
            "eth_cross_check": {
                "symbol": "ETHUSDT",
                "pass_rate": 0.75,
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "practical_status_label": "carryable_candidate",
            "combined_health_line": "practical || research || contract",
            "research_stack_status": "research healthy",
            "execution_contract_health_line": "execution health || execution contract",
            "execution_contract_read": "execution contract | aligned | paper execution",
            "paper_execution_read": "paper execution | track=operating | applied=1 | closed=1 | open=0",
            "paper_execution_contract_aligned": True,
            "paper_exit_duplicate_run": False,
            "paper_ledger_consistent": True,
            "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
            "contract_health_aligned": True,
            "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit",
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": True,
            "attack_challenger_bridge_entry_ready": True,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue",
            "attack_challenger_execution_contract_entry_ready": True,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue",
            "attack_challenger_operator_stack_handoff_ready": True,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue",
            "attack_challenger_operator_runbook_candidate_entry_ready": True,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue",
            "attack_challenger_operator_runbook_execution_entry_ready": True,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue",
            "attack_challenger_live_readiness_review_ready": True,
            "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue",
            "attack_challenger_live_shadow_activation_review_ready": True,
            "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue",
            "attack_challenger_live_candidate_entry_ready": True,
            "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue",
            "attack_challenger_live_operator_paper_entry_ready": True,
            "attack_challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue",
            "attack_challenger_live_shadow_governance_review_ready": True,
            "attack_challenger_live_shadow_governance_review_lane": "challenger_live_shadow_governance_queue",
            "attack_challenger_live_governed_shadow_entry_ready": True,
            "attack_challenger_live_governed_shadow_entry_lane": "challenger_live_governed_shadow_queue",
            "attack_challenger_live_shadow_candidate_paper_review_ready": True,
            "attack_challenger_live_shadow_candidate_paper_review_lane": "challenger_live_shadow_candidate_paper_queue",
            "attack_challenger_live_shadow_candidate_governance_lock_ready": True,
            "attack_challenger_live_shadow_candidate_governance_lock_lane": "challenger_live_shadow_candidate_governance_lock_queue",
            "attack_challenger_live_shadow_locked_entry_ready": True,
            "attack_challenger_live_shadow_locked_entry_lane": "challenger_live_shadow_locked_queue",
            "attack_challenger_live_shadow_locked_candidate_review_ready": True,
            "attack_challenger_live_shadow_locked_candidate_review_lane": "challenger_live_shadow_locked_candidate_review_queue",
            "attack_challenger_live_shadow_locked_candidate_release_review_ready": True,
            "attack_challenger_live_shadow_locked_candidate_release_review_lane": "challenger_live_shadow_locked_candidate_release_review_queue",
            "attack_challenger_live_shadow_locked_release_entry_ready": True,
            "attack_challenger_live_shadow_locked_release_entry_lane": "challenger_live_shadow_locked_release_queue",
            "attack_challenger_live_shadow_locked_release_candidate_review_ready": True,
            "attack_challenger_live_shadow_locked_release_candidate_review_lane": "challenger_live_shadow_locked_release_candidate_review_queue",
            "attack_challenger_live_shadow_locked_release_governance_check_ready": True,
            "attack_challenger_live_shadow_locked_release_governance_check_lane": "challenger_live_shadow_locked_release_governance_check_queue",
            "attack_challenger_next_step": "challenger_live_shadow_locked_release_governance_entry",
            "attack_challenger_paper_validation_cagr": 0.2712,
            "attack_challenger_paper_validation_max_drawdown": 0.16,
            "attack_challenger_walk_forward_sensitivity_max_drift": 0.0928,
            "attack_challenger_friction_final_decision": "continue",
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_promotion_bridge_latest.json",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "contract_health_line": "BTC 1d contract health | aligned=True",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_quick_read_contract_screen_latest.json",
        {
            "contract_summary": {
                "operating_contract_aligned": True,
                "paper_execution_contract_aligned": True,
                "contract_health_aligned": True,
            },
            "contract_verdict": {
                "contracts_are_well_partitioned": True,
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_contract_screen_latest.json",
        {
            "execution_contract_summary": {
                "execution_contract_health_line": "execution health || execution contract",
                "execution_contract_read": "execution contract | aligned | paper execution",
                "paper_ledger_snapshot_summary_aligned": True,
                "paper_execution_contract_aligned_summary_aligned": True,
            },
            "execution_contract_verdict": {
                "execution_contract_aligned": True,
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "intent_count": 1,
            "signed_request_count": 1,
            "paper_applied_count": 1,
            "paper_duplicate_count": 0,
            "paper_closed_count": 1,
            "paper_open_count": 0,
            "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "operating_brief": {
                "attack_frontier": "ratio112_tighter_stop_main",
                "attack_backup": "bridge_28_relief",
                "attack_challenger": "post_spike_trend960_depth055_volume100_hold36",
                "highest_priority_near_miss": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
            },
            "models": {
                "attack_main": {"base_cagr": 0.4243, "base_mdd": 0.1609, "base_sharpe": 1.5613},
                "attack_backup": {"sensitivity_max_drift": 0.1322},
                "attack_challenger": {"stack_read": "active_post_spike_challenger", "base_cagr": 0.3078},
                "highest_priority_near_miss": {"candidate_stage_status": "validated_fail_hold"},
            },
            "local_ceiling": {
                "status_band": "pressure_watch",
                "primary_blocker": "base_cagr_gap",
                "do_not_repeat_local_loop": True,
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_hold36_local_ceiling_handoff_latest.json",
        {
            "handoff_reference": {
                "attack_main": "ratio112_tighter_stop_main",
                "active_backup": "post_spike_trend92_depth058_volume105_hold36",
                "monitoring_candidate": "post_spike_trend92_depth058_volume105_hold36",
            },
            "local_ceiling_status": {
                "status_band": "pressure_watch",
                "ceiling_confirmed": True,
                "primary_blocker": "base_cagr_gap",
                "remaining_base_cagr_gap_to_open": 0.03788175,
                "remaining_cost20_cagr_gap_to_open": 0.0,
                "closed_local_axes": [
                    "challenger_reopen",
                    "base_gap_recovery",
                    "entry_timing",
                    "entry_strength",
                    "structure",
                ],
                "do_not_repeat_local_loop": True,
                "next_step_now": "open_only_new_family_or_wider_frame_search",
            },
            "handoff_metrics": {
                "base_cagr_gap_to_main": 0.07788175,
                "cost20_cagr_gap_to_main": 0.05723624,
                "sharpe_edge_vs_main": 0.25185224,
                "mdd_improvement_vs_main": 0.06568218,
                "drift_improvement_vs_main": 0.20381937,
            },
        },
    )

    report = build_dashboard(analysis_dir)

    assert report["dashboard_summary"]["dashboard_ready"] is True
    assert report["dashboard_summary"]["deployment_monitoring_active"] is False
    assert report["dashboard_summary"]["operator_verdict"] == "ready"
    assert report["dashboard_summary"]["candidate"] == "btc_1d_prod_candidate"
    assert report["dashboard_summary"]["quick_read_contract_partitioned"] is True
    assert report["dashboard_summary"]["contract_health_aligned"] is True
    assert report["dashboard_summary"]["execution_contract_aligned"] is True
    assert report["dashboard_summary"]["paper_ledger_consistent"] is True
    assert report["dashboard_summary"]["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert report["dashboard_summary"]["attack_challenger_promotion_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_bridge_entry_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_execution_contract_entry_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_operator_stack_handoff_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_operator_runbook_candidate_entry_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_operator_runbook_execution_entry_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_live_readiness_review_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_live_shadow_activation_review_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_live_candidate_entry_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_live_operator_paper_entry_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_live_shadow_governance_review_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_live_governed_shadow_entry_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_live_shadow_candidate_paper_review_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_live_shadow_candidate_governance_lock_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_live_shadow_locked_entry_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_live_shadow_locked_candidate_review_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_live_shadow_locked_candidate_release_review_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_live_shadow_locked_release_governance_check_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_live_shadow_locked_release_entry_ready"] is True
    assert report["dashboard_summary"]["attack_challenger_live_shadow_locked_release_candidate_review_ready"] is True
    assert report["development"]["project_direction"] == "model validation"
    assert "candidate=btc_1d_prod_candidate" in report["development"]["current_work"]
    assert "attack_challenger=pullthrough_asymmetric_release_tighter_exit" in report["development"]["current_work"]
    assert "hold36_backup=post_spike_trend92_depth058_volume105_hold36" in report["development"]["current_work"]
    assert "hold36_ceiling=pressure_watch/base_cagr_gap" in report["development"]["current_work"]
    assert "backup=bridge_28_relief" in report["overview"]["research_stack_status"]
    assert "challenger=post_spike_trend960_depth055_volume100_hold36" in report["overview"]["research_stack_status"]
    assert "challenger_live_shadow_locked_release_governance_entry" in report["development"]["next_actions"]
    assert report["promotion_bridge"]["attack_challenger_role_assignment"] == "attack_challenger_candidate"
    assert report["promotion_bridge"]["attack_challenger_bridge_queue_lane"] == "attack_challenger_queue"
    assert report["promotion_bridge"]["attack_challenger_execution_contract_queue_lane"] == "challenger_execution_contract_queue"
    assert report["promotion_bridge"]["attack_challenger_operator_stack_handoff_lane"] == "operator_stack_handoff_queue"
    assert report["promotion_bridge"]["attack_challenger_operator_runbook_candidate_entry_lane"] == "operator_runbook_candidate_queue"
    assert report["promotion_bridge"]["attack_challenger_operator_runbook_execution_entry_lane"] == "challenger_shadow_monitoring_queue"
    assert report["promotion_bridge"]["attack_challenger_live_readiness_review_lane"] == "challenger_live_readiness_review_queue"
    assert report["promotion_bridge"]["attack_challenger_live_shadow_activation_review_lane"] == "challenger_live_shadow_activation_queue"
    assert report["promotion_bridge"]["attack_challenger_live_candidate_entry_lane"] == "challenger_live_candidate_queue"
    assert report["promotion_bridge"]["attack_challenger_live_operator_paper_entry_lane"] == "challenger_live_operator_paper_queue"
    assert report["promotion_bridge"]["attack_challenger_live_shadow_governance_review_lane"] == "challenger_live_shadow_governance_queue"
    assert report["promotion_bridge"]["attack_challenger_live_governed_shadow_entry_lane"] == "challenger_live_governed_shadow_queue"
    assert report["promotion_bridge"]["attack_challenger_live_shadow_candidate_paper_review_lane"] == "challenger_live_shadow_candidate_paper_queue"
    assert report["promotion_bridge"]["attack_challenger_live_shadow_candidate_governance_lock_lane"] == "challenger_live_shadow_candidate_governance_lock_queue"
    assert report["promotion_bridge"]["attack_challenger_live_shadow_locked_entry_lane"] == "challenger_live_shadow_locked_queue"
    assert report["promotion_bridge"]["attack_challenger_live_shadow_locked_candidate_review_lane"] == "challenger_live_shadow_locked_candidate_review_queue"
    assert report["promotion_bridge"]["attack_challenger_live_shadow_locked_candidate_release_review_lane"] == "challenger_live_shadow_locked_candidate_release_review_queue"
    assert report["promotion_bridge"]["attack_challenger_live_shadow_locked_release_entry_lane"] == "challenger_live_shadow_locked_release_queue"
    assert report["promotion_bridge"]["attack_challenger_live_shadow_locked_release_candidate_review_lane"] == "challenger_live_shadow_locked_release_candidate_review_queue"
    assert report["promotion_bridge"]["attack_challenger_live_shadow_locked_release_governance_check_lane"] == "challenger_live_shadow_locked_release_governance_check_queue"
    assert report["promotion_bridge"]["attack_challenger_friction_final_decision"] == "continue"
    assert report["performance"]["carry_sharpe"] == 1.25
    assert report["performance"]["eth_pass_rate"] == 0.75
    assert report["hold36_local_ceiling"]["active"] is True
    assert report["hold36_local_ceiling"]["status_band"] == "pressure_watch"
    assert report["hold36_local_ceiling"]["do_not_repeat_local_loop"] is True
    assert report["paper_execution"]["paper_applied_count"] == 1
    assert report["contracts"]["quick_read_contract_health_aligned"] is True
    assert report["contracts"]["execution_contract_paper_ledger_snapshot_summary_aligned"] is True
    assert report["dashboard_summary"]["attention_flags"] == []


def test_build_dashboard_marks_shadow_monitoring_ready_as_dashboard_ready(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"

    _write_json(
        analysis_dir / "btc_1d_latest_summary_latest.json",
        {
            "candidate": "btc_1d_shadow_candidate",
            "shadow_decision": "shadow_ready_for_btc_only",
            "carry": {"decision": "pass", "sharpe": 1.1, "cagr": 0.2, "max_drawdown": 0.1},
            "survivability": {
                "decision": "pass",
                "sharpe": 1.0,
                "cagr": 0.18,
                "max_drawdown": 0.12,
            },
            "walk_forward": {
                "passed": True,
                "oos_sharpe": 0.8,
                "oos_cagr": 0.1,
                "oos_max_drawdown": 0.08,
            },
            "friction": {"decision": "continue", "heaviest_level_bps": 20, "heaviest_level_sharpe": 0.7},
            "eth_cross_check": {"symbol": "ETHUSDT", "pass_rate": 0.0},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "practical_status_label": "btc_only_practical_with_caveats",
            "combined_health_line": "practical || research || contract",
            "research_stack_status": "research healthy",
            "execution_contract_health_line": "execution health || execution contract",
            "execution_contract_read": "execution contract | aligned | paper execution",
            "paper_execution_read": "paper execution | track=operating | applied=0 | closed=0 | open=0",
            "paper_execution_contract_aligned": True,
            "paper_exit_duplicate_run": True,
            "paper_ledger_consistent": True,
            "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
            "contract_health_aligned": True,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {"contract_health_line": "BTC 1d contract health | aligned=True"},
    )
    _write_json(
        analysis_dir / "btc_1d_quick_read_contract_screen_latest.json",
        {
            "contract_summary": {
                "operating_contract_aligned": True,
                "paper_execution_contract_aligned": True,
                "contract_health_aligned": True,
            },
            "contract_verdict": {"contracts_are_well_partitioned": True},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_contract_screen_latest.json",
        {
            "execution_contract_summary": {
                "execution_contract_health_line": "execution health || execution contract",
                "execution_contract_read": "execution contract | aligned | paper execution",
                "paper_ledger_snapshot_summary_aligned": True,
                "paper_execution_contract_aligned_summary_aligned": True,
            },
            "execution_contract_verdict": {"execution_contract_aligned": True},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "intent_count": 1,
            "signed_request_count": 1,
            "paper_applied_count": 0,
            "paper_duplicate_count": 1,
            "paper_closed_count": 0,
            "paper_open_count": 0,
            "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
        },
    )

    report = build_dashboard(analysis_dir)

    assert report["dashboard_summary"]["dashboard_ready"] is True
    assert report["dashboard_summary"]["deployment_ready"] is False
    assert report["dashboard_summary"]["deployment_monitoring_active"] is False
    assert report["dashboard_summary"]["operator_verdict"] == "shadow_monitoring_ready"
    assert "shadow_decision=shadow_ready_for_btc_only" not in report["dashboard_summary"]["attention_flags"]
    assert "paper_exit_duplicate_run=true(no-op rerun)" not in report["dashboard_summary"]["attention_flags"]


def test_render_markdown_html_and_latest_aliases_for_operator_dashboard(tmp_path: Path) -> None:
    report = {
        "dashboard_summary": {
            "dashboard_ready": False,
            "operator_verdict": "ops_repair_required",
            "candidate": "btc_1d_prod_candidate",
            "shadow_decision": "hold",
            "practical_status_label": "needs_review",
            "quick_read_contract_partitioned": False,
            "contract_health_aligned": False,
            "execution_contract_aligned": False,
            "paper_execution_contract_aligned": False,
            "paper_ledger_consistent": False,
            "paper_exit_duplicate_run": True,
            "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit",
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": True,
            "attack_challenger_bridge_entry_ready": True,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue",
            "attack_challenger_execution_contract_entry_ready": True,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue",
            "attack_challenger_operator_stack_handoff_ready": True,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue",
            "attack_challenger_operator_runbook_candidate_entry_ready": True,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue",
            "attack_challenger_operator_runbook_execution_entry_ready": True,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue",
            "attack_challenger_live_readiness_review_ready": True,
            "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue",
            "attack_challenger_live_shadow_activation_review_ready": True,
            "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue",
            "attack_challenger_live_candidate_entry_ready": True,
            "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue",
            "attack_challenger_live_operator_paper_entry_ready": True,
            "attack_challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue",
            "attack_challenger_live_shadow_governance_review_ready": True,
            "attack_challenger_live_shadow_governance_review_lane": "challenger_live_shadow_governance_queue",
            "attack_challenger_live_governed_shadow_entry_ready": True,
            "attack_challenger_live_governed_shadow_entry_lane": "challenger_live_governed_shadow_queue",
            "attack_challenger_live_shadow_candidate_paper_review_ready": True,
            "attack_challenger_live_shadow_candidate_paper_review_lane": "challenger_live_shadow_candidate_paper_queue",
            "attack_challenger_live_shadow_candidate_governance_lock_ready": True,
            "attack_challenger_live_shadow_candidate_governance_lock_lane": "challenger_live_shadow_candidate_governance_lock_queue",
            "attack_challenger_live_shadow_locked_entry_ready": True,
            "attack_challenger_live_shadow_locked_entry_lane": "challenger_live_shadow_locked_queue",
            "attack_challenger_live_shadow_locked_candidate_review_ready": True,
            "attack_challenger_live_shadow_locked_candidate_review_lane": "challenger_live_shadow_locked_candidate_review_queue",
            "attack_challenger_live_shadow_locked_candidate_release_review_ready": True,
            "attack_challenger_live_shadow_locked_candidate_release_review_lane": "challenger_live_shadow_locked_candidate_release_review_queue",
            "attack_challenger_live_shadow_locked_release_entry_ready": True,
            "attack_challenger_live_shadow_locked_release_entry_lane": "challenger_live_shadow_locked_release_queue",
            "attack_challenger_live_shadow_locked_release_candidate_review_ready": True,
            "attack_challenger_live_shadow_locked_release_candidate_review_lane": "challenger_live_shadow_locked_release_candidate_review_queue",
            "attack_challenger_live_shadow_locked_release_governance_check_ready": True,
            "attack_challenger_live_shadow_locked_release_governance_check_lane": "challenger_live_shadow_locked_release_governance_check_queue",
            "attack_challenger_next_step": "challenger_live_shadow_locked_release_governance_entry",
            "attack_challenger_remote_monitoring_deployment_handoff_ready": False,
            "attack_challenger_remote_monitoring_deployment_handoff_lane": "",
            "attention_flags": [
                "quick_read_contract=drifted",
            ],
        },
        "development": {
            "project_direction": "ops hardening",
            "current_work": [
                "candidate=btc_1d_prod_candidate",
                "practical_status=needs_review",
                "attack_challenger=pullthrough_asymmetric_release_tighter_exit",
            ],
            "next_actions": [
                "contract_health drift recovery",
                "paper ledger consistency recovery",
                "challenger_live_shadow_locked_release_governance_entry",
            ],
        },
        "promotion_bridge": {
            "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit",
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": True,
            "attack_challenger_bridge_entry_ready": True,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue",
            "attack_challenger_execution_contract_entry_ready": True,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue",
            "attack_challenger_operator_stack_handoff_ready": True,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue",
            "attack_challenger_operator_runbook_candidate_entry_ready": True,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue",
            "attack_challenger_operator_runbook_execution_entry_ready": True,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue",
            "attack_challenger_live_readiness_review_ready": True,
            "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue",
            "attack_challenger_live_shadow_activation_review_ready": True,
            "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue",
            "attack_challenger_live_candidate_entry_ready": True,
            "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue",
            "attack_challenger_live_operator_paper_entry_ready": True,
            "attack_challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue",
            "attack_challenger_live_shadow_governance_review_ready": True,
            "attack_challenger_live_shadow_governance_review_lane": "challenger_live_shadow_governance_queue",
            "attack_challenger_live_governed_shadow_entry_ready": True,
            "attack_challenger_live_governed_shadow_entry_lane": "challenger_live_governed_shadow_queue",
            "attack_challenger_live_shadow_candidate_paper_review_ready": True,
            "attack_challenger_live_shadow_candidate_paper_review_lane": "challenger_live_shadow_candidate_paper_queue",
            "attack_challenger_live_shadow_candidate_governance_lock_ready": True,
            "attack_challenger_live_shadow_candidate_governance_lock_lane": "challenger_live_shadow_candidate_governance_lock_queue",
            "attack_challenger_live_shadow_locked_entry_ready": True,
            "attack_challenger_live_shadow_locked_entry_lane": "challenger_live_shadow_locked_queue",
            "attack_challenger_live_shadow_locked_candidate_review_ready": True,
            "attack_challenger_live_shadow_locked_candidate_review_lane": "challenger_live_shadow_locked_candidate_review_queue",
            "attack_challenger_live_shadow_locked_candidate_release_review_ready": True,
            "attack_challenger_live_shadow_locked_candidate_release_review_lane": "challenger_live_shadow_locked_candidate_release_review_queue",
            "attack_challenger_live_shadow_locked_release_entry_ready": True,
            "attack_challenger_live_shadow_locked_release_entry_lane": "challenger_live_shadow_locked_release_queue",
            "attack_challenger_live_shadow_locked_release_candidate_review_ready": True,
            "attack_challenger_live_shadow_locked_release_candidate_review_lane": "challenger_live_shadow_locked_release_candidate_review_queue",
            "attack_challenger_live_shadow_locked_release_governance_check_ready": True,
            "attack_challenger_live_shadow_locked_release_governance_check_lane": "challenger_live_shadow_locked_release_governance_check_queue",
            "attack_challenger_next_step": "challenger_live_shadow_locked_release_governance_entry",
            "attack_challenger_paper_validation_cagr": 0.2712,
            "attack_challenger_paper_validation_max_drawdown": 0.16,
            "attack_challenger_walk_forward_sensitivity_max_drift": 0.0928,
            "attack_challenger_friction_final_decision": "continue",
        },
        "hold36_local_ceiling": {
            "active": True,
            "attack_main": "ratio112_tighter_stop_main",
            "active_backup": "post_spike_trend92_depth058_volume105_hold36",
            "monitoring_candidate": "post_spike_trend92_depth058_volume105_hold36",
            "status_band": "pressure_watch",
            "ceiling_confirmed": True,
            "primary_blocker": "base_cagr_gap",
            "remaining_base_cagr_gap_to_open": 0.03788175,
            "remaining_cost20_cagr_gap_to_open": 0.0,
            "do_not_repeat_local_loop": True,
            "next_step_now": "open_only_new_family_or_wider_frame_search",
            "closed_local_axes": [
                "challenger_reopen",
                "base_gap_recovery",
                "entry_timing",
                "entry_strength",
                "structure",
            ],
            "base_cagr_gap_to_main": 0.07788175,
            "cost20_cagr_gap_to_main": 0.05723624,
            "sharpe_edge_vs_main": 0.25185224,
            "mdd_improvement_vs_main": 0.06568218,
            "drift_improvement_vs_main": 0.20381937,
        },
        "performance": {
            "carry_decision": "pass",
            "carry_sharpe": 1.2,
            "carry_cagr": 0.25,
            "carry_max_drawdown": 0.1,
            "survivability_decision": "pass",
            "survivability_sharpe": 1.0,
            "survivability_cagr": 0.2,
            "survivability_max_drawdown": 0.12,
            "walk_forward_passed": False,
            "walk_forward_oos_sharpe": 0.7,
            "walk_forward_oos_cagr": 0.1,
            "walk_forward_oos_max_drawdown": 0.18,
            "friction_decision": "warn",
            "friction_heaviest_level_bps": 16,
            "friction_heaviest_level_sharpe": 0.55,
            "eth_symbol": "ETHUSDT",
            "eth_pass_rate": 0.6,
        },
        "overview": {
            "combined_health_line": "combined health",
            "research_stack_status": "research status",
            "contract_health_line": "contract health",
            "execution_contract_health_line": "execution contract health",
            "execution_contract_read": "execution contract read",
        },
        "paper_execution": {
            "paper_execution_read": "paper execution read",
            "intent_count": 1,
            "signed_request_count": 1,
            "paper_applied_count": 0,
            "paper_duplicate_count": 2,
            "paper_closed_count": 0,
            "paper_open_count": 1,
            "paper_ledger_snapshot_read": "paper ledger | open=1 | closed=0 | exit_fills=0 | orders=1 | fills=1",
        },
        "contracts": {
            "quick_read_operating_contract_aligned": False,
            "quick_read_paper_execution_contract_aligned": False,
            "quick_read_contract_health_aligned": False,
            "execution_contract_paper_ledger_snapshot_summary_aligned": False,
            "execution_contract_paper_execution_contract_aligned_summary_aligned": False,
        },
        "artifacts": {
            "latest_summary_json": "analysis_results\\btc_1d_latest_summary_latest.json",
            "operating_index_json": "analysis_results\\btc_1d_operating_index_latest.json",
            "operating_brief_json": "analysis_results\\btc_1d_operating_brief_latest.json",
            "quick_read_contract_json": "analysis_results\\btc_1d_quick_read_contract_screen_latest.json",
            "execution_contract_json": "analysis_results\\btc_1d_execution_contract_screen_latest.json",
            "paper_nightly_summary_json": "analysis_results\\btc_1d_paper_nightly_summary_latest.json",
            "attack_challenger_bridge_report_json": "analysis_results\\btc_1d_pullthrough_asymmetric_release_promotion_bridge_latest.json",
            "hold36_local_ceiling_json": "analysis_results\\btc_1d_hold36_local_ceiling_handoff_latest.json",
        },
    }

    rendered = render_markdown(report)
    html_rendered = render_html(report)

    assert "# BTC 1d Operator Dashboard" in rendered
    assert "Dashboard ready: `False`" in rendered
    assert "Operator verdict: `ops_repair_required`" in rendered
    assert "Quick-read contract partitioned: `False`" in rendered
    assert "Contract health aligned: `False`" in rendered
    assert "Execution contract aligned: `False`" in rendered
    assert "Paper ledger consistent: `False`" in rendered
    assert "## Development" in rendered
    assert "Project direction: `ops hardening`" in rendered
    assert "## Promotion Bridge" in rendered
    assert "Attack challenger: `pullthrough_asymmetric_release_tighter_exit`" in rendered
    assert "Bridge entry ready: `True`" in rendered
    assert "Queue lane: `attack_challenger_queue`" in rendered
    assert "## Performance" in rendered
    assert "## Hold36 Local Ceiling" in rendered
    assert "Status band: `pressure_watch`" in rendered
    assert "ETH cross-check: `ETHUSDT` | pass_rate `0.6`" in rendered
    assert "paper_duplicate_count: `2`" in rendered
    assert "- quick_read_contract=drifted" in rendered
    assert "- Remote monitoring deployment handoff ready: `False`" in rendered
    assert (
        "- hold36_local_ceiling_json: "
        "`analysis_results\\btc_1d_hold36_local_ceiling_handoff_latest.json`"
    ) in rendered
    assert "<title>BTC 1d Operator Dashboard</title>" in html_rendered
    assert "dashboard_ready=False" in html_rendered
    assert "operator_verdict=ops_repair_required" in html_rendered
    assert "Attack challenger" in html_rendered
    assert "Project direction" in html_rendered
    assert "ETH cross-check" in html_rendered
    assert "Hold36 Local Ceiling" in html_rendered
    assert "pressure_watch" in html_rendered
    assert "quick_read_contract=drifted" in html_rendered
    assert "Remote monitoring deployment handoff ready" in html_rendered

    json_path = tmp_path / "btc_1d_operator_dashboard_20260418T000000Z.json"
    md_path = tmp_path / "btc_1d_operator_dashboard_20260418T000000Z.md"
    html_path = tmp_path / "btc_1d_operator_dashboard_20260418T000000Z.html"
    json_path.write_text('{"ok": true}', encoding="utf-8")
    md_path.write_text("# ok", encoding="utf-8")
    html_path.write_text("<html>ok</html>", encoding="utf-8")

    aliases = _write_latest_aliases(json_path, md_path, html_path)

    latest_json = Path(aliases["btc_1d_operator_dashboard"])
    latest_md = Path(aliases["btc_1d_operator_dashboard_md"])
    latest_html = Path(aliases["btc_1d_operator_dashboard_html"])
    assert latest_json.name == "btc_1d_operator_dashboard_latest.json"
    assert latest_json.read_text(encoding="utf-8") == '{"ok": true}'
    assert latest_md.name == "btc_1d_operator_dashboard_md_latest.md"
    assert latest_md.read_text(encoding="utf-8") == "# ok"
    assert latest_html.name == "btc_1d_operator_dashboard_html_latest.html"
    assert latest_html.read_text(encoding="utf-8") == "<html>ok</html>"


def test_build_dashboard_reflects_remote_monitoring_handoff_surface(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"

    _write_json(
        analysis_dir / "btc_1d_latest_summary_latest.json",
        {
            "candidate": "btc_1d_shadow_candidate",
            "shadow_decision": "shadow_ready_for_btc_only",
            "carry": {"decision": "pass", "sharpe": 1.1, "cagr": 0.2, "max_drawdown": 0.1},
            "survivability": {"decision": "pass", "sharpe": 1.0, "cagr": 0.18, "max_drawdown": 0.12},
            "walk_forward": {"passed": True, "oos_sharpe": 0.8, "oos_cagr": 0.1, "oos_max_drawdown": 0.08},
            "friction": {"decision": "continue", "heaviest_level_bps": 20, "heaviest_level_sharpe": 0.7},
            "eth_cross_check": {"symbol": "ETHUSDT", "pass_rate": 0.0},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "practical_status_label": "btc_only_practical_with_caveats",
            "combined_health_line": "practical || research || contract",
            "research_stack_status": "research healthy",
            "execution_contract_health_line": "execution health || execution contract",
            "execution_contract_read": "execution contract | aligned | paper execution",
            "paper_execution_read": "paper execution | track=operating | applied=0 | closed=0 | open=0",
            "paper_execution_contract_aligned": True,
            "paper_exit_duplicate_run": False,
            "paper_ledger_consistent": True,
            "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=0 | exit_fills=0 | orders=0 | fills=0",
            "contract_health_aligned": True,
            "operator_verdict": "shadow_monitoring_ready",
            "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit",
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": True,
            "attack_challenger_live_shadow_locked_release_governance_entry_ready": True,
            "attack_challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue",
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_remote_monitoring_deployment_handoff_lane": ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE,
            "attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
            "attack_challenger_paper_validation_cagr": 0.2712,
            "attack_challenger_paper_validation_max_drawdown": 0.16,
            "attack_challenger_walk_forward_sensitivity_max_drift": 0.0928,
            "attack_challenger_friction_final_decision": "continue",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {"contract_health_line": "BTC 1d contract health | aligned=True"},
    )
    _write_json(
        analysis_dir / "btc_1d_quick_read_contract_screen_latest.json",
        {
            "contract_summary": {
                "operating_contract_aligned": True,
                "paper_execution_contract_aligned": True,
                "contract_health_aligned": True,
            },
            "contract_verdict": {"contracts_are_well_partitioned": True},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_contract_screen_latest.json",
        {
            "execution_contract_summary": {
                "execution_contract_health_line": "execution health || execution contract",
                "execution_contract_read": "execution contract | aligned | paper execution",
                "paper_ledger_snapshot_summary_aligned": True,
                "paper_execution_contract_aligned_summary_aligned": True,
            },
            "execution_contract_verdict": {"execution_contract_aligned": True},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "intent_count": 1,
            "signed_request_count": 1,
            "paper_applied_count": 0,
            "paper_duplicate_count": 0,
            "paper_closed_count": 0,
            "paper_open_count": 0,
            "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=0 | exit_fills=0 | orders=0 | fills=0",
        },
    )

    report = build_dashboard(analysis_dir)

    assert report["dashboard_summary"]["attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert report["dashboard_summary"]["deployment_monitoring_active"] is True
    assert (
        report["dashboard_summary"]["attack_challenger_remote_monitoring_deployment_handoff_lane"]
        == ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE
    )
    assert (
        report["dashboard_summary"]["attack_challenger_next_step"]
        == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
    )
    assert report["development"]["next_actions"] == [
        ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
    ]
    assert (
        report["artifacts"]["attack_challenger_bridge_report_json"]
        == "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )
    rendered = render_markdown(report)
    rendered_html = render_html(report)
    assert "- Deployment monitoring active: `True`" in rendered
    assert (
        f"- Remote monitoring deployment handoff lane: `{ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE}`"
        in rendered
    )
    assert (
        f"- Next step: `{ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP}`"
        in rendered
    )
    assert (
        "- attack_challenger_bridge_report_json: "
        "`analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json`"
    ) in rendered
    assert "Remote monitoring deployment handoff lane" in rendered_html
    assert "deployment_monitoring_active=True" in rendered_html
    assert ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP in rendered_html
    assert (
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
        in rendered_html
    )
