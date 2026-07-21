from __future__ import annotations

from scripts.validate_btc_1d_volatility_expansion_reclaim_cooldown_floor_candidate import parse_args


def test_validate_btc_1d_volatility_expansion_reclaim_cooldown_floor_candidate_defaults() -> None:
    config = parse_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2600
    assert config.strategy_name == "btc_1d_volatility_expansion_reclaim_cdf12s"
    assert config.extra_parameters["breakout_window"] == 18
    assert config.extra_parameters["atr_window"] == 11
    assert config.extra_parameters["atr_expansion_window"] == 5
    assert config.extra_parameters["min_atr_expansion_ratio"] == 1.10
    assert config.extra_parameters["cooldown_bars"] == 12
    assert config.extra_parameters["min_trend_slope_ratio"] == 0.0028
