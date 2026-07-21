from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_pullthrough_exit_compression_batch import (
    Btc1dVolatilityExpansionPullthroughExitCompressionBatchService,
    Btc1dVolatilityExpansionPullthroughExitCompressionConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_expansion_pullthrough_exit_compression_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilityExpansionPullthroughExitCompressionBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dVolatilityExpansionPullthroughExitCompressionConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-pullthrough-exit-compression-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
