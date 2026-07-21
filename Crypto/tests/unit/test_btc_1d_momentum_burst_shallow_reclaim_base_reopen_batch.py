from __future__ import annotations

from app.domains.experiments.btc_1d_momentum_burst_shallow_reclaim_base_reopen_batch import (
    Btc1dMomentumBurstShallowReclaimBaseReopenBatchService,
    Btc1dMomentumBurstShallowReclaimBaseReopenConfig,
    DEFAULT_VARIANTS,
)


def test_momentum_burst_shallow_reclaim_base_reopen_batch_runs(tmp_path) -> None:
    service = Btc1dMomentumBurstShallowReclaimBaseReopenBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dMomentumBurstShallowReclaimBaseReopenConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-momentum-burst-shallow-reclaim-base-reopen-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
