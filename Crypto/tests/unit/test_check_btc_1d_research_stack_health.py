from __future__ import annotations

import json
from pathlib import Path

from scripts.btc_1d_handoff_constants import (
    ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
)
from scripts.check_btc_1d_research_stack_health import (
    build_parser,
    check_research_stack_health,
    render_research_stack_health_line,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_research_stack_health_parser_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.analysis_dir == Path("analysis_results")
    assert args.as_json is False


def test_check_research_stack_health_reads_latest_brief(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "standard_check_order_reference": ["practical", "research", "contract", "brief"],
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
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
        },
    )

    result = check_research_stack_health(analysis_dir=analysis_dir)

    assert result["regression_lock_test"] == "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    assert result["standard_check_order_reference"] == ["practical", "research", "contract", "brief"]
    assert result["attack_frontier"] == "ratio112_tighter_stop_main"
    assert result["attack_backup"] == "bridge_28_relief"
    assert result["attack_challenger"] == "post_spike_trend960_depth055_volume100_hold36"
    assert result["attack_challenger_status"] == "active_post_spike_challenger"
    assert result["hold36_status_band"] == "pressure_watch"
    assert result["hold36_do_not_repeat_local_loop"] is True
    assert result["near_miss_status"] == "validated_fail_hold"
    assert result["attack_frontier_sharpe"] == 1.5613
    assert result["attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert (
        result["attack_challenger_next_step"]
        == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
    )
    assert (
        result["attack_challenger_bridge_report"]
        == "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )


def test_render_research_stack_health_line_includes_core_fields() -> None:
    rendered = render_research_stack_health_line(
        {
            "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
            "attack_frontier": "ratio112_tighter_stop_main",
            "attack_backup": "bridge_28_relief",
            "attack_challenger": "post_spike_trend960_depth055_volume100_hold36",
            "highest_priority_near_miss": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
            "attack_frontier_cagr": 0.4243,
            "attack_frontier_max_drawdown": 0.1609,
            "attack_frontier_sharpe": 1.5613,
            "attack_backup_drift": 0.1322,
            "attack_challenger_status": "active_post_spike_challenger",
            "attack_challenger_cagr": 0.3078,
            "hold36_status_band": "pressure_watch",
            "hold36_primary_blocker": "base_cagr_gap",
            "hold36_do_not_repeat_local_loop": True,
            "near_miss_status": "validated_fail_hold",
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
        }
    )

    assert "BTC 1d research stack" in rendered
    assert "frontier=ratio112_tighter_stop_main" in rendered
    assert "backup=bridge_28_relief" in rendered
    assert "challenger=post_spike_trend960_depth055_volume100_hold36" in rendered
    assert "hold36_ceiling=pressure_watch/base_cagr_gap (do_not_repeat=True)" in rendered
    assert "validated_fail_hold" in rendered
    assert (
        f"attack_challenger_next={ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP}"
        in rendered
    )
