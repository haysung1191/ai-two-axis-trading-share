from __future__ import annotations

from scripts.run_btc_1d_walk_forward_volatility_expansion_reclaim_cooldown_sr121_candidate import parse_args as parse_walk_args
from scripts.validate_btc_1d_volatility_expansion_reclaim_cooldown_sr121_candidate import parse_args as parse_validation_args


def test_validate_btc_1d_volatility_expansion_reclaim_cooldown_sr121_candidate_defaults() -> None:
    config = parse_validation_args([])
    assert config.periods == 2600
    assert config.strategy_name == "btc_1d_volatility_expansion_reclaim_cdf12sr121"
    assert config.extra_parameters["min_atr_expansion_ratio"] == 1.21
    assert config.extra_parameters["cooldown_bars"] == 12
    assert config.extra_parameters["min_trend_slope_ratio"] == 0.0028


def test_run_btc_1d_walk_forward_volatility_expansion_reclaim_cooldown_sr121_candidate_defaults() -> None:
    config = parse_walk_args([])
    assert config.periods == 2600
    assert config.strategy_name == "btc_1d_volatility_expansion_reclaim_cdf12sr121"
    assert config.extra_parameters["min_atr_expansion_ratio"] == 1.21
    assert config.candidate_label == "volatility_expansion_reclaim_cooldown_sr121"
