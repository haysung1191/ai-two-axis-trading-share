from __future__ import annotations

from scripts.validate_btc_1d_post_spike_consolidation_breakout_candidate import (
    parse_args as parse_validation_args,
)
from scripts.validate_btc_1d_post_spike_consolidation_breakout_friction import build_parser


def test_validate_btc_1d_post_spike_consolidation_breakout_candidate_defaults() -> None:
    config = parse_validation_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "btc_1d_post_spike_consolidation_breakout_v4"
    assert config.artifact_label == "btcusdt_1d_2200_trend960_depth055_volume100_hold36"
    assert config.extra_parameters["min_spike_pct"] == 0.085
    assert config.extra_parameters["trend_ema_window"] == 96.0
    assert config.extra_parameters["max_consolidation_depth_pct"] == 0.055
    assert config.extra_parameters["min_volume_ratio"] == 1.0
    assert config.extra_parameters["max_hold_bars"] == 36.0


def test_btc_1d_post_spike_consolidation_breakout_friction_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.periods == 2200
    assert args.cost_levels_bps == [0.0, 8.0, 12.0, 20.0]
