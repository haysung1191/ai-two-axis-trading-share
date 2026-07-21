from __future__ import annotations

from scripts.run_btc_1d_shallow_liquidity_void_refill_repair_step import (
    build_candidate_repair_report,
    build_friction_repair_report,
)


def test_void_refill_candidate_repair_stays_in_loop_when_sensitivity_fails() -> None:
    validation_result = {
        "run_id": "demo-run",
        "analysis_result_json": "analysis_results/demo.json",
        "config": {"strategy_name": "btc_1d_shallow_liquidity_void_refill_continuation_exit_v1"},
        "decision_record": {
            "decision": "FAIL",
            "failed_gates": ["overfitting_flags", "overfitting_pass", "overfitting_sensitivity"],
            "key_metrics": {
                "cagr": 0.2407,
                "max_drawdown": 0.1661,
                "sharpe": 1.1884,
                "win_rate": 0.513,
                "trades": 26.0,
            },
        },
    }

    report = build_candidate_repair_report(
        step="candidate_repair_retest",
        validation_result=validation_result,
    )

    assert report["repair_gate_check"]["clears_overfitting_sensitivity"] is False
    assert report["step_verdict"]["status"] == "stay_in_candidate_repair_loop"
    assert report["step_verdict"]["next_step"] == "continue_candidate_repair_search"


def test_void_refill_candidate_repair_advances_when_sensitivity_clears() -> None:
    validation_result = {
        "run_id": "demo-run",
        "analysis_result_json": "analysis_results/demo.json",
        "config": {"strategy_name": "btc_1d_shallow_liquidity_void_refill_continuation_exit_v1"},
        "decision_record": {
            "decision": "PASS",
            "failed_gates": [],
            "key_metrics": {
                "cagr": 0.231,
                "max_drawdown": 0.175,
                "sharpe": 1.05,
                "win_rate": 0.51,
                "trades": 26.0,
            },
        },
    }

    report = build_candidate_repair_report(
        step="candidate_repair_retest",
        validation_result=validation_result,
    )

    assert report["repair_gate_check"]["clears_overfitting_sensitivity"] is True
    assert report["step_verdict"]["status"] == "advance_to_friction_retest"
    assert report["step_verdict"]["next_step"] == "friction_retest"


def test_void_refill_friction_repair_stays_when_lane_is_still_paused() -> None:
    friction_result = {
        "report_json_path": None,
        "report_md_path": None,
        "final_decision": "pause",
        "decision_reason": "still blocked",
        "levels": [
            {
                "cost_bps": 0.0,
                "decision": "FAIL",
                "cagr": 0.2407,
                "max_drawdown": 0.1661,
                "sharpe": 1.1884,
                "failed_gates": ["overfitting_flags", "overfitting_pass", "overfitting_sensitivity"],
            }
        ],
    }

    report = build_friction_repair_report(step="friction_retest", friction_result=friction_result)

    assert report["repair_gate_check"]["flips_pause_decision"] is False
    assert report["step_verdict"]["status"] == "stay_in_friction_repair_loop"
    assert report["step_verdict"]["next_step"] == "continue_friction_repair_search"


def test_void_refill_friction_repair_advances_when_pause_flips() -> None:
    friction_result = {
        "report_json_path": None,
        "report_md_path": None,
        "final_decision": "continue_with_caution",
        "decision_reason": "recovered",
        "levels": [
            {
                "cost_bps": 0.0,
                "decision": "PASS",
                "cagr": 0.231,
                "max_drawdown": 0.175,
                "sharpe": 1.05,
                "failed_gates": [],
            }
        ],
    }

    report = build_friction_repair_report(step="friction_retest", friction_result=friction_result)

    assert report["repair_gate_check"]["flips_pause_decision"] is True
    assert report["repair_gate_check"]["clears_overfitting_sensitivity"] is True
    assert report["step_verdict"]["status"] == "advance_to_exit_compression_retest"
    assert report["step_verdict"]["next_step"] == "exit_compression_retest"
