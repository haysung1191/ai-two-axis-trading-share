from __future__ import annotations

from scripts.run_btc_1d_walk_forward_low_vol_cap_candidate import parse_args as parse_walk_args
from scripts.validate_btc_1d_low_vol_cap_candidate import parse_args as parse_validation_args


def test_validate_btc_1d_low_vol_cap_candidate_defaults() -> None:
    config = parse_validation_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.extra_parameters["min_annualized_volatility"] == 0.2
    assert config.extra_parameters["low_volatility_cap_threshold"] == 0.50
    assert config.extra_parameters["low_volatility_position_cap"] == 0.25


def test_run_btc_1d_walk_forward_low_vol_cap_candidate_defaults() -> None:
    config = parse_walk_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.candidate_label == "low_vol_cap_050_025_minvol020"
    assert config.extra_parameters["min_annualized_volatility"] == 0.2
    assert config.extra_parameters["low_volatility_cap_threshold"] == 0.50
    assert config.extra_parameters["low_volatility_position_cap"] == 0.25
