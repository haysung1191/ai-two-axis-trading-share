from __future__ import annotations

from scripts.validate_btc_1d_volatility_expansion_reclaim_stab_atrs_candidate import parse_args


def test_parse_stab_atrs_candidate_defaults() -> None:
    config = parse_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.artifact_label == "btcusdt_1d_2200"
