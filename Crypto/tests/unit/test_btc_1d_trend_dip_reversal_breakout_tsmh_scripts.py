from __future__ import annotations

from scripts.run_btc_1d_walk_forward_trend_dip_reversal_breakout_tsmh_candidate import (
    parse_args as parse_walk_args,
)
from scripts.validate_btc_1d_trend_dip_reversal_breakout_tsmh_candidate import (
    parse_args as parse_validation_args,
)
from scripts.validate_btc_1d_trend_dip_reversal_breakout_tsmh_friction import build_parser


def test_validate_btc_1d_trend_dip_reversal_breakout_tsmh_candidate_defaults() -> None:
    config = parse_validation_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "btc_1d_trend_dip_reversal_breakout_symmetry_v4"
    assert config.extra_parameters["stop_ema_window"] == 16
    assert config.extra_parameters["max_hold_bars"] == 29


def test_run_btc_1d_walk_forward_trend_dip_reversal_breakout_tsmh_candidate_defaults() -> None:
    config = parse_walk_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "btc_1d_trend_dip_reversal_breakout_symmetry_v4"
    assert config.candidate_label == "trend_dip_reversal_breakout_tighter_stop_mid_hold"
    assert config.extra_parameters["stop_ema_window"] == 16
    assert config.extra_parameters["max_hold_bars"] == 29


def test_btc_1d_trend_dip_reversal_breakout_tsmh_friction_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.periods == 2200
    assert args.cost_levels_bps == [0.0, 8.0, 12.0, 20.0]
