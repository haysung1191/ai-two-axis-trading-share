from __future__ import annotations

from scripts.validate_btc_1d_volatility_expansion_reclaim_stab_atrs_benchmark_stats import parse_args


def test_parse_benchmark_stats_defaults() -> None:
    config = parse_args([])
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.fee_bps == 8.0
    assert config.slippage_bps == 8.0
    assert config.bootstrap_samples == 1000
    assert config.bootstrap_block_size == 20
