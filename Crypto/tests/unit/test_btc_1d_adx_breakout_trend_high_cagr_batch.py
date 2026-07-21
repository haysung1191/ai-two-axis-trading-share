from __future__ import annotations

from app.domains.experiments.btc_1d_adx_breakout_trend_high_cagr_batch import (
    DEFAULT_VARIANTS,
    Btc1dAdxBreakoutTrendHighCagrConfig,
)


def test_adx_breakout_variants_are_defined() -> None:
    assert len(DEFAULT_VARIANTS) == 4
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}
    assert {"reference", "faster_breakout", "stronger_trend", "longer_hold"} <= labels


def test_adx_breakout_config_targets_attack_track() -> None:
    config = Btc1dAdxBreakoutTrendHighCagrConfig()
    assert config.stage1_min_cagr == 0.2
    assert config.stage1_max_drawdown == 0.35
