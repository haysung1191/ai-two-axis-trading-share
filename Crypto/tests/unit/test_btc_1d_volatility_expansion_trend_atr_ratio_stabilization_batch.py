from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_trend_atr_ratio_stabilization_batch import (
    DEFAULT_VARIANTS,
    Btc1dVolatilityExpansionTrendAtrRatioStabilizationConfig,
)


def test_atr_ratio_stabilization_variants_include_reference() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}
    assert "faster_trigger_wider_stop_reference" in labels
    assert len(DEFAULT_VARIANTS) == 5


def test_atr_ratio_stabilization_config_targets_high_cagr_candidates() -> None:
    config = Btc1dVolatilityExpansionTrendAtrRatioStabilizationConfig()
    assert config.stage1_min_cagr == 0.30
    assert config.stage1_max_drawdown == 0.28
