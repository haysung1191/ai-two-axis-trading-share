from __future__ import annotations

import json
from pathlib import Path

from scripts.build_btc_1d_shadow_packet import build_shadow_packet


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_btc_1d_shadow_packet_reads_latest_artifacts(tmp_path: Path) -> None:
    analysis = tmp_path / "analysis"
    analysis.mkdir()
    _write_json(
        analysis / "btc_1d_baseline_freeze_20260413T000000Z.json",
        {
            "frozen_candidate": "low_vol_cap_045_025_minvol020_p2200",
        },
    )
    _write_json(
        analysis / "btc_1d_candidate_status_board_20260413T000001Z.json",
        {
            "active_candidate": "low_vol_cap_045_025_minvol020_p2200",
            "status": "carryable_candidate",
            "carry_reference_period": 2200,
            "survivability_reference_period": 2600,
        },
    )
    _write_json(
        analysis / "btc_1d_shadow_readiness_20260413T000002Z.json",
        {
            "decision": "shadow_ready_for_btc_only",
        },
    )
    _write_json(
        analysis / "btc_1d_low_vol_cap_friction_20260413T000002Z.json",
        {
            "final_decision": "continue",
            "decision_reason": "baseline remains paper-valid even under the heaviest tested friction.",
            "levels": [
                {"cost_bps": 0.0, "decision": "PASS"},
                {"cost_bps": 20.0, "decision": "PASS", "sharpe": 1.04, "cagr": 0.12, "max_drawdown": 0.12, "win_rate": 0.50, "trades": 215},
            ],
        },
    )
    _write_json(
        analysis / "btc_1d_walk_forward_diagnostic_20260413T000002Z.json",
        {
            "config": {"periods": 2200},
            "overfitting": {
                "passed": True,
                "summary": "stable",
                "oos_metrics": {"sharpe": 0.82, "cagr": 0.11, "max_drawdown": 0.10},
                "sensitivity_max_drift": 0.09,
                "unstable_parameters": [],
            },
        },
    )
    _write_json(
        analysis / "btc_1d_promoted_candidate_regression_20260413T000002Z.json",
        {
            "config": {"symbol": "ETHUSDT"},
            "summary": {"pass_rate": 0.0},
            "results": [
                {"periods": 2200, "decision": "DROP", "sharpe": 0.85, "max_drawdown": 0.31},
                {"periods": 2600, "decision": "DROP", "sharpe": 0.86, "max_drawdown": 0.32},
            ],
        },
    )
    _write_json(
        analysis / "btc_1d_ema_trend_atr_exit_paper_validation_20260413T000003Z.json",
        {
            "config": {
                "periods": 2200,
                "ema_fast_window": 20,
                "ema_slow_window": 50,
                "atr_window": 14,
                "atr_multiple": 3.5,
                "time_stop_bars": 90,
                "extra_parameters": {
                    "regime_exit_confirmation_bars": 2,
                    "volatility_window": 20,
                    "volatility_target": 0.2,
                    "min_position_size": 0.35,
                    "min_annualized_volatility": 0.2,
                    "low_volatility_cap_threshold": 0.45,
                    "low_volatility_position_cap": 0.25,
                },
            },
            "decision_record": {
                "decision": "PASS",
                "key_metrics": {
                    "sharpe": 1.1,
                    "cagr": 0.14,
                    "max_drawdown": 0.12,
                    "win_rate": 0.51,
                    "trades": 317,
                    "completed_trades": 265,
                },
            },
        },
    )
    _write_json(
        analysis / "btc_1d_ema_trend_atr_exit_paper_validation_20260413T000004Z.json",
        {
            "config": {
                "periods": 2600,
                "ema_fast_window": 20,
                "ema_slow_window": 50,
                "atr_window": 14,
                "atr_multiple": 3.5,
                "time_stop_bars": 90,
                "extra_parameters": {
                    "regime_exit_confirmation_bars": 2,
                    "volatility_window": 20,
                    "volatility_target": 0.2,
                    "min_position_size": 0.35,
                    "min_annualized_volatility": 0.2,
                    "low_volatility_cap_threshold": 0.45,
                    "low_volatility_position_cap": 0.25,
                },
            },
            "decision_record": {
                "decision": "PASS",
                "key_metrics": {
                    "sharpe": 1.05,
                    "cagr": 0.15,
                    "max_drawdown": 0.13,
                    "win_rate": 0.52,
                    "trades": 364,
                    "completed_trades": 301,
                },
            },
        },
    )

    packet = build_shadow_packet(analysis_dir=analysis)

    assert packet["candidate"] == "low_vol_cap_045_025_minvol020_p2200"
    assert packet["shadow_decision"] == "shadow_ready_for_btc_only"
    assert packet["paper_validation_decision"] == "PASS"
    assert packet["survivability_validation_decision"] == "PASS"
    assert packet["friction_validation_decision"] == "continue"
    assert packet["friction_validation_heaviest_level"]["cost_bps"] == 20.0
    assert packet["walk_forward"]["passed"] is True
    assert packet["walk_forward"]["oos_metrics"]["sharpe"] == 0.82
    assert packet["eth_regression_summary"]["pass_rate"] == 0.0
    assert packet["eth_regression_read"]["2200"]["decision"] == "DROP"
    assert packet["survivability_validation_metrics"]["trades"] == 364
    assert packet["parameters"]["min_annualized_volatility"] == 0.2
