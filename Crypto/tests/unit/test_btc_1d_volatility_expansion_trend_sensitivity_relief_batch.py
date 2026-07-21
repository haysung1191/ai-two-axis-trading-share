from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_trend_sensitivity_relief_batch import (
    DEFAULT_VARIANTS,
    Btc1dVolatilityExpansionTrendSensitivityReliefConfig,
)


def test_sensitivity_relief_variants_cover_bridge_ratios() -> None:
    ratios = {variant["parameters"]["min_atr_expansion_ratio"] for variant in DEFAULT_VARIANTS}
    assert ratios == {1.13, 1.14, 1.16}


def test_sensitivity_relief_config_targets_high_cagr_only() -> None:
    config = Btc1dVolatilityExpansionTrendSensitivityReliefConfig()
    assert config.stage1_min_cagr == 0.36
    assert config.stage1_max_drawdown == 0.27
