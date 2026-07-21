from __future__ import annotations

from app.domains.experiments.btc_1d_trend_pullback_reclaim_cooldown_batch import (
    Btc1dTrendPullbackReclaimCooldownBatchService,
    Btc1dTrendPullbackReclaimCooldownConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_trend_pullback_reclaim_cooldown_batch_runs(tmp_path) -> None:
    service = Btc1dTrendPullbackReclaimCooldownBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dTrendPullbackReclaimCooldownConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-trend-pullback-reclaim-cooldown-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
