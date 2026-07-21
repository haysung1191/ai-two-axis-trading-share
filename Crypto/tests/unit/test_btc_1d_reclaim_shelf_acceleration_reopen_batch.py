from __future__ import annotations

from app.domains.experiments.btc_1d_reclaim_shelf_acceleration_reopen_batch import (
    Btc1dReclaimShelfAccelerationReopenBatchService,
    Btc1dReclaimShelfAccelerationReopenConfig,
    DEFAULT_VARIANTS,
)


def test_reclaim_shelf_acceleration_reopen_batch_runs(tmp_path) -> None:
    service = Btc1dReclaimShelfAccelerationReopenBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dReclaimShelfAccelerationReopenConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-reclaim-shelf-acceleration-reopen-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
