from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_trend_cooldown_batch import (
    Btc1dVolatilityExpansionTrendCooldownBatchService,
    Btc1dVolatilityExpansionTrendCooldownConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_expansion_trend_cooldown_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilityExpansionTrendCooldownBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dVolatilityExpansionTrendCooldownConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-trend-cooldown-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
