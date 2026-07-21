from __future__ import annotations

from app.domains.experiments.btc_1d_failed_breakout_continuation_reopen_batch import (
    Btc1dFailedBreakoutContinuationReopenBatchService,
    Btc1dFailedBreakoutContinuationReopenConfig,
    DEFAULT_VARIANTS,
)


def test_failed_breakout_continuation_reopen_batch_runs(tmp_path) -> None:
    service = Btc1dFailedBreakoutContinuationReopenBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dFailedBreakoutContinuationReopenConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-failed-breakout-continuation-reopen-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
