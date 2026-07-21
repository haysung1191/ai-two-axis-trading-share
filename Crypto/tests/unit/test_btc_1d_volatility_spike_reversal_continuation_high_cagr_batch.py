from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_spike_reversal_continuation_high_cagr_batch import (
    Btc1dVolatilitySpikeReversalContinuationHighCagrBatchService,
    Btc1dVolatilitySpikeReversalContinuationHighCagrConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_spike_reversal_continuation_high_cagr_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilitySpikeReversalContinuationHighCagrBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dVolatilitySpikeReversalContinuationHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-spike-reversal-continuation-high-cagr-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
