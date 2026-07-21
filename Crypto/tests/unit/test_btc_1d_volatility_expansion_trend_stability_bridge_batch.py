from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_trend_stability_bridge_batch import (
    DEFAULT_VARIANTS,
    Btc1dVolatilityExpansionTrendStabilityBridgeConfig,
)


def test_stability_bridge_variants_cover_lower_atr_window() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}
    assert "mid_ratio_lower_atr_window" in labels
    assert "mid_ratio_lower_atr_shorter_memory" in labels


def test_stability_bridge_config_is_stricter_than_mid_ratio_batch() -> None:
    config = Btc1dVolatilityExpansionTrendStabilityBridgeConfig()
    assert config.stage1_min_cagr == 0.34
    assert config.stage1_max_drawdown == 0.27
