from __future__ import annotations

import json
from pathlib import Path

from scripts.compare_btc_1d_post_spike_consolidation_breakout_candidate_stage_review import build_report
from scripts.run_btc_1d_walk_forward_post_spike_consolidation_breakout_candidate import (
    parse_args as parse_walk_forward_args,
)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_post_spike_walk_forward_defaults() -> None:
    config = parse_walk_forward_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "btc_1d_post_spike_consolidation_breakout_v4"
    assert config.candidate_label == "post_spike_consolidation_breakout_trend960_depth055_volume100_hold36"
    assert config.extra_parameters["max_consolidation_depth_pct"] == 0.055
    assert config.extra_parameters["min_volume_ratio"] == 1.0
    assert config.extra_parameters["max_hold_bars"] == 36.0


def test_post_spike_candidate_stage_review_holds_when_walk_forward_has_negative_window(tmp_path: Path) -> None:
    validation_path = (
        tmp_path / "btc_1d_post_spike_consolidation_breakout_v4_btcusdt_1d_2200_trend960_depth055_volume100_hold36_paper_validation_20260420T000000Z.json"
    )
    _write_json(
        validation_path,
        {
            "decision_record": {
                "decision": "PASS",
                "key_metrics": {"sharpe": 1.67, "cagr": 0.30, "max_drawdown": 0.13},
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_friction_20260420T000100Z.json",
        {
            "candidate": "post_spike_consolidation_breakout_trend960_depth055_volume100_hold36",
            "final_decision": "continue",
            "levels": [{"cost_bps": 8.0, "analysis_result_json": str(validation_path)}],
        },
    )
    _write_json(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260420T000200Z.json",
        {
            "config": {"candidate_label": "post_spike_consolidation_breakout_trend960_depth055_volume100_hold36"},
            "overfitting": {
                "passed": True,
                "sensitivity_max_drift": 0.18,
                "unstable_parameters": [],
                "walk_forward": [
                    {"window": 1, "metrics": {"sharpe": 1.3, "cagr": 0.28, "trades": 3}},
                    {"window": 4, "metrics": {"sharpe": -0.2, "cagr": -0.01, "trades": 1}},
                ],
            },
        },
    )

    report = build_report(analysis_dir=tmp_path)
    verdict = report["post_spike_candidate_stage_review_verdict"]
    candidate = report["candidate_profile"]

    assert verdict["candidate_stage_ready"] is False
    assert verdict["candidate_stage_lane"] == "post_spike_candidate_stage_repair_hold"
    assert verdict["next_step_now"] == "repair_candidate_walk_forward_or_sensitivity"
    assert verdict["failed_requirements"] == ["walk_forward_no_negative_window"]
    assert candidate["negative_walk_forward_windows"] == [4]


def test_post_spike_candidate_stage_review_reason_lists_failed_requirements(tmp_path: Path) -> None:
    validation_path = (
        tmp_path / "btc_1d_post_spike_consolidation_breakout_v4_btcusdt_1d_2200_trend960_depth055_volume100_hold36_paper_validation_20260420T000000Z.json"
    )
    _write_json(
        validation_path,
        {
            "decision_record": {
                "decision": "FAIL",
                "key_metrics": {"sharpe": 1.64, "cagr": 0.26, "max_drawdown": 0.07},
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_friction_20260420T000100Z.json",
        {
            "candidate": "post_spike_consolidation_breakout_trend960_depth055_volume100_hold36",
            "final_decision": "pause",
            "levels": [{"cost_bps": 8.0, "analysis_result_json": str(validation_path)}],
        },
    )
    _write_json(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260420T000200Z.json",
        {
            "config": {"candidate_label": "post_spike_consolidation_breakout_trend960_depth055_volume100_hold36"},
            "overfitting": {
                "passed": False,
                "sensitivity_max_drift": 0.39,
                "unstable_parameters": ["min_volume_ratio"],
                "walk_forward": [
                    {"window": 5, "metrics": {"sharpe": -0.1, "cagr": -0.02, "trades": 1}},
                ],
            },
        },
    )

    report = build_report(analysis_dir=tmp_path)
    verdict = report["post_spike_candidate_stage_review_verdict"]

    assert verdict["candidate_stage_ready"] is False
    assert "paper_validation_passed" in verdict["failed_requirements"]
    assert "friction_stays_green" in verdict["failed_requirements"]
    assert "sensitivity_drift_within_guardrail" in verdict["failed_requirements"]
    assert "unstable_parameters_clear" in verdict["failed_requirements"]
    assert "paper_validation_passed" in verdict["reason"]


def test_post_spike_candidate_stage_review_marks_ready_when_all_gates_are_green(tmp_path: Path) -> None:
    validation_path = (
        tmp_path / "btc_1d_post_spike_consolidation_breakout_v4_btcusdt_1d_2200_trend960_depth055_volume100_hold36_paper_validation_20260420T000000Z.json"
    )
    _write_json(
        validation_path,
        {
            "decision_record": {
                "decision": "PASS",
                "key_metrics": {"sharpe": 1.67, "cagr": 0.30, "max_drawdown": 0.13},
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_friction_20260420T000100Z.json",
        {
            "candidate": "post_spike_consolidation_breakout_trend960_depth055_volume100_hold36",
            "final_decision": "continue",
            "levels": [{"cost_bps": 8.0, "analysis_result_json": str(validation_path)}],
        },
    )
    _write_json(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260420T000200Z.json",
        {
            "config": {"candidate_label": "post_spike_consolidation_breakout_trend960_depth055_volume100_hold36"},
            "overfitting": {
                "passed": True,
                "sensitivity_max_drift": 0.18,
                "unstable_parameters": [],
                "walk_forward": [
                    {"window": 1, "metrics": {"sharpe": 1.3, "cagr": 0.28, "trades": 3}},
                    {"window": 2, "metrics": {"sharpe": 0.9, "cagr": 0.16, "trades": 2}},
                ],
            },
        },
    )

    report = build_report(analysis_dir=tmp_path)
    verdict = report["post_spike_candidate_stage_review_verdict"]

    assert verdict["candidate_stage_ready"] is True
    assert verdict["candidate_stage_lane"] == "post_spike_candidate_stage_promotion_queue"
    assert verdict["next_step_now"] == "promote_candidate_into_attack_comparison"
