from __future__ import annotations

from scripts.run_btc_1d_secondary_repair_step import (
    build_secondary_parameter_repair_report,
    build_secondary_repair_step_report,
)


def test_secondary_repair_step_stays_in_candidate_loop_when_drawdown_gate_fails() -> None:
    validation_result = {
        "run_id": "demo-run",
        "analysis_result_json": "analysis_results/demo.json",
        "config": {"strategy_name": "btc_1d_volatility_spike_reversal_continuation_exit_v2"},
        "decision_record": {
            "decision": "FAIL",
            "failed_gates": ["backtest_max_drawdown"],
            "key_metrics": {
                "cagr": 0.33764892,
                "max_drawdown": 0.25968288,
                "sharpe": 1.10097698,
                "win_rate": 0.5266559,
                "completed_trades": 46.0,
            },
        },
    }

    report = build_secondary_repair_step_report(
        step="candidate_repair_retest",
        validation_result=validation_result,
    )

    assert report["repair_gate_check"]["clears_drawdown_gate"] is False
    assert report["step_verdict"]["status"] == "stay_in_candidate_repair_loop"
    assert report["step_verdict"]["next_step"] == "candidate_parameter_repair"


def test_secondary_repair_step_advances_when_drawdown_gate_clears() -> None:
    validation_result = {
        "run_id": "demo-run",
        "analysis_result_json": "analysis_results/demo.json",
        "config": {"strategy_name": "btc_1d_volatility_spike_reversal_continuation_exit_v2"},
        "decision_record": {
            "decision": "PASS",
            "failed_gates": [],
            "key_metrics": {
                "cagr": 0.301,
                "max_drawdown": 0.219,
                "sharpe": 1.05,
                "win_rate": 0.51,
                "completed_trades": 46.0,
            },
        },
    }

    report = build_secondary_repair_step_report(
        step="candidate_repair_retest",
        validation_result=validation_result,
    )

    assert report["repair_gate_check"]["clears_drawdown_gate"] is True
    assert report["step_verdict"]["status"] == "advance_to_friction_retest"
    assert report["step_verdict"]["next_step"] == "friction_retest"


def test_secondary_parameter_repair_exhausts_when_current_variant_is_still_best() -> None:
    batch_result = {
        "run_id": "demo-run",
        "analysis_result_json": "analysis_results/demo.json",
        "analysis_result_csv": "analysis_results/demo.csv",
        "results": [
            {
                "variant_label": "current_reference",
                "strategy_name": "btc_1d_volatility_spike_reversal_continuation_exit_v1",
                "cagr": 0.4045141,
                "max_drawdown": 0.28714206,
                "sharpe": 1.23766822,
                "failed_gates": ["backtest_max_drawdown"],
            },
            {
                "variant_label": "tighter_stop",
                "strategy_name": "btc_1d_volatility_spike_reversal_continuation_exit_v2",
                "cagr": 0.33764892,
                "max_drawdown": 0.25968288,
                "sharpe": 1.10097698,
                "failed_gates": ["backtest_max_drawdown"],
            },
        ],
    }

    report = build_secondary_parameter_repair_report(
        step="candidate_parameter_repair",
        batch_result=batch_result,
    )

    assert report["repair_gate_check"]["improves_drawdown_vs_current"] is False
    assert report["step_verdict"]["status"] == "secondary_repair_exhausted"
    assert report["step_verdict"]["next_step"] == "new_family_search_or_secondary_reframe"


def test_secondary_parameter_repair_advances_when_new_variant_beats_current() -> None:
    batch_result = {
        "run_id": "demo-run",
        "analysis_result_json": "analysis_results/demo.json",
        "analysis_result_csv": "analysis_results/demo.csv",
        "results": [
            {
                "variant_label": "tighter_stop",
                "strategy_name": "btc_1d_volatility_spike_reversal_continuation_exit_v2",
                "cagr": 0.33764892,
                "max_drawdown": 0.25968288,
                "sharpe": 1.10097698,
                "failed_gates": ["backtest_max_drawdown"],
            },
            {
                "variant_label": "repair_candidate",
                "strategy_name": "btc_1d_volatility_spike_reversal_continuation_exit_v5",
                "cagr": 0.301,
                "max_drawdown": 0.239,
                "sharpe": 1.02,
                "failed_gates": [],
            },
        ],
    }

    report = build_secondary_parameter_repair_report(
        step="candidate_parameter_repair",
        batch_result=batch_result,
    )

    assert report["repair_gate_check"]["improves_drawdown_vs_current"] is True
    assert report["step_verdict"]["status"] == "advance_to_friction_retest"
    assert report["step_verdict"]["next_step"] == "friction_retest"
