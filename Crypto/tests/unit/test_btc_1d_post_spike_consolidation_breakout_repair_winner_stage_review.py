from __future__ import annotations

import json
from pathlib import Path

from scripts.compare_btc_1d_post_spike_consolidation_breakout_repair_winner_stage_review import build_report


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_repair_winner_stage_review_marks_ready_when_negative_window_is_removed(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch_20260420T000000Z.json",
        {
            "best_variant": {
                "variant_label": "trend864_depth055_volume108",
                "strategy_name": "btc_1d_post_spike_consolidation_breakout_v4",
                "analysis_result_json": str(tmp_path / "btc_1d_walk_forward_diagnostic_20260419T171733Z.json"),
                "parameters": {
                    "trend_ema_window": 86.4,
                    "spike_lookback": 24,
                    "min_spike_pct": 0.085,
                    "consolidation_window": 7,
                    "max_consolidation_depth_pct": 0.055,
                    "breakout_buffer_pct": 0.002,
                    "volume_lookback": 20,
                    "min_volume_ratio": 1.08,
                    "stop_ema_window": 20,
                    "max_hold_bars": 36,
                },
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_v4_btcusdt_1d_2200_trend864_depth055_volume100_hold32_paper_validation_20260419T170649Z.json",
        {
            "decision_record": {
                "decision": "PASS",
                "key_metrics": {"sharpe": 1.67, "cagr": 0.305, "max_drawdown": 0.127},
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_v4_btcusdt_1d_2200_trend864_depth055_volume108_friction_8bps_paper_validation_20260419T172818Z.json",
        {
            "decision_record": {
                "decision": "PASS",
                "key_metrics": {"sharpe": 1.649, "cagr": 0.320, "max_drawdown": 0.127},
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_v4_btcusdt_1d_2200_trend864_depth055_volume108_friction_20bps_paper_validation_20260419T172930Z.json",
        {
            "decision_record": {
                "decision": "PASS",
                "key_metrics": {"sharpe": 1.585, "cagr": 0.306, "max_drawdown": 0.135},
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260419T171733Z.json",
        {
            "config": {"candidate_label": "post_spike_walk_forward_repair::trend864_depth055_volume108"},
            "overfitting": {
                "passed": True,
                "sensitivity_max_drift": 0.184,
                "unstable_parameters": [],
                "walk_forward": [
                    {"window": 1, "metrics": {"trades": 6, "sharpe": 2.14, "cagr": 0.56}},
                    {"window": 2, "metrics": {"trades": 0, "sharpe": 0.0, "cagr": 0.0}},
                    {"window": 5, "metrics": {"trades": 6, "sharpe": 0.73, "cagr": 0.08}},
                ],
            },
        },
    )

    report = build_report(analysis_dir=tmp_path)
    verdict = report["repair_winner_stage_verdict"]
    profile = report["repair_winner_profile"]

    assert verdict["candidate_stage_ready"] is True
    assert verdict["next_step_now"] == "replace_anchor_candidate_with_repair_winner"
    assert profile["negative_walk_forward_windows"] == []
    assert profile["idle_walk_forward_windows"] == [2]
