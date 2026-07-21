from __future__ import annotations

from scripts.run_btc_1d_walk_forward_volatility_expansion_reclaim_sr112_candidate import parse_args as parse_walk_args
from scripts.validate_btc_1d_volatility_expansion_reclaim_sr112_candidate import parse_args as parse_validation_args


def test_validate_btc_1d_volatility_expansion_reclaim_sr112_candidate_defaults() -> None:
    config = parse_validation_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "btc_1d_volatility_expansion_reclaim_sr112"
    assert config.extra_parameters["breakout_window"] == 18
    assert config.extra_parameters["atr_expansion_window"] == 5
    assert config.extra_parameters["min_atr_expansion_ratio"] == 1.12
    assert config.extra_parameters["reclaim_buffer_ratio"] == 0.12
    assert config.extra_parameters["stop_ema_window"] == 18
    assert config.extra_parameters["max_hold_bars"] == 34


def test_run_btc_1d_walk_forward_volatility_expansion_reclaim_sr112_candidate_defaults() -> None:
    config = parse_walk_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "btc_1d_volatility_expansion_reclaim_sr112"
    assert config.candidate_label == "volatility_expansion_reclaim_ratio_112_reference"
    assert config.extra_parameters["breakout_window"] == 18
    assert config.extra_parameters["atr_expansion_window"] == 5
    assert config.extra_parameters["min_atr_expansion_ratio"] == 1.12
    assert config.extra_parameters["reclaim_buffer_ratio"] == 0.12
    assert config.extra_parameters["stop_ema_window"] == 18
    assert config.extra_parameters["max_hold_bars"] == 34
