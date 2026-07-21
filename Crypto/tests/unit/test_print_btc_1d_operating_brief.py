from __future__ import annotations

import json
from pathlib import Path

from scripts.btc_1d_handoff_constants import (
    ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE,
)
from scripts.print_btc_1d_operating_brief import (
    build_operating_brief,
    render_operating_brief,
    render_operating_brief_markdown,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_build_operating_brief_reads_latest_artifacts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir / "btc_1d_latest_summary_latest.json",
        {
            "candidate": "low_vol_cap_050_025_minvol020_p2200",
            "scope": "BTC-only",
            "shadow_decision": "shadow_ready_for_btc_only",
            "operator_verdict": "shadow_monitoring_ready",
        },
    )
    practical_gate_path = analysis_dir / "btc_1d_practical_promotion_gate_latest.json"
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "quick_read_order_version": "operating_v3",
            "quick_read_order": [
                "practical_status",
                "combined_health",
                "research_stack_status",
                "carry",
                "survivability",
                "walk_forward",
                "friction",
                "eth_cross_check",
                "quick_read_contract",
                "open_first",
            ],
            "operator_verdict": "shadow_monitoring_ready",
            "practical_promotion_gate": str(practical_gate_path),
            "practical_promotion_gate_md": "analysis_results\\btc_1d_practical_promotion_gate_md_latest.md",
            "research_stack_operating_brief_md": "analysis_results\\btc_1d_research_stack_operating_brief_md_latest.md",
            "quick_read_contract_screen_md": "analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md",
            "execution_contract_screen_md": "analysis_results\\btc_1d_execution_contract_screen_md_latest.md",
            "execution_contract_screen": "analysis_results\\btc_1d_execution_contract_screen_latest.json",
            "meta_contract_screen_md": "analysis_results\\btc_1d_meta_contract_screen_md_latest.md",
            "paper_nightly_summary": "analysis_results\\btc_1d_paper_nightly_summary_latest.json",
            "paper_nightly_summary_md": "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md",
            "paper_nightly_health_line": "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0",
            "execution_health_line": "BTC 1d practical health | status=btc_only_practical_with_caveats | ok=True | candidate=volatility_expansion_reclaim_lower_atr_window_tighter_stop | sharpe=1.3946 | cagr=37.72% | mdd=16.09% | caveats=2 || BTC 1d research stack | frontier=ratio112_tighter_stop_main || BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0",
            "execution_contract_health_line": "BTC 1d practical health | status=btc_only_practical_with_caveats | ok=True | candidate=volatility_expansion_reclaim_lower_atr_window_tighter_stop | sharpe=1.3946 | cagr=37.72% | mdd=16.09% | caveats=4 || BTC 1d research stack | frontier=ratio112_tighter_stop_main | cagr=42.43% | mdd=16.09% | sharpe=1.5613 | backup=ratio111_tighter_stop_backup | backup_drift=0.4172 | defensive=volatility_expansion_pullthrough_shorter_hold (candidate_stage_hold) | next_near_miss=trend_dip_reversal_breakout_tighter_stop_mid_hold (validated_fail_hold) || BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0 || execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0",
            "execution_contract_read": "execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0",
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "paper_execution_contract_checked_aligned": True,
            "paper_execution_contract_aligned_aligned": True,
            "paper_execution_contract_checked_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned": True,
            "paper_execution_contract_checked_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_aligned_entry_aligned": True,
            "paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "paper_execution_contract_checked_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_aligned_summary_aligned": True,
            "paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "paper_execution_read": "paper execution | track=operating | applied=1 | closed=1 | open=0",
            "paper_exit_duplicate_run": True,
            "paper_ledger_consistent": True,
            "paper_ledger_snapshot": {
                "open_position_count": 0,
                "closed_position_count": 1,
                "exit_fill_count": 1,
                "order_count": 1,
                "fill_count": 1,
            },
            "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
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
            "latest_summary_md": "analysis_results\\btc_1d_latest_summary_md_latest.md",
            "shadow_packet_md": "analysis_results\\btc_1d_shadow_packet_md_latest.md",
            "status_board_md": "analysis_results\\btc_1d_candidate_status_board_md_latest.md",
            "baseline_freeze_md": "analysis_results\\btc_1d_baseline_freeze_md_latest.md",
            "shadow_readiness_md": "analysis_results\\btc_1d_shadow_readiness_md_latest.md",
            "checks": {
                "carry": {"periods": 2200, "decision": "PASS", "sharpe": 1.16, "cagr": 0.14, "max_drawdown": 0.10},
                "survivability": {
                    "periods": 2600,
                    "decision": "PASS",
                    "sharpe": 1.15,
                    "cagr": 0.15,
                    "max_drawdown": 0.13,
                },
                "walk_forward": {
                    "passed": True,
                    "oos_sharpe": 0.82,
                    "oos_cagr": 0.05,
                    "oos_max_drawdown": 0.06,
                    "sensitivity_max_drift": 0.09,
                    "unstable_parameters": [],
                },
                "friction": {"decision": "continue", "heaviest_level_bps": 20.0, "heaviest_level_sharpe": 1.04},
                "eth_cross_check": {"symbol": "ETHUSDT", "pass_rate": 0.0, "pass_count": 0, "total_count": 4},
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_contract_screen_latest.json",
        {
            "execution_contract_summary": {
                "paper_ledger_snapshot_summary_aligned": True,
            },
            "execution_contract_verdict": {
                "execution_contract_aligned": True,
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "operating_brief": {
                "attack_frontier": "ratio112_tighter_stop_main",
                "attack_backup": "ratio111_tighter_stop_backup",
                "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
                "highest_priority_near_miss": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
            },
            "models": {
                "attack_main": {"base_cagr": 0.4243, "base_mdd": 0.1609, "base_sharpe": 1.5613},
                "attack_backup": {"sensitivity_max_drift": 0.4172},
                "defensive_hold": {"status_label": "candidate_stage_hold"},
                "highest_priority_near_miss": {"candidate_stage_status": "validated_fail_hold"},
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "operating_brief": {
                "attack_frontier": "ratio112_tighter_stop_main",
                "attack_backup": "ratio111_tighter_stop_backup",
                "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
                "highest_priority_near_miss": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
            },
            "models": {
                "attack_main": {"base_cagr": 0.4243, "base_mdd": 0.1609, "base_sharpe": 1.5613},
                "attack_backup": {"sensitivity_max_drift": 0.4172},
                "defensive_hold": {"status_label": "candidate_stage_hold"},
                "highest_priority_near_miss": {"candidate_stage_status": "validated_fail_hold"},
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "operating_brief": {
                "attack_frontier": "ratio112_tighter_stop_main",
                "attack_backup": "ratio111_tighter_stop_backup",
                "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
                "highest_priority_near_miss": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
            },
            "models": {
                "attack_main": {"base_cagr": 0.4243, "base_mdd": 0.1609, "base_sharpe": 1.5613},
                "attack_backup": {"sensitivity_max_drift": 0.4172},
                "defensive_hold": {"status_label": "candidate_stage_hold"},
                "highest_priority_near_miss": {"candidate_stage_status": "validated_fail_hold"},
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "execution_contract_checked": True,
            "execution_contract_aligned": True,
            "paper_execution_contract_checked_aligned": True,
            "paper_execution_contract_aligned_aligned": True,
            "paper_execution_contract_checked_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned": True,
            "paper_execution_contract_checked_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_aligned_entry_aligned": True,
            "paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "paper_execution_contract_checked_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_aligned_summary_aligned": True,
            "paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "quick_read_order_version": "operating_v3",
            "quick_read_order": [
                "practical_status",
                "combined_health",
                "research_stack_status",
                "carry",
                "survivability",
                "walk_forward",
                "friction",
                "eth_cross_check",
                "quick_read_contract",
                "open_first",
            ],
        },
    )
    _write_json(
        practical_gate_path,
        {
            "ok": True,
            "decision": "btc_only_practical_with_caveats",
            "status_label": "btc_only_practical_with_caveats",
            "caveats": ["dsr weak", "range weak"],
            "candidate": "volatility_expansion_reclaim_lower_atr_window_tighter_stop",
            "carry_metrics": {"sharpe": 1.3946, "cagr": 0.3772, "max_drawdown": 0.1609},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "operating_brief": {
                "attack_frontier": "ratio112_tighter_stop_main",
                "attack_backup": "ratio111_tighter_stop_backup",
                "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
                "highest_priority_near_miss": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
            },
            "models": {
                "attack_main": {"base_cagr": 0.4243, "base_mdd": 0.1609, "base_sharpe": 1.5613},
                "attack_backup": {"sensitivity_max_drift": 0.4172},
                "defensive_hold": {"status_label": "candidate_stage_hold"},
                "highest_priority_near_miss": {"candidate_stage_status": "validated_fail_hold"},
            },
        },
    )

    brief = build_operating_brief(analysis_dir=analysis_dir)

    assert brief["candidate"] == "low_vol_cap_050_025_minvol020_p2200"
    assert brief["operator_verdict"] == "shadow_monitoring_ready"
    assert brief["deployment_monitoring_active"] is False
    assert brief["standard_check_order"] == ["practical", "research", "contract", "brief"]
    assert brief["regression_lock_test"] == "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    assert brief["quick_read_order_version"] == "operating_v3"
    assert brief["quick_read_order"] == [
        "practical_status",
        "combined_health",
        "research_stack_status",
        "carry",
        "survivability",
        "walk_forward",
        "friction",
        "eth_cross_check",
        "quick_read_contract",
        "open_first",
    ]
    assert brief["carry"]["periods"] == 2200
    assert brief["walk_forward"]["oos_sharpe"] == 0.82
    assert brief["practical_status_label"] == "btc_only_practical_with_caveats"
    assert brief["practical"]["decision"] == "btc_only_practical_with_caveats"
    assert brief["practical"]["status_label"] == "btc_only_practical_with_caveats"
    assert brief["practical"]["caveat_count"] == 2
    assert brief["practical"]["candidate"] == "volatility_expansion_reclaim_lower_atr_window_tighter_stop"
    assert brief["practical"]["sharpe"] == 1.3946
    assert brief["research_stack_health"]["attack_frontier"] == "ratio112_tighter_stop_main"
    assert brief["research_stack_status"].startswith("BTC 1d research stack | frontier=ratio112_tighter_stop_main")
    assert brief["research_stack_status"] in brief["execution_health_line"]
    assert brief["research_stack_status"] in brief["execution_contract_health_line"]
    assert brief["contract_health"]["operating_brief_version"] == "operating_v3"
    assert brief["contract_health_line"].startswith("BTC 1d contract health | operating_brief=operating_v3")
    assert brief["contract_health_operating_contract_aligned"] is True
    assert brief["contract_health_paper_execution_contract_aligned"] is True
    assert brief["contract_health_aligned"] is True
    assert brief["contract_health_contracts_are_well_partitioned"] is True
    assert brief["combined_health_line"].startswith("BTC 1d practical health | status=btc_only_practical_with_caveats")
    assert brief["paper_nightly_health_line"].startswith("BTC 1d paper nightly | track=operating")
    assert brief["execution_health_line"].startswith("BTC 1d practical health | status=btc_only_practical_with_caveats")
    assert brief["execution_contract_health_line"].endswith("execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0")
    assert brief["execution_contract_read"] == "execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0"
    assert brief["execution_contract_aligned"] is True
    assert brief["execution_contract_paper_ledger_snapshot_summary_aligned"] is True
    assert brief["execution_contract_paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert brief["execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert brief["execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert brief["execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert brief["execution_contract_paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert brief["execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert brief["execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert brief["execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True
    assert brief["paper_execution_contract_checked"] is True
    assert brief["paper_execution_contract_aligned"] is True
    assert brief["paper_execution_contract_checked_aligned"] is True
    assert brief["paper_execution_contract_aligned_aligned"] is True
    assert brief["paper_execution_contract_checked_summary_aligned"] is True
    assert brief["paper_execution_contract_aligned_summary_aligned"] is True
    assert brief["paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert brief["paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert brief["paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert brief["paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert brief["paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert brief["paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert brief["paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert brief["paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True
    assert brief["paper_execution_read"] == "paper execution | track=operating | applied=1 | closed=1 | open=0"
    assert brief["paper_exit_duplicate_run"] is True
    assert brief["paper_ledger_consistent"] is True
    assert brief["paper_ledger_snapshot"]["closed_position_count"] == 1
    assert brief["paper_ledger_snapshot_read"] == "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1"
    assert brief["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert brief["attack_challenger_role_assignment"] == "attack_challenger_candidate"
    assert brief["attack_challenger_promotion_ready"] is True
    assert brief["attack_challenger_bridge_entry_ready"] is True
    assert brief["attack_challenger_bridge_queue_lane"] == "attack_challenger_queue"
    assert brief["attack_challenger_execution_contract_entry_ready"] is True
    assert brief["attack_challenger_execution_contract_queue_lane"] == "challenger_execution_contract_queue"
    assert brief["attack_challenger_operator_stack_handoff_ready"] is True
    assert brief["attack_challenger_operator_stack_handoff_lane"] == "operator_stack_handoff_queue"
    assert brief["attack_challenger_operator_runbook_candidate_entry_ready"] is True
    assert brief["attack_challenger_operator_runbook_candidate_entry_lane"] == "operator_runbook_candidate_queue"
    assert brief["attack_challenger_operator_runbook_execution_entry_ready"] is True
    assert brief["attack_challenger_operator_runbook_execution_entry_lane"] == "challenger_shadow_monitoring_queue"
    assert brief["attack_challenger_live_readiness_review_ready"] is True
    assert brief["attack_challenger_live_readiness_review_lane"] == "challenger_live_readiness_review_queue"
    assert brief["attack_challenger_live_shadow_activation_review_ready"] is True
    assert brief["attack_challenger_live_shadow_activation_review_lane"] == "challenger_live_shadow_activation_queue"
    assert brief["attack_challenger_live_candidate_entry_ready"] is True
    assert brief["attack_challenger_live_candidate_entry_lane"] == "challenger_live_candidate_queue"
    assert brief["attack_challenger_live_operator_paper_entry_ready"] is True
    assert brief["attack_challenger_live_operator_paper_entry_lane"] == "challenger_live_operator_paper_queue"
    assert brief["attack_challenger_live_shadow_governance_review_ready"] is True
    assert brief["attack_challenger_live_shadow_governance_review_lane"] == "challenger_live_shadow_governance_queue"
    assert brief["attack_challenger_live_governed_shadow_entry_ready"] is True
    assert brief["attack_challenger_live_governed_shadow_entry_lane"] == "challenger_live_governed_shadow_queue"
    assert brief["attack_challenger_live_shadow_candidate_paper_review_ready"] is True
    assert (
        brief["attack_challenger_live_shadow_candidate_paper_review_lane"]
        == "challenger_live_shadow_candidate_paper_queue"
    )
    assert brief["attack_challenger_live_shadow_candidate_governance_lock_ready"] is True
    assert (
        brief["attack_challenger_live_shadow_candidate_governance_lock_lane"]
        == "challenger_live_shadow_candidate_governance_lock_queue"
    )
    assert brief["attack_challenger_live_shadow_locked_entry_ready"] is True
    assert (
        brief["attack_challenger_live_shadow_locked_entry_lane"]
        == "challenger_live_shadow_locked_queue"
    )
    assert brief["attack_challenger_live_shadow_locked_candidate_review_ready"] is True
    assert (
        brief["attack_challenger_live_shadow_locked_candidate_review_lane"]
        == "challenger_live_shadow_locked_candidate_review_queue"
    )
    assert (
        brief["attack_challenger_live_shadow_locked_candidate_release_review_ready"]
        is True
    )
    assert (
        brief["attack_challenger_live_shadow_locked_candidate_release_review_lane"]
        == "challenger_live_shadow_locked_candidate_release_review_queue"
    )
    assert brief["attack_challenger_live_shadow_locked_release_entry_ready"] is True
    assert (
        brief["attack_challenger_live_shadow_locked_release_entry_lane"]
        == "challenger_live_shadow_locked_release_queue"
    )
    assert brief["attack_challenger_live_shadow_locked_release_candidate_review_ready"] is True
    assert (
        brief["attack_challenger_live_shadow_locked_release_candidate_review_lane"]
        == "challenger_live_shadow_locked_release_candidate_review_queue"
    )
    assert brief["attack_challenger_live_shadow_locked_release_governance_check_ready"] is True
    assert (
        brief["attack_challenger_live_shadow_locked_release_governance_check_lane"]
        == "challenger_live_shadow_locked_release_governance_check_queue"
    )
    assert brief["attack_challenger_next_step"] == "challenger_live_shadow_locked_release_governance_entry"
    assert brief["attack_challenger_paper_validation_cagr"] == 0.2712
    assert brief["attack_challenger_friction_final_decision"] == "continue"
    assert brief["paths"]["operating_index_md"].endswith("btc_1d_operating_index_md_latest.md")
    assert brief["paths"]["research_stack_operating_brief_md"].endswith(
        "btc_1d_research_stack_operating_brief_md_latest.md"
    )
    assert brief["paths"]["quick_read_contract_screen_md"].endswith(
        "btc_1d_quick_read_contract_screen_md_latest.md"
    )
    assert brief["paths"]["execution_contract_screen_md"].endswith(
        "btc_1d_execution_contract_screen_md_latest.md"
    )
    assert brief["paths"]["meta_contract_screen_md"].endswith(
        "btc_1d_meta_contract_screen_md_latest.md"
    )
    assert brief["paths"]["paper_nightly_summary"].endswith("btc_1d_paper_nightly_summary_latest.json")
    assert brief["paths"]["paper_nightly_summary_md"].endswith("btc_1d_paper_nightly_summary_md_latest.md")


def test_build_operating_brief_prefers_paper_summary_self_check_mirror_over_stale_index(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir / "btc_1d_latest_summary_latest.json",
        {
            "candidate": "low_vol_cap_050_025_minvol020_p2200",
            "scope": "BTC-only",
            "shadow_decision": "shadow_ready_for_btc_only",
        },
    )
    practical_gate_path = analysis_dir / "btc_1d_practical_promotion_gate_latest.json"
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "quick_read_order_version": "operating_v3",
            "quick_read_order": [
                "practical_status",
                "combined_health",
                "research_stack_status",
                "carry",
                "survivability",
                "walk_forward",
                "friction",
                "eth_cross_check",
                "quick_read_contract",
                "open_first",
            ],
            "practical_promotion_gate": str(practical_gate_path),
            "practical_promotion_gate_md": "analysis_results\\btc_1d_practical_promotion_gate_md_latest.md",
            "research_stack_operating_brief_md": "analysis_results\\btc_1d_research_stack_operating_brief_md_latest.md",
            "quick_read_contract_screen_md": "analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md",
            "execution_contract_screen_md": "analysis_results\\btc_1d_execution_contract_screen_md_latest.md",
            "execution_contract_screen": "analysis_results\\btc_1d_execution_contract_screen_latest.json",
            "meta_contract_screen_md": "analysis_results\\btc_1d_meta_contract_screen_md_latest.md",
            "paper_nightly_summary": "analysis_results\\btc_1d_paper_nightly_summary_latest.json",
            "paper_nightly_summary_md": "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md",
            "paper_nightly_health_line": "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0",
            "execution_contract_health_line": "execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0",
            "execution_contract_read": "execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0",
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "paper_execution_contract_checked_aligned": True,
            "paper_execution_contract_aligned_aligned": True,
            "paper_execution_contract_checked_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned": True,
            "paper_execution_contract_checked_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_aligned_entry_aligned": True,
            "paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "paper_execution_contract_checked_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_aligned_summary_aligned": True,
            "paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "paper_execution_read": "paper execution | track=operating | applied=1 | closed=1 | open=0",
            "paper_exit_duplicate_run": False,
            "paper_ledger_consistent": True,
            "paper_ledger_snapshot": {
                "open_position_count": 0,
                "closed_position_count": 1,
                "exit_fill_count": 1,
                "order_count": 1,
                "fill_count": 1,
            },
            "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
            "latest_summary_md": "analysis_results\\btc_1d_latest_summary_md_latest.md",
            "shadow_packet_md": "analysis_results\\btc_1d_shadow_packet_md_latest.md",
            "status_board_md": "analysis_results\\btc_1d_candidate_status_board_md_latest.md",
            "baseline_freeze_md": "analysis_results\\btc_1d_baseline_freeze_md_latest.md",
            "shadow_readiness_md": "analysis_results\\btc_1d_shadow_readiness_md_latest.md",
            "checks": {
                "carry": {"periods": 2200, "decision": "PASS", "sharpe": 1.16, "cagr": 0.14, "max_drawdown": 0.10},
                "survivability": {
                    "periods": 2600,
                    "decision": "PASS",
                    "sharpe": 1.15,
                    "cagr": 0.15,
                    "max_drawdown": 0.13,
                },
                "walk_forward": {
                    "passed": True,
                    "oos_sharpe": 0.82,
                    "oos_cagr": 0.05,
                    "oos_max_drawdown": 0.06,
                    "sensitivity_max_drift": 0.09,
                    "unstable_parameters": [],
                },
                "friction": {"decision": "continue", "heaviest_level_bps": 20.0, "heaviest_level_sharpe": 1.04},
                "eth_cross_check": {"symbol": "ETHUSDT", "pass_rate": 0.0, "pass_count": 0, "total_count": 4},
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "execution_contract_checked": True,
            "execution_contract_aligned": True,
            "paper_execution_contract_checked_aligned": False,
            "paper_execution_contract_aligned_aligned": True,
            "paper_execution_contract_checked_summary_aligned": False,
            "paper_execution_contract_aligned_summary_aligned": True,
            "paper_execution_contract_checked_aligned_entry_aligned": False,
            "paper_execution_contract_aligned_aligned_entry_aligned": True,
            "paper_execution_contract_checked_summary_aligned_entry_aligned": False,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "paper_execution_contract_checked_aligned_summary_aligned": False,
            "paper_execution_contract_aligned_aligned_summary_aligned": True,
            "paper_execution_contract_checked_summary_aligned_summary_aligned": False,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_checked_aligned": True,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_contract_screen_latest.json",
        {
            "execution_contract_summary": {
                "paper_ledger_snapshot_summary_aligned": True,
            },
            "execution_contract_verdict": {
                "execution_contract_aligned": True,
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "quick_read_order_version": "operating_v3",
            "quick_read_order": [
                "practical_status",
                "combined_health",
                "research_stack_status",
                "carry",
                "survivability",
                "walk_forward",
                "friction",
                "eth_cross_check",
                "quick_read_contract",
                "open_first",
            ],
        },
    )
    _write_json(
        practical_gate_path,
        {
            "ok": True,
            "decision": "btc_only_practical_with_caveats",
            "status_label": "btc_only_practical_with_caveats",
            "caveats": [],
            "candidate": "volatility_expansion_reclaim_lower_atr_window_tighter_stop",
            "carry_metrics": {"sharpe": 1.3946, "cagr": 0.3772, "max_drawdown": 0.1609},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "operating_brief": {
                "attack_frontier": "ratio112_tighter_stop_main",
                "attack_backup": "ratio111_tighter_stop_backup",
                "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
                "highest_priority_near_miss": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
            },
            "models": {
                "attack_main": {"base_cagr": 0.4243, "base_mdd": 0.1609, "base_sharpe": 1.5613},
                "attack_backup": {"sensitivity_max_drift": 0.4172},
                "defensive_hold": {"status_label": "candidate_stage_hold"},
                "highest_priority_near_miss": {"candidate_stage_status": "validated_fail_hold"},
            },
        },
    )

    brief = build_operating_brief(analysis_dir=analysis_dir)

    assert brief["paper_execution_contract_checked"] is True
    assert brief["paper_execution_contract_aligned"] is True
    assert brief["paper_execution_contract_checked_aligned"] is False
    assert brief["paper_execution_contract_checked_summary_aligned"] is False
    assert brief["paper_execution_contract_checked_aligned_entry_aligned"] is False
    assert brief["paper_execution_contract_checked_summary_aligned_entry_aligned"] is False
    assert brief["paper_execution_contract_checked_aligned_summary_aligned"] is False
    assert brief["paper_execution_contract_checked_summary_aligned_summary_aligned"] is False


def test_render_operating_brief_contains_key_lines() -> None:
    rendered = render_operating_brief(
        {
            "candidate": "low_vol_cap_050_025_minvol020_p2200",
            "scope": "BTC-only",
            "shadow_decision": "shadow_ready_for_btc_only",
            "operator_verdict": "shadow_monitoring_ready",
            "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit",
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": True,
            "attack_challenger_bridge_entry_ready": True,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue",
            "attack_challenger_execution_contract_entry_ready": True,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue",
            "attack_challenger_operator_stack_handoff_ready": True,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue",
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
            "practical": {"decision": "btc_only_practical_with_caveats", "status_label": "btc_only_practical_with_caveats", "ok": True, "caveats": ["a", "b"]},
            "carry": {"periods": 2200, "decision": "PASS", "sharpe": 1.16, "cagr": 0.14, "max_drawdown": 0.10},
            "survivability": {
                "periods": 2600,
                "decision": "PASS",
                "sharpe": 1.15,
                "cagr": 0.15,
                "max_drawdown": 0.13,
            },
            "walk_forward": {
                "passed": True,
                "oos_sharpe": 0.82,
                "oos_cagr": 0.05,
                "oos_max_drawdown": 0.06,
                "sensitivity_max_drift": 0.09,
                "unstable_parameters": [],
            },
            "friction": {"decision": "continue", "heaviest_level_bps": 20.0, "heaviest_level_sharpe": 1.04},
            "eth_cross_check": {"symbol": "ETHUSDT", "pass_rate": 0.0, "pass_count": 0, "total_count": 4},
            "combined_health_line": (
                "BTC 1d practical health | status=btc_only_practical_with_caveats | ok=True | "
                "candidate=low_vol_cap_050_025_minvol020_p2200 | sharpe=1.1600 | cagr=14.00% | mdd=10.00% | caveats=2 "
                "|| BTC 1d research stack | frontier=ratio112_tighter_stop_main"
            ),
            "research_stack_health": {
                "attack_frontier": "ratio112_tighter_stop_main",
                "attack_backup": "ratio111_tighter_stop_backup",
                "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
                "highest_priority_near_miss": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
                "attack_frontier_cagr": 0.4243,
                "attack_frontier_max_drawdown": 0.1609,
                "attack_frontier_sharpe": 1.5613,
                "attack_backup_drift": 0.4172,
                "defensive_hold_status": "candidate_stage_hold",
                "near_miss_status": "validated_fail_hold",
            },
                "contract_health": {
                    "operating_brief_version": "operating_v3",
                    "operating_index_version": "operating_v3",
                "research_stack_version": "research_stack_v2",
                "operating_contract_aligned": True,
                "research_contract_distinct": True,
                "contracts_are_well_partitioned": True,
                "preferred_operating_contract_version": "operating_v3",
                    "preferred_research_contract_version": "research_stack_v2",
                    "shared_standard_check_order": ["practical", "research", "contract", "brief"],
                    "standard_check_order_aligned": True,
                    "health_order_aligned": True,
                },
            "paths": {
                "operating_index_md": "analysis_results\\btc_1d_operating_index_md_latest.md",
                "practical_promotion_gate_md": "analysis_results\\btc_1d_practical_promotion_gate_md_latest.md",
                "research_stack_operating_brief_md": "analysis_results\\btc_1d_research_stack_operating_brief_md_latest.md",
                "quick_read_contract_screen_md": "analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md",
                "execution_contract_screen_md": "analysis_results\\btc_1d_execution_contract_screen_md_latest.md",
                "meta_contract_screen_md": "analysis_results\\btc_1d_meta_contract_screen_md_latest.md",
                "paper_nightly_summary_md": "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md",
            },
            "paper_nightly_health_line": "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0",
            "execution_health_line": "BTC 1d practical health | status=btc_only_practical_with_caveats | ok=True | candidate=low_vol_cap_050_025_minvol020_p2200 | sharpe=1.1600 | cagr=14.00% | mdd=10.00% | caveats=2 || BTC 1d research stack | frontier=ratio112_tighter_stop_main || BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0",
            "execution_contract_health_line": "BTC 1d practical health | status=btc_only_practical_with_caveats | ok=True | candidate=low_vol_cap_050_025_minvol020_p2200 | sharpe=1.1600 | cagr=14.00% | mdd=10.00% | caveats=2 || BTC 1d research stack | frontier=ratio112_tighter_stop_main || BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0 || execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0",
            "execution_contract_read": "execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0",
            "execution_contract_aligned": True,
            "execution_contract_paper_ledger_snapshot_summary_aligned": True,
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "paper_execution_contract_checked_aligned": True,
            "paper_execution_contract_aligned_aligned": True,
            "paper_execution_contract_checked_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned": True,
            "paper_execution_contract_checked_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_aligned_entry_aligned": True,
            "paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "paper_execution_contract_checked_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_aligned_summary_aligned": True,
            "paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "paper_execution_read": "paper execution | track=operating | applied=1 | closed=1 | open=0",
            "paper_exit_duplicate_run": True,
            "paper_ledger_consistent": True,
            "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
        }
    )

    assert "BTC 1d Operating Brief" in rendered
    assert "operator_verdict: shadow_monitoring_ready" in rendered
    assert "practical_status: btc_only_practical_with_caveats | ok=True | caveats=2" in rendered
    assert "carry_2200: PASS" in rendered
    assert "walk_forward: PASS" in rendered
    assert "combined_health_line: BTC 1d practical health | status=btc_only_practical_with_caveats" in rendered
    assert "execution_health_line: BTC 1d practical health | status=btc_only_practical_with_caveats" in rendered
    assert "execution_contract_health_line: BTC 1d practical health | status=btc_only_practical_with_caveats" in rendered
    assert "execution_contract_read: execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0" in rendered
    assert "execution_contract_aligned: True" in rendered
    assert "execution_contract_paper_ledger_snapshot_summary_aligned: True" in rendered
    assert "attack_challenger_candidate: pullthrough_asymmetric_release_tighter_exit" in rendered
    assert "attack_challenger_role_assignment: attack_challenger_candidate" in rendered
    assert "attack_challenger_promotion_ready: True" in rendered
    assert "attack_challenger_bridge_entry_ready: True" in rendered
    assert "attack_challenger_bridge_queue_lane: attack_challenger_queue" in rendered
    assert "attack_challenger_execution_contract_entry_ready: True" in rendered
    assert "attack_challenger_execution_contract_queue_lane: challenger_execution_contract_queue" in rendered
    assert "attack_challenger_operator_stack_handoff_ready: True" in rendered
    assert "attack_challenger_operator_stack_handoff_lane: operator_stack_handoff_queue" in rendered
    assert "attack_challenger_live_readiness_review_ready: True" in rendered
    assert "attack_challenger_live_readiness_review_lane: challenger_live_readiness_review_queue" in rendered
    assert "attack_challenger_live_shadow_activation_review_ready: True" in rendered
    assert "attack_challenger_live_shadow_activation_review_lane: challenger_live_shadow_activation_queue" in rendered
    assert "attack_challenger_live_candidate_entry_ready: True" in rendered
    assert "attack_challenger_live_candidate_entry_lane: challenger_live_candidate_queue" in rendered
    assert "attack_challenger_live_operator_paper_entry_ready: True" in rendered
    assert "attack_challenger_live_operator_paper_entry_lane: challenger_live_operator_paper_queue" in rendered
    assert "attack_challenger_live_shadow_governance_review_ready: True" in rendered
    assert "attack_challenger_live_shadow_governance_review_lane: challenger_live_shadow_governance_queue" in rendered
    assert "attack_challenger_live_governed_shadow_entry_ready: True" in rendered
    assert "attack_challenger_live_governed_shadow_entry_lane: challenger_live_governed_shadow_queue" in rendered
    assert "attack_challenger_live_shadow_candidate_paper_review_ready: True" in rendered
    assert "attack_challenger_live_shadow_candidate_paper_review_lane: challenger_live_shadow_candidate_paper_queue" in rendered
    assert "attack_challenger_live_shadow_candidate_governance_lock_ready: True" in rendered
    assert "attack_challenger_live_shadow_candidate_governance_lock_lane: challenger_live_shadow_candidate_governance_lock_queue" in rendered
    assert "attack_challenger_live_shadow_locked_entry_ready: True" in rendered
    assert "attack_challenger_live_shadow_locked_entry_lane: challenger_live_shadow_locked_queue" in rendered
    assert "attack_challenger_live_shadow_locked_candidate_review_ready: True" in rendered
    assert "attack_challenger_live_shadow_locked_candidate_review_lane: challenger_live_shadow_locked_candidate_review_queue" in rendered
    assert "attack_challenger_live_shadow_locked_candidate_release_review_ready: True" in rendered
    assert "attack_challenger_live_shadow_locked_candidate_release_review_lane: challenger_live_shadow_locked_candidate_release_review_queue" in rendered
    assert "attack_challenger_live_shadow_locked_release_entry_ready: True" in rendered
    assert "attack_challenger_live_shadow_locked_release_entry_lane: challenger_live_shadow_locked_release_queue" in rendered
    assert "attack_challenger_live_shadow_locked_release_candidate_review_ready: True" in rendered
    assert "attack_challenger_live_shadow_locked_release_candidate_review_lane: challenger_live_shadow_locked_release_candidate_review_queue" in rendered
    assert "attack_challenger_live_shadow_locked_release_governance_check_ready: True" in rendered
    assert "attack_challenger_live_shadow_locked_release_governance_check_lane: challenger_live_shadow_locked_release_governance_check_queue" in rendered
    assert "attack_challenger_remote_monitoring_deployment_handoff_ready: False" in rendered
    assert "attack_challenger_remote_monitoring_deployment_handoff_lane: " in rendered
    assert "attack_challenger_next_step: challenger_live_shadow_locked_release_governance_entry" in rendered
    assert "execution_contract_paper_execution_contract_checked_aligned_entry_aligned: True" in rendered
    assert "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned: True" in rendered
    assert "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned: True" in rendered
    assert "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned: True" in rendered
    assert "execution_contract_paper_execution_contract_checked_aligned_summary_aligned: True" in rendered
    assert "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned: True" in rendered
    assert "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned: True" in rendered
    assert "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned: True" in rendered
    assert "paper_execution_contract_checked: True" in rendered
    assert "paper_execution_contract_aligned: True" in rendered
    assert "paper_execution_contract_checked_aligned: True" in rendered
    assert "paper_execution_contract_aligned_aligned: True" in rendered
    assert "paper_execution_contract_checked_summary_aligned: True" in rendered
    assert "paper_execution_contract_aligned_summary_aligned: True" in rendered
    assert "paper_execution_contract_checked_aligned_entry_aligned: True" in rendered
    assert "paper_execution_contract_aligned_aligned_entry_aligned: True" in rendered
    assert "paper_execution_contract_checked_summary_aligned_entry_aligned: True" in rendered
    assert "paper_execution_contract_aligned_summary_aligned_entry_aligned: True" in rendered
    assert "paper_execution_contract_checked_aligned_summary_aligned: True" in rendered
    assert "paper_execution_contract_aligned_aligned_summary_aligned: True" in rendered
    assert "paper_execution_contract_checked_summary_aligned_summary_aligned: True" in rendered
    assert "paper_execution_contract_aligned_summary_aligned_summary_aligned: True" in rendered
    assert "research_stack_status: BTC 1d research stack | frontier=ratio112_tighter_stop_main" in rendered
    assert "contract_health_line: BTC 1d contract health | operating_brief=operating_v3" in rendered
    assert "contract_health_operating_contract_aligned: True" in rendered
    assert "contract_health_paper_execution_contract_aligned: True" in rendered
    assert "contract_health_aligned: True" in rendered
    assert "contract_health_contracts_are_well_partitioned: True" in rendered
    assert "paper_nightly_health_line: BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0" in rendered
    assert "paper_execution_read: paper execution | track=operating | applied=1 | closed=1 | open=0" in rendered
    assert "paper_exit_duplicate_run: True" in rendered
    assert "paper_ledger_consistent: True" in rendered
    assert "paper_ledger_snapshot: paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1" in rendered
    assert "practical_gate: analysis_results\\btc_1d_practical_promotion_gate_md_latest.md" in rendered
    assert "research_stack: analysis_results\\btc_1d_research_stack_operating_brief_md_latest.md" in rendered
    assert "quick_read_contract: analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md" in rendered
    assert "execution_contract: analysis_results\\btc_1d_execution_contract_screen_md_latest.md" in rendered
    assert "meta_contract: analysis_results\\btc_1d_meta_contract_screen_md_latest.md" in rendered
    assert "paper_nightly: analysis_results\\btc_1d_paper_nightly_summary_md_latest.md" in rendered
    assert "open_first: analysis_results\\btc_1d_operating_index_md_latest.md" in rendered


def test_render_operating_brief_markdown_contains_sections() -> None:
    rendered = render_operating_brief_markdown(
        {
            "candidate": "low_vol_cap_050_025_minvol020_p2200",
            "scope": "BTC-only",
            "shadow_decision": "shadow_ready_for_btc_only",
            "operator_verdict": "shadow_monitoring_ready",
            "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit",
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": True,
            "attack_challenger_bridge_entry_ready": True,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue",
            "attack_challenger_execution_contract_entry_ready": True,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue",
            "attack_challenger_operator_stack_handoff_ready": True,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue",
            "attack_challenger_next_step": "operator_runbook_candidate_entry",
            "attack_challenger_paper_validation_cagr": 0.2712,
            "attack_challenger_paper_validation_max_drawdown": 0.16,
            "attack_challenger_walk_forward_sensitivity_max_drift": 0.0928,
            "attack_challenger_friction_final_decision": "continue",
            "practical": {"decision": "btc_only_practical_with_caveats", "status_label": "btc_only_practical_with_caveats", "ok": True, "caveats": ["a", "b"]},
            "carry": {"periods": 2200, "decision": "PASS", "sharpe": 1.16, "cagr": 0.14, "max_drawdown": 0.10},
            "survivability": {
                "periods": 2600,
                "decision": "PASS",
                "sharpe": 1.15,
                "cagr": 0.15,
                "max_drawdown": 0.13,
            },
            "walk_forward": {
                "passed": True,
                "oos_sharpe": 0.82,
                "oos_cagr": 0.05,
                "oos_max_drawdown": 0.06,
                "sensitivity_max_drift": 0.09,
                "unstable_parameters": [],
            },
            "friction": {"decision": "continue", "heaviest_level_bps": 20.0, "heaviest_level_sharpe": 1.04},
            "eth_cross_check": {"symbol": "ETHUSDT", "pass_rate": 0.0, "pass_count": 0, "total_count": 4},
            "combined_health_line": (
                "BTC 1d practical health | status=btc_only_practical_with_caveats | ok=True | "
                "candidate=low_vol_cap_050_025_minvol020_p2200 | sharpe=1.1600 | cagr=14.00% | mdd=10.00% | caveats=2 "
                "|| BTC 1d research stack | frontier=ratio112_tighter_stop_main"
            ),
            "research_stack_health": {
                "attack_frontier": "ratio112_tighter_stop_main",
                "attack_backup": "ratio111_tighter_stop_backup",
                "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
                "highest_priority_near_miss": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
                "attack_frontier_cagr": 0.4243,
                "attack_frontier_max_drawdown": 0.1609,
                "attack_frontier_sharpe": 1.5613,
                "attack_backup_drift": 0.4172,
                "defensive_hold_status": "candidate_stage_hold",
                "near_miss_status": "validated_fail_hold",
            },
                "contract_health": {
                    "operating_brief_version": "operating_v3",
                    "operating_index_version": "operating_v3",
                "research_stack_version": "research_stack_v2",
                "operating_contract_aligned": True,
                "research_contract_distinct": True,
                "contracts_are_well_partitioned": True,
                "preferred_operating_contract_version": "operating_v3",
                    "preferred_research_contract_version": "research_stack_v2",
                    "shared_standard_check_order": ["practical", "research", "contract", "brief"],
                    "standard_check_order_aligned": True,
                    "health_order_aligned": True,
                },
            "paths": {
                "operating_index_md": "analysis_results\\btc_1d_operating_index_md_latest.md",
                "practical_promotion_gate_md": "analysis_results\\btc_1d_practical_promotion_gate_md_latest.md",
                "research_stack_operating_brief_md": "analysis_results\\btc_1d_research_stack_operating_brief_md_latest.md",
                "quick_read_contract_screen_md": "analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md",
                "execution_contract_screen_md": "analysis_results\\btc_1d_execution_contract_screen_md_latest.md",
                "meta_contract_screen_md": "analysis_results\\btc_1d_meta_contract_screen_md_latest.md",
                "paper_nightly_summary_md": "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md",
            },
            "paper_nightly_health_line": "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0",
            "execution_health_line": "BTC 1d practical health | status=btc_only_practical_with_caveats | ok=True | candidate=low_vol_cap_050_025_minvol020_p2200 | sharpe=1.1600 | cagr=14.00% | mdd=10.00% | caveats=2 || BTC 1d research stack | frontier=ratio112_tighter_stop_main || BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0",
            "execution_contract_health_line": "BTC 1d practical health | status=btc_only_practical_with_caveats | ok=True | candidate=low_vol_cap_050_025_minvol020_p2200 | sharpe=1.1600 | cagr=14.00% | mdd=10.00% | caveats=2 || BTC 1d research stack | frontier=ratio112_tighter_stop_main || BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0 || execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0",
            "execution_contract_read": "execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0",
            "execution_contract_aligned": True,
            "execution_contract_paper_ledger_snapshot_summary_aligned": True,
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "paper_execution_contract_checked_aligned": True,
            "paper_execution_contract_aligned_aligned": True,
            "paper_execution_contract_checked_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned": True,
            "paper_execution_contract_checked_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_aligned_entry_aligned": True,
            "paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "paper_execution_contract_checked_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_aligned_summary_aligned": True,
            "paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "paper_execution_read": "paper execution | track=operating | applied=1 | closed=1 | open=0",
            "paper_exit_duplicate_run": True,
            "paper_ledger_consistent": True,
            "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
        }
    )

    assert "# BTC 1d Operating Brief" in rendered
    assert "Operator verdict: `shadow_monitoring_ready`" in rendered
    assert "Attack challenger: `pullthrough_asymmetric_release_tighter_exit` | role `attack_challenger_candidate` | promotion_ready `True` | bridge_entry_ready `True` | queue `attack_challenger_queue` | contract_entry_ready `True` | contract_queue `challenger_execution_contract_queue` | handoff_ready `True` | handoff_lane `operator_stack_handoff_queue` | runbook_entry_ready `False` | runbook_lane `` | runbook_execution_ready `False` | runbook_execution_lane `` | live_readiness_ready `False` | live_readiness_lane `` | live_shadow_activation_ready `False` | live_shadow_activation_lane `` | live_candidate_ready `False` | live_candidate_lane `` | live_operator_paper_ready `False` | live_operator_paper_lane `` | live_shadow_governance_ready `False` | live_shadow_governance_lane `` | live_governed_shadow_ready `False` | live_governed_shadow_lane `` | live_shadow_candidate_paper_ready `False` | live_shadow_candidate_paper_lane `` | live_shadow_candidate_governance_lock_ready `False` | live_shadow_candidate_governance_lock_lane `` | live_shadow_locked_entry_ready `False` | live_shadow_locked_entry_lane `` | live_shadow_locked_candidate_review_ready `False` | live_shadow_locked_candidate_review_lane `` | live_shadow_locked_candidate_release_review_ready `False` | live_shadow_locked_candidate_release_review_lane `` | live_shadow_locked_release_entry_ready `False` | live_shadow_locked_release_entry_lane `` | live_shadow_locked_release_candidate_review_ready `False` | live_shadow_locked_release_candidate_review_lane `` | live_shadow_locked_release_governance_check_ready `False` | live_shadow_locked_release_governance_check_lane `` | live_shadow_locked_release_governance_entry_ready `False` | live_shadow_locked_release_governance_entry_lane `` | remote_monitoring_deployment_handoff_ready `False` | remote_monitoring_deployment_handoff_lane `` | next `operator_runbook_candidate_entry`" in rendered
    assert "Attack challenger profile: `cagr=0.2712 | mdd=0.16 | drift=0.0928 | friction=continue`" in rendered
    assert "## Standard Check Order" in rendered
    assert "1. Practical" in rendered
    assert "2. Research" in rendered
    assert "3. Contract" in rendered
    assert "4. Brief" in rendered
    assert "Regression lock: `tests/unit/test_btc_1d_operating_cli_help_contract.py`" in rendered
    assert "## Quick Read" in rendered
    assert "Execution health: `BTC 1d practical health | status=btc_only_practical_with_caveats" in rendered
    assert "Execution contract health: `BTC 1d practical health | status=btc_only_practical_with_caveats" in rendered
    assert "Execution contract read: `execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0`" in rendered
    assert "Execution contract aligned: `True`" in rendered
    assert "Execution contract paper ledger snapshot summary aligned: `True`" in rendered
    assert "Execution contract paper execution contract checked aligned entry aligned: `True`" in rendered
    assert "Execution contract paper execution contract aligned aligned entry aligned: `True`" in rendered
    assert "Execution contract paper execution contract checked summary aligned entry aligned: `True`" in rendered
    assert "Execution contract paper execution contract aligned summary aligned entry aligned: `True`" in rendered
    assert "Execution contract paper execution contract checked aligned summary aligned: `True`" in rendered
    assert "Execution contract paper execution contract aligned aligned summary aligned: `True`" in rendered
    assert "Execution contract paper execution contract checked summary aligned summary aligned: `True`" in rendered
    assert "Execution contract paper execution contract aligned summary aligned summary aligned: `True`" in rendered
    assert "Paper execution contract checked: `True`" in rendered
    assert "Paper execution contract aligned: `True`" in rendered
    assert "Paper execution contract checked aligned: `True`" in rendered
    assert "Paper execution contract aligned aligned: `True`" in rendered
    assert "Paper execution contract checked summary aligned: `True`" in rendered
    assert "Paper execution contract aligned summary aligned: `True`" in rendered
    assert "Paper execution contract checked aligned entry aligned: `True`" in rendered
    assert "Paper execution contract aligned aligned entry aligned: `True`" in rendered
    assert "Paper execution contract checked summary aligned entry aligned: `True`" in rendered
    assert "Paper execution contract aligned summary aligned entry aligned: `True`" in rendered
    assert "Paper execution contract checked aligned summary aligned: `True`" in rendered
    assert "Paper execution contract aligned aligned summary aligned: `True`" in rendered
    assert "Paper execution contract checked summary aligned summary aligned: `True`" in rendered
    assert "Paper execution contract aligned summary aligned summary aligned: `True`" in rendered
    assert "Practical status: `btc_only_practical_with_caveats` | ok `True` | caveats `2`" in rendered
    assert "Combined health: `BTC 1d practical health | status=btc_only_practical_with_caveats" in rendered
    assert "Research stack status: `BTC 1d research stack | frontier=ratio112_tighter_stop_main" in rendered
    assert "Contract health: `BTC 1d contract health | operating_brief=operating_v3" in rendered
    assert "Contract health operating aligned: `True`" in rendered
    assert "Contract health paper execution aligned: `True`" in rendered
    assert "Contract health aligned: `True`" in rendered
    assert "Contract health partitioned: `True`" in rendered
    assert "Paper nightly: `BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0`" in rendered
    assert "Paper exit duplicate run: `True`" in rendered
    assert "Paper ledger consistent: `True`" in rendered
    assert "Paper ledger snapshot: `paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1`" in rendered
    assert "## Carry" in rendered
    assert "## Walk-Forward" in rendered
    assert "## Open First" in rendered
    assert "## Practical Gate" in rendered
    assert "## Research Stack" in rendered
    assert "## Quick-Read Contract" in rendered
    assert "## Paper Nightly" in rendered
    assert "`analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md`" in rendered
    assert "`analysis_results\\btc_1d_execution_contract_screen_md_latest.md`" in rendered
    assert "`analysis_results\\btc_1d_meta_contract_screen_md_latest.md`" in rendered
    assert "`analysis_results\\btc_1d_paper_nightly_summary_md_latest.md`" in rendered
    standard_pos = rendered.index("## Standard Check Order")
    regression_lock_pos = rendered.index("Regression lock: `tests/unit/test_btc_1d_operating_cli_help_contract.py`")
    execution_pos = rendered.index("Execution health: `BTC 1d practical health | status=btc_only_practical_with_caveats")
    execution_contract_health_pos = rendered.index("Execution contract health: `BTC 1d practical health | status=btc_only_practical_with_caveats")
    execution_contract_pos = rendered.index("Execution contract read: `execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0`")
    practical_pos = rendered.index("Practical status: `btc_only_practical_with_caveats`")
    combined_pos = rendered.index("Combined health: `BTC 1d practical health | status=btc_only_practical_with_caveats")
    research_pos = rendered.index("Research stack status: `BTC 1d research stack | frontier=ratio112_tighter_stop_main")
    contract_line_pos = rendered.index("Contract health: `BTC 1d contract health | operating_brief=operating_v3")
    paper_line_pos = rendered.index("Paper nightly: `BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0`")
    contract_pos = rendered.index("## Quick-Read Contract")
    paper_pos = rendered.index("## Paper Nightly")
    open_first_pos = rendered.index("## Open First")
    carry_pos = rendered.index("## Carry")
    execution_contract_aligned_pos = rendered.index("Execution contract aligned: `True`")
    execution_contract_snapshot_summary_aligned_pos = rendered.index(
        "Execution contract paper ledger snapshot summary aligned: `True`"
    )
    paper_execution_contract_checked_pos = rendered.index("Paper execution contract checked: `True`")
    paper_execution_contract_aligned_pos = rendered.index("Paper execution contract aligned: `True`")
    paper_execution_contract_checked_aligned_pos = rendered.index(
        "Paper execution contract checked aligned: `True`"
    )
    paper_execution_contract_aligned_aligned_pos = rendered.index(
        "Paper execution contract aligned aligned: `True`"
    )
    paper_execution_contract_checked_summary_aligned_pos = rendered.index(
        "Paper execution contract checked summary aligned: `True`"
    )
    paper_execution_contract_aligned_summary_aligned_pos = rendered.index(
        "Paper execution contract aligned summary aligned: `True`"
    )
    assert standard_pos < regression_lock_pos < execution_pos < execution_contract_health_pos < execution_contract_pos < execution_contract_aligned_pos < execution_contract_snapshot_summary_aligned_pos < paper_execution_contract_checked_pos < paper_execution_contract_aligned_pos < paper_execution_contract_checked_aligned_pos < paper_execution_contract_aligned_aligned_pos < paper_execution_contract_checked_summary_aligned_pos < paper_execution_contract_aligned_summary_aligned_pos < practical_pos < combined_pos < research_pos < contract_line_pos < paper_line_pos < contract_pos < paper_pos < open_first_pos < carry_pos


def test_build_operating_brief_reflects_remote_monitoring_handoff_surface(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir / "btc_1d_latest_summary_latest.json",
        {
            "candidate": "low_vol_cap_050_025_minvol020_p2200",
            "scope": "BTC-only",
            "shadow_decision": "shadow_ready_for_btc_only",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "operator_verdict": "shadow_monitoring_ready",
            "quick_read_order_version": "operating_v3",
            "quick_read_order": ["practical_status", "combined_health", "research_stack_status", "contract", "brief"],
            "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit",
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": True,
            "attack_challenger_live_shadow_locked_release_governance_entry_ready": True,
            "attack_challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue",
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_remote_monitoring_deployment_handoff_lane": ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE,
            "attack_challenger_next_step": "deployment monitoring active",
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
            "combined_health_line": "practical || research || contract",
            "research_stack_status": "research healthy",
            "contract_health_line": "BTC 1d contract health | aligned=True",
            "execution_contract_health_line": "execution health || execution contract",
            "execution_contract_read": "execution contract | aligned | paper execution",
            "paper_execution_read": "paper execution | track=operating | applied=0 | closed=0 | open=0",
            "paper_execution_contract_aligned": True,
            "paper_ledger_consistent": True,
            "paper_exit_duplicate_run": False,
            "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=0 | exit_fills=0 | orders=0 | fills=0",
            "contract_health_aligned": True,
            "latest_summary_md": "analysis_results\\btc_1d_latest_summary_md_latest.md",
            "shadow_packet_md": "analysis_results\\btc_1d_shadow_packet_md_latest.md",
            "status_board_md": "analysis_results\\btc_1d_candidate_status_board_md_latest.md",
            "baseline_freeze_md": "analysis_results\\btc_1d_baseline_freeze_md_latest.md",
            "shadow_readiness_md": "analysis_results\\btc_1d_shadow_readiness_md_latest.md",
            "checks": {
                "carry": {"periods": 2200, "decision": "PASS", "sharpe": 1.1, "cagr": 0.2, "max_drawdown": 0.1},
                "survivability": {"periods": 2600, "decision": "PASS", "sharpe": 1.0, "cagr": 0.18, "max_drawdown": 0.12},
                "walk_forward": {
                    "passed": True,
                    "oos_sharpe": 0.8,
                    "oos_cagr": 0.1,
                    "oos_max_drawdown": 0.08,
                    "sensitivity_max_drift": 0.09,
                    "unstable_parameters": [],
                },
                "friction": {"decision": "continue", "heaviest_level_bps": 20, "heaviest_level_sharpe": 0.7},
                "eth_cross_check": {"symbol": "ETHUSDT", "pass_rate": 0.0, "pass_count": 0, "total_count": 4},
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_contract_screen_latest.json",
        {
            "execution_contract_summary": {
                "paper_ledger_snapshot_summary_aligned": True,
            },
            "execution_contract_verdict": {
                "execution_contract_aligned": True,
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "operating_brief": {
                "attack_frontier": "ratio112_tighter_stop_main",
                "attack_backup": "ratio111_tighter_stop_backup",
                "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
                "highest_priority_near_miss": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
            },
            "models": {
                "attack_main": {"base_cagr": 0.4243, "base_mdd": 0.1609, "base_sharpe": 1.5613},
                "attack_backup": {"sensitivity_max_drift": 0.4172},
                "defensive_hold": {"status_label": "candidate_stage_hold"},
                "highest_priority_near_miss": {"candidate_stage_status": "validated_fail_hold"},
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "execution_contract_checked": True,
            "execution_contract_aligned": True,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "quick_read_order_version": "operating_v3",
            "quick_read_order": ["practical_status", "combined_health", "research_stack_status", "contract", "brief"],
        },
    )

    brief = build_operating_brief(analysis_dir=analysis_dir)

    assert brief["attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert (
        brief["attack_challenger_remote_monitoring_deployment_handoff_lane"]
        == ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE
    )
    assert (
        brief["attack_challenger_next_step"]
        == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
    )
    assert brief["deployment_monitoring_active"] is True
    assert (
        brief["attack_challenger_bridge_report"]
        == "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )
    rendered = render_operating_brief(brief)
    rendered_md = render_operating_brief_markdown(brief)
    assert (
        "attack_challenger_remote_monitoring_deployment_handoff_lane: "
        f"{ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE}"
    ) in rendered
    assert (
        "attack_challenger_bridge_report: "
        "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    ) in rendered
    assert "deployment_monitoring_active: True" in rendered
    assert (
        f"next `{ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP}`" in rendered_md
    )
    assert "Deployment monitoring active: `True`" in rendered_md
    assert (
        f"remote_monitoring_deployment_handoff_lane `{ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE}`"
    ) in rendered_md
    assert (
        "- Attack challenger bridge report: "
        "`analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json`"
    ) in rendered_md
