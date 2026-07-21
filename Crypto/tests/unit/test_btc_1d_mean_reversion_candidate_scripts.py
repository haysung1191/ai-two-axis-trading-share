from __future__ import annotations

from scripts.run_btc_1d_walk_forward_mean_reversion import parse_args as parse_walk_args
from scripts.validate_btc_1d_mean_reversion_candidate import parse_args as parse_validation_args


def test_validate_btc_1d_mean_reversion_candidate_defaults() -> None:
    config = parse_validation_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "mean_reversion"
    assert config.extra_parameters["window"] == 20
    assert config.extra_parameters["z_threshold"] == 1.0


def test_run_btc_1d_walk_forward_mean_reversion_defaults() -> None:
    config = parse_walk_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.window == 20
    assert config.z_threshold == 1.0
    assert config.candidate_label == "btc_1d_mean_reversion_w20_z1.0"
