from __future__ import annotations

from app.domains.experiments.btc_1d_micro_undercut_reclaim_continuation_reopen_batch import (
    Btc1dMicroUndercutReclaimContinuationReopenBatchService,
    Btc1dMicroUndercutReclaimContinuationReopenConfig,
    DEFAULT_VARIANTS,
)


def test_micro_undercut_reclaim_continuation_reopen_batch_runs(tmp_path) -> None:
    service = Btc1dMicroUndercutReclaimContinuationReopenBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dMicroUndercutReclaimContinuationReopenConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-micro-undercut-reclaim-continuation-reopen-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
