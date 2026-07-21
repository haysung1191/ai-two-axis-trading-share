from __future__ import annotations

from app.domains.experiments.btc_1d_failed_breakout_continuation_high_cagr_batch import (
    Btc1dFailedBreakoutContinuationHighCagrBatchService,
    Btc1dFailedBreakoutContinuationHighCagrConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_failed_breakout_continuation_high_cagr_batch_runs(tmp_path) -> None:
    service = Btc1dFailedBreakoutContinuationHighCagrBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dFailedBreakoutContinuationHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-failed-breakout-continuation-high-cagr-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
