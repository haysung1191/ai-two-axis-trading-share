from __future__ import annotations

from app.domains.experiments.btc_1d_trend_liquidity_sweep_reclaim_high_cagr_batch import (
    Btc1dTrendLiquiditySweepReclaimHighCagrBatchService,
    Btc1dTrendLiquiditySweepReclaimHighCagrConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_trend_liquidity_sweep_reclaim_high_cagr_batch_runs(tmp_path) -> None:
    service = Btc1dTrendLiquiditySweepReclaimHighCagrBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dTrendLiquiditySweepReclaimHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-trend-liquidity-sweep-reclaim-high-cagr-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
