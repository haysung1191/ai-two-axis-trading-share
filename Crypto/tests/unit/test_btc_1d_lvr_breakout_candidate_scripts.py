from __future__ import annotations

from scripts.run_btc_1d_walk_forward_lvr_breakout_candidate import parse_args as parse_walk_args
from scripts.validate_btc_1d_lvr_breakout_candidate import parse_args as parse_validation_args


def test_validate_btc_1d_lvr_breakout_candidate_defaults() -> None:
    config = parse_validation_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "btc_1d_lvr_breakout"
    assert config.extra_parameters["trend_ema_window"] == 96
    assert config.extra_parameters["min_volume_ratio"] == 1.6


def test_run_btc_1d_walk_forward_lvr_breakout_candidate_defaults() -> None:
    config = parse_walk_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "btc_1d_lvr_breakout"
    assert config.candidate_label == "lvr_breakout_slower_trend_cleaner_breakout"
    assert config.extra_parameters["trend_ema_window"] == 96
    assert config.extra_parameters["min_volume_ratio"] == 1.6
