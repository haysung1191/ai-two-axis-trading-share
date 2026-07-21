from __future__ import annotations

import json
from pathlib import Path

from scripts.compare_btc_1d_pullthrough_candidate_stage_review import build_report


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_pullthrough_candidate_stage_review_holds_when_negative_window_exists(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "btc_1d_volatility_expansion_pullthrough_v3_btcusdt_1d_2200_paper_validation_20260419T000000Z.json",
        {
            "decision_record": {
                "decision": "PASS",
                "key_metrics": {"sharpe": 1.18, "cagr": 0.25, "max_drawdown": 0.16},
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_volatility_expansion_pullthrough_shorthold_friction_20260419T000100Z.json",
        {
            "candidate": "volatility_expansion_pullthrough_softer_setup_hold31",
            "final_decision": "continue",
            "levels": [
                {
                    "cost_bps": 8.0,
                    "analysis_result_json": str(
                        tmp_path
                        / "btc_1d_volatility_expansion_pullthrough_v3_btcusdt_1d_2200_paper_validation_20260419T000000Z.json"
                    ),
                }
            ],
        },
    )
    _write_json(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260419T000200Z.json",
        {
            "config": {"candidate_label": "volatility_expansion_pullthrough_softer_setup_hold31"},
            "overfitting": {
                "passed": True,
                "sensitivity_max_drift": 0.14,
                "unstable_parameters": [],
                "walk_forward": [
                    {"window": 1, "metrics": {"sharpe": 1.2, "cagr": 0.3, "trades": 4}},
                    {"window": 5, "metrics": {"sharpe": -0.5, "cagr": -0.02, "trades": 3}},
                ],
            },
        },
    )

    report = build_report(analysis_dir=tmp_path)

    verdict = report["pullthrough_candidate_stage_review_verdict"]
    candidate = report["candidate_profile"]

    assert verdict["candidate_stage_ready"] is False
    assert verdict["candidate_stage_lane"] == "pullthrough_candidate_stage_repair_hold"
    assert verdict["next_step_now"] == "repair_negative_walk_forward_window"
    assert candidate["negative_walk_forward_windows"] == [5]


def test_pullthrough_candidate_stage_review_marks_ready_when_all_gates_are_green(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "btc_1d_volatility_expansion_pullthrough_v3_btcusdt_1d_2200_paper_validation_20260419T000000Z.json",
        {
            "decision_record": {
                "decision": "PASS",
                "key_metrics": {"sharpe": 1.18, "cagr": 0.25, "max_drawdown": 0.16},
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_volatility_expansion_pullthrough_shorthold_friction_20260419T000100Z.json",
        {
            "candidate": "volatility_expansion_pullthrough_softer_setup_hold31",
            "final_decision": "continue",
            "levels": [
                {
                    "cost_bps": 8.0,
                    "analysis_result_json": str(
                        tmp_path
                        / "btc_1d_volatility_expansion_pullthrough_v3_btcusdt_1d_2200_paper_validation_20260419T000000Z.json"
                    ),
                }
            ],
        },
    )
    _write_json(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260419T000200Z.json",
        {
            "config": {"candidate_label": "volatility_expansion_pullthrough_softer_setup_hold31"},
            "overfitting": {
                "passed": True,
                "sensitivity_max_drift": 0.14,
                "unstable_parameters": [],
                "walk_forward": [
                    {"window": 1, "metrics": {"sharpe": 1.2, "cagr": 0.3, "trades": 4}},
                    {"window": 2, "metrics": {"sharpe": 0.8, "cagr": 0.1, "trades": 2}},
                ],
            },
        },
    )

    report = build_report(analysis_dir=tmp_path)

    verdict = report["pullthrough_candidate_stage_review_verdict"]

    assert verdict["candidate_stage_ready"] is True
    assert verdict["candidate_stage_lane"] == "pullthrough_candidate_stage_promotion_queue"
    assert verdict["next_step_now"] == "promote_candidate_into_attack_comparison"
