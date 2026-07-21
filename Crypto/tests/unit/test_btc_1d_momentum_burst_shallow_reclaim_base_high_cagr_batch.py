from __future__ import annotations

from app.domains.experiments.btc_1d_momentum_burst_shallow_reclaim_base_high_cagr_batch import (
    Btc1dMomentumBurstShallowReclaimBaseHighCagrBatchService,
    Btc1dMomentumBurstShallowReclaimBaseHighCagrConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_momentum_burst_shallow_reclaim_base_high_cagr_batch_runs(tmp_path) -> None:
    service = Btc1dMomentumBurstShallowReclaimBaseHighCagrBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dMomentumBurstShallowReclaimBaseHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-momentum-burst-shallow-reclaim-base-high-cagr-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
