from __future__ import annotations

from scripts.run_btc_1d_walk_forward_defensive_cash_filter import parse_args as parse_walk_args
from scripts.validate_btc_1d_defensive_cash_filter_candidate import parse_args as parse_validation_args


def test_validate_btc_1d_defensive_cash_filter_candidate_defaults() -> None:
    config = parse_validation_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "major_4h_defensive_cash_filter"
    assert config.extra_parameters["floor_ema_window"] == 96
    assert config.extra_parameters["max_volatility"] == 0.03


def test_run_btc_1d_walk_forward_defensive_cash_filter_defaults() -> None:
    config = parse_walk_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.candidate_label == "btc_1d_defensive_cash_filter"
    assert config.floor_ema_window == 96
    assert config.max_volatility == 0.03
