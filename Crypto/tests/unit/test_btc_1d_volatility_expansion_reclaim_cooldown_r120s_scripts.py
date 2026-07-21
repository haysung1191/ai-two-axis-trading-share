from __future__ import annotations

from scripts.run_btc_1d_walk_forward_volatility_expansion_reclaim_cooldown_r120s_candidate import parse_args as parse_walk_args
from scripts.validate_btc_1d_volatility_expansion_reclaim_cooldown_r120s_candidate import parse_args as parse_validation_args


def test_validate_btc_1d_volatility_expansion_reclaim_cooldown_r120s_candidate_defaults() -> None:
    config = parse_validation_args([])
    assert config.periods == 2600
    assert config.strategy_name == "btc_1d_volatility_expansion_reclaim_sr121b_r120s"
    assert config.extra_parameters["min_atr_expansion_ratio"] == 1.20
    assert config.extra_parameters["min_trend_slope_ratio"] == 0.00252


def test_run_btc_1d_walk_forward_volatility_expansion_reclaim_cooldown_r120s_candidate_defaults() -> None:
    config = parse_walk_args([])
    assert config.periods == 2600
    assert config.strategy_name == "btc_1d_volatility_expansion_reclaim_sr121b_r120s"
    assert config.extra_parameters["min_atr_expansion_ratio"] == 1.20
    assert config.candidate_label == "volatility_expansion_reclaim_cooldown_ratio120_lower_slope"
