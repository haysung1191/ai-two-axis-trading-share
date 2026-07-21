from __future__ import annotations

from app.domains.experiments.btc_1d_one_bar_failed_dip_continuation_reopen_batch import (
    Btc1dOneBarFailedDipContinuationReopenBatchService,
    Btc1dOneBarFailedDipContinuationReopenConfig,
    DEFAULT_VARIANTS,
)


def test_one_bar_failed_dip_continuation_reopen_batch_runs(tmp_path) -> None:
    service = Btc1dOneBarFailedDipContinuationReopenBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dOneBarFailedDipContinuationReopenConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-one-bar-failed-dip-continuation-reopen-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
