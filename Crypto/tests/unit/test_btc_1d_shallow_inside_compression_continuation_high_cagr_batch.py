from __future__ import annotations

from app.domains.experiments.btc_1d_shallow_inside_compression_continuation_high_cagr_batch import (
    Btc1dShallowInsideCompressionContinuationHighCagrBatchService,
    Btc1dShallowInsideCompressionContinuationHighCagrConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_shallow_inside_compression_continuation_high_cagr_batch_runs(tmp_path) -> None:
    service = Btc1dShallowInsideCompressionContinuationHighCagrBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dShallowInsideCompressionContinuationHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-shallow-inside-compression-continuation-high-cagr-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
