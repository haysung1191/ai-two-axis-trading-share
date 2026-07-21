from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff as target
from scripts.btc_1d_handoff_constants import (
    ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_REPAIR_LANE,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_REPAIR_NEXT_STEP,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_remote_monitoring_deployment_handoff_marks_ready(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_entry_latest.json",
        {
            "stack_context": {
                "attack_main": "ratio112_tighter_stop_main",
                "attack_backup": "ratio111_tighter_stop_backup",
                "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit",
                "operator_verdict": "shadow_monitoring_ready",
                "shadow_decision": "shadow_ready_for_btc_only",
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "paper_validation_sharpe": 1.21,
                "paper_validation_trades": 12,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_shadow_locked_release_governance_entry_requirements": {
                "promotion_chain_still_green": True,
            },
            "challenger_live_shadow_locked_release_governance_entry_verdict": {
                "challenger_live_shadow_locked_release_governance_entry_ready": True,
                "challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue",
                "next_step_now": "remote monitoring and deployment handoff",
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "operator_verdict": "shadow_monitoring_ready",
            "attack_challenger_live_shadow_locked_release_governance_entry_ready": True,
            "attack_challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "attack_challenger_live_shadow_locked_release_governance_entry_ready": True,
            "attack_challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operator_dashboard_latest.json",
        {
            "dashboard_summary": {
                "dashboard_ready": True,
                "operator_verdict": "shadow_monitoring_ready",
                "attack_challenger_live_shadow_locked_release_governance_entry_ready": True,
                "attack_challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue",
            },
            "development": {
                "next_actions": ["remote monitoring and deployment handoff"],
            },
        },
    )

    report = target.build_report(analysis_dir=analysis_dir)

    requirements = report["remote_monitoring_deployment_handoff_requirements"]
    verdict = report["remote_monitoring_deployment_handoff_verdict"]

    assert all(requirements.values())
    assert verdict["remote_monitoring_deployment_handoff_ready"] is True
    assert (
        verdict["remote_monitoring_deployment_handoff_lane"]
        == ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE
    )
    assert verdict["next_step_now"] == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP


def test_remote_monitoring_deployment_handoff_accepts_advanced_dashboard_next_action(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_entry_latest.json",
        {
            "stack_context": {
                "attack_main": "ratio112_tighter_stop_main",
                "attack_backup": "ratio111_tighter_stop_backup",
                "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit",
                "operator_verdict": "shadow_monitoring_ready",
                "shadow_decision": "shadow_ready_for_btc_only",
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "paper_validation_sharpe": 1.21,
                "paper_validation_trades": 12,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_shadow_locked_release_governance_entry_requirements": {
                "promotion_chain_still_green": True,
            },
            "challenger_live_shadow_locked_release_governance_entry_verdict": {
                "challenger_live_shadow_locked_release_governance_entry_ready": True,
                "challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue",
                "next_step_now": "remote monitoring and deployment handoff",
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "operator_verdict": "shadow_monitoring_ready",
            "attack_challenger_live_shadow_locked_release_governance_entry_ready": True,
            "attack_challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "attack_challenger_live_shadow_locked_release_governance_entry_ready": True,
            "attack_challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operator_dashboard_latest.json",
        {
            "dashboard_summary": {
                "dashboard_ready": True,
                "operator_verdict": "shadow_monitoring_ready",
                "attack_challenger_live_shadow_locked_release_governance_entry_ready": True,
                "attack_challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue",
            },
            "development": {
                "next_actions": [ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP],
            },
        },
    )

    report = target.build_report(analysis_dir=analysis_dir)

    requirements = report["remote_monitoring_deployment_handoff_requirements"]
    verdict = report["remote_monitoring_deployment_handoff_verdict"]

    assert requirements["dashboard_next_actions_include_handoff"] is True
    assert verdict["remote_monitoring_deployment_handoff_ready"] is True
    assert verdict["next_step_now"] == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP


def test_remote_monitoring_deployment_handoff_marks_repair_hold_when_not_ready(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_entry_latest.json",
        {
            "stack_context": {
                "attack_main": "ratio112_tighter_stop_main",
                "attack_backup": "ratio111_tighter_stop_backup",
                "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit",
                "operator_verdict": "shadow_monitoring_ready",
                "shadow_decision": "shadow_ready_for_btc_only",
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "paper_validation_sharpe": 1.21,
                "paper_validation_trades": 12,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_shadow_locked_release_governance_entry_requirements": {
                "promotion_chain_still_green": True,
            },
            "challenger_live_shadow_locked_release_governance_entry_verdict": {
                "challenger_live_shadow_locked_release_governance_entry_ready": True,
                "challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue",
                "next_step_now": "remote monitoring and deployment handoff",
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "operator_verdict": "shadow_monitoring_ready",
            "attack_challenger_live_shadow_locked_release_governance_entry_ready": True,
            "attack_challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "attack_challenger_live_shadow_locked_release_governance_entry_ready": False,
            "attack_challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operator_dashboard_latest.json",
        {
            "dashboard_summary": {
                "dashboard_ready": True,
                "operator_verdict": "shadow_monitoring_ready",
                "attack_challenger_live_shadow_locked_release_governance_entry_ready": True,
                "attack_challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue",
            },
            "development": {
                "next_actions": ["remote monitoring and deployment handoff"],
            },
        },
    )

    report = target.build_report(analysis_dir=analysis_dir)

    requirements = report["remote_monitoring_deployment_handoff_requirements"]
    verdict = report["remote_monitoring_deployment_handoff_verdict"]

    assert requirements["operating_brief_governance_entry_ready"] is False
    assert verdict["remote_monitoring_deployment_handoff_ready"] is False
    assert (
        verdict["remote_monitoring_deployment_handoff_lane"]
        == ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_REPAIR_LANE
    )
    assert (
        verdict["next_step_now"]
        == ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_REPAIR_NEXT_STEP
    )
