from __future__ import annotations

from scripts.run_btc_1d_post_spike_consolidation_breakout_carry_extension_batch import (
    BASE_PARAMETERS,
    DEFAULT_VARIANTS,
    build_parser,
)


def test_post_spike_carry_extension_defaults_preserve_anchor() -> None:
    assert BASE_PARAMETERS["trend_ema_window"] == 92.0
    assert BASE_PARAMETERS["spike_lookback"] == 28.0
    assert BASE_PARAMETERS["min_volume_ratio"] == 1.05
    assert BASE_PARAMETERS["max_hold_bars"] == 36.0
    assert DEFAULT_VARIANTS[0]["label"] == "anchor_hold36_stop20"
    assert any(row["label"] == "hold34_stop20" for row in DEFAULT_VARIANTS)


def test_post_spike_carry_extension_cli_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.periods == 2200
    assert args.variant_label == []
    assert args.allow_synthetic_ohlcv_fallback is False
