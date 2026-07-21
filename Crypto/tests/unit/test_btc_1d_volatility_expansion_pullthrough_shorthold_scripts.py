from __future__ import annotations

from scripts.run_btc_1d_walk_forward_volatility_expansion_pullthrough_shorthold_candidate import (
    parse_args as parse_walk_args,
)
from scripts.validate_btc_1d_volatility_expansion_pullthrough_shorthold_candidate import (
    parse_args as parse_validation_args,
)
from scripts.validate_btc_1d_volatility_expansion_pullthrough_shorthold_friction import build_parser


def test_validate_btc_1d_volatility_expansion_pullthrough_shorthold_candidate_defaults() -> None:
    config = parse_validation_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "btc_1d_volatility_expansion_pullthrough_v3"
    assert config.extra_parameters["stop_ema_window"] == 18
    assert config.extra_parameters["min_atr_expansion_ratio"] == 1.10
    assert config.extra_parameters["setup_close_strength_threshold"] == 0.70
    assert config.extra_parameters["min_volume_ratio"] == 1.05
    assert config.extra_parameters["max_hold_bars"] == 31


def test_run_btc_1d_walk_forward_volatility_expansion_pullthrough_shorthold_candidate_defaults() -> None:
    config = parse_walk_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "btc_1d_volatility_expansion_pullthrough_v3"
    assert config.candidate_label == "volatility_expansion_pullthrough_softer_setup_hold31"
    assert config.extra_parameters["stop_ema_window"] == 18
    assert config.extra_parameters["min_atr_expansion_ratio"] == 1.10
    assert config.extra_parameters["setup_close_strength_threshold"] == 0.70
    assert config.extra_parameters["min_volume_ratio"] == 1.05
    assert config.extra_parameters["max_hold_bars"] == 31


def test_btc_1d_volatility_expansion_pullthrough_shorthold_friction_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.periods == 2200
    assert args.cost_levels_bps == [0.0, 8.0, 12.0, 20.0]
