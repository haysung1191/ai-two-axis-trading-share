from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_trend_robustness_followup_v2_batch import (
    DEFAULT_VARIANTS,
    Btc1dVolatilityExpansionTrendRobustnessFollowupV2Config,
)


def test_v2_variants_keep_atr_ratio_fixed() -> None:
    assert len(DEFAULT_VARIANTS) == 5
    assert {variant["parameters"]["min_atr_expansion_ratio"] for variant in DEFAULT_VARIANTS} == {1.16}


def test_v2_config_targets_high_cagr_window() -> None:
    config = Btc1dVolatilityExpansionTrendRobustnessFollowupV2Config()
    assert config.stage1_min_cagr == 0.30
    assert config.stage1_max_drawdown == 0.26
