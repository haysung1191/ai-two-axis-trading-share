from __future__ import annotations

from scripts.validate_btc_1d_volatility_expansion_reclaim_sr112_tightstop_concentration_compare import parse_args


def test_parse_sr112_tightstop_concentration_compare_defaults() -> None:
    config = parse_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.fee_bps == 8.0
    assert config.slippage_bps == 8.0
