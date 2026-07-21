from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_btc_1d_post_spike_consolidation_breakout_repair_winner import parse_args


def test_repair_winner_validation_defaults_follow_latest_batch(tmp_path: Path, monkeypatch) -> None:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir()
    payload = {
        "best_variant": {
            "variant_label": "trend864_depth055_volume108",
            "strategy_name": "btc_1d_post_spike_consolidation_breakout_v4",
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
    }
    (analysis_dir / "btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch_20260420T000000Z.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    config = parse_args(["--analysis-dir", "analysis_results"])

    assert config.strategy_name == "btc_1d_post_spike_consolidation_breakout_v4"
    assert config.artifact_label == "btcusdt_1d_2200_trend864_depth055_volume108_friction_8bps"
    assert config.extra_parameters["trend_ema_window"] == 86.4
    assert config.extra_parameters["max_consolidation_depth_pct"] == 0.055
