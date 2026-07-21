from __future__ import annotations

from app.domains.experiments.btc_1d_micro_undercut_reclaim_continuation_high_cagr_batch import (
    Btc1dMicroUndercutReclaimContinuationHighCagrBatchService,
    Btc1dMicroUndercutReclaimContinuationHighCagrConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_micro_undercut_reclaim_continuation_high_cagr_batch_runs(tmp_path) -> None:
    service = Btc1dMicroUndercutReclaimContinuationHighCagrBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dMicroUndercutReclaimContinuationHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-micro-undercut-reclaim-continuation-high-cagr-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
