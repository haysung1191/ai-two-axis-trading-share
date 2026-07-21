from __future__ import annotations

from app.domains.experiments.btc_1d_brief_close_above_reset_continuation_reopen_batch import (
    Btc1dBriefCloseAboveResetContinuationReopenBatchService,
    Btc1dBriefCloseAboveResetContinuationReopenConfig,
    DEFAULT_VARIANTS,
)


def test_brief_close_above_reset_continuation_reopen_batch_runs(tmp_path) -> None:
    service = Btc1dBriefCloseAboveResetContinuationReopenBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dBriefCloseAboveResetContinuationReopenConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-brief-close-above-reset-continuation-reopen-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
