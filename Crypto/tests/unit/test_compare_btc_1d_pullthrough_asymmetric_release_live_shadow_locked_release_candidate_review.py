from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_candidate_review as target


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _base_release_entry_report() -> dict:
    return {
        "stack_context": {
            "attack_main": "ratio112_tighter_stop_main",
            "attack_backup": "ratio111_tighter_stop_backup",
            "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
            "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit",
            "shadow_decision": "shadow_ready_for_btc_only",
        },
        "candidate_profile": {
            "label": "pullthrough_asymmetric_release_tighter_exit",
            "paper_validation_cagr": 0.2712,
            "paper_validation_max_drawdown": 0.16,
            "paper_validation_sharpe": 1.3363,
            "paper_validation_trades": 22,
            "walk_forward_sensitivity_max_drift": 0.0928,
            "friction_final_decision": "continue",
        },
        "challenger_live_shadow_locked_release_entry_requirements": {
            "promotion_chain_still_green": True,
            "challenger_live_shadow_locked_candidate_release_review_ready": True,
        },
        "challenger_live_shadow_locked_release_entry_verdict": {
            "challenger_live_shadow_locked_release_entry_ready": True,
            "challenger_live_shadow_locked_release_entry_lane": "challenger_live_shadow_locked_release_queue",
            "next_step_now": "challenger_live_shadow_locked_release_candidate_review",
        },
    }


def test_pullthrough_live_shadow_locked_release_candidate_review_marks_ready(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_entry_latest.json",
        _base_release_entry_report(),
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "operator_verdict": "shadow_monitoring_ready",
            "candidate": "volatility_expansion_reclaim_lower_atr_window_tighter_stop",
            "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit",
            "attack_challenger_live_shadow_locked_release_entry_ready": True,
            "attack_challenger_live_shadow_locked_release_entry_lane": "challenger_live_shadow_locked_release_queue",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "shadow_decision": "shadow_ready_for_btc_only",
            "research_stack_health": {
                "attack_frontier": "ratio112_tighter_stop_main",
                "attack_backup": "bridge_28_relief",
            },
            "attack_challenger_live_shadow_locked_release_entry_ready": True,
            "attack_challenger_live_shadow_locked_release_entry_lane": "challenger_live_shadow_locked_release_queue",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operator_dashboard_latest.json",
        {
            "dashboard_summary": {
                "attack_challenger_live_shadow_locked_release_entry_ready": True,
                "attack_challenger_live_shadow_locked_release_entry_lane": "challenger_live_shadow_locked_release_queue",
            }
        },
    )
    report = target.build_report(analysis_dir=analysis_dir)

    requirements = report[
        "challenger_live_shadow_locked_release_candidate_review_requirements"
    ]
    verdict = report["challenger_live_shadow_locked_release_candidate_review_verdict"]

    assert requirements["challenger_live_shadow_locked_release_entry_ready"] is True
    assert requirements["operating_index_live_shadow_locked_release_entry_ready"] is True
    assert requirements["operating_brief_live_shadow_locked_release_entry_ready"] is True
    assert requirements["dashboard_live_shadow_locked_release_entry_ready"] is True
    assert requirements["queue_lane_mirrored"] is True
    assert verdict["challenger_live_shadow_locked_release_candidate_review_ready"] is True


def test_pullthrough_live_shadow_locked_release_candidate_review_points_to_governance_check(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_entry_latest.json",
        _base_release_entry_report(),
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "operator_verdict": "shadow_monitoring_ready",
            "candidate": "volatility_expansion_reclaim_lower_atr_window_tighter_stop",
            "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit",
            "attack_challenger_live_shadow_locked_release_entry_ready": True,
            "attack_challenger_live_shadow_locked_release_entry_lane": "challenger_live_shadow_locked_release_queue",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "shadow_decision": "shadow_ready_for_btc_only",
            "research_stack_health": {
                "attack_frontier": "ratio112_tighter_stop_main",
                "attack_backup": "bridge_28_relief",
            },
            "attack_challenger_live_shadow_locked_release_entry_ready": True,
            "attack_challenger_live_shadow_locked_release_entry_lane": "challenger_live_shadow_locked_release_queue",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operator_dashboard_latest.json",
        {
            "dashboard_summary": {
                "attack_challenger_live_shadow_locked_release_entry_ready": True,
                "attack_challenger_live_shadow_locked_release_entry_lane": "challenger_live_shadow_locked_release_queue",
            }
        },
    )
    report = target.build_report(analysis_dir=analysis_dir)

    verdict = report["challenger_live_shadow_locked_release_candidate_review_verdict"]
    context = report["stack_context"]

    assert context["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert (
        verdict["challenger_live_shadow_locked_release_candidate_review_lane"]
        == "challenger_live_shadow_locked_release_candidate_review_queue"
    )
    assert verdict["next_step_now"] == "challenger_live_shadow_locked_release_governance_check"
    assert context["attack_backup"] == "bridge_28_relief"
