from __future__ import annotations

from scripts.run_btc_1d_walk_forward_volatility_spike_reversal_continuation_tightstop_candidate import (
    parse_args as parse_walk_args,
)
from scripts.validate_btc_1d_volatility_spike_reversal_continuation_tightstop_candidate import (
    parse_args as parse_validation_args,
)
from scripts.validate_btc_1d_volatility_spike_reversal_continuation_tightstop_friction import build_parser


def test_validate_btc_1d_volatility_spike_reversal_continuation_tightstop_candidate_defaults() -> None:
    config = parse_validation_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "btc_1d_volatility_spike_reversal_continuation_exit_v2"
    assert config.max_drawdown == 0.30
    assert config.extra_parameters["stop_ema_window"] == 16
    assert config.extra_parameters["max_hold_bars"] == 34


def test_run_btc_1d_walk_forward_volatility_spike_reversal_continuation_tightstop_candidate_defaults() -> None:
    config = parse_walk_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "btc_1d_volatility_spike_reversal_continuation_exit_v2"
    assert config.candidate_label == "volatility_spike_reversal_continuation_tighter_stop"
    assert config.extra_parameters["stop_ema_window"] == 16
    assert config.extra_parameters["max_hold_bars"] == 34


def test_btc_1d_volatility_spike_reversal_continuation_tightstop_friction_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.periods == 2200
    assert args.cost_levels_bps == [0.0, 8.0, 12.0, 20.0]
