from __future__ import annotations

from app.domains.experiments.btc_1d_trend_continuation_pullback_filter_longspan_batch import (
    Btc1dTrendContinuationPullbackFilterLongspanBatchService,
    Btc1dTrendContinuationPullbackFilterLongspanConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_trend_continuation_pullback_filter_longspan_batch_runs(tmp_path) -> None:
    service = Btc1dTrendContinuationPullbackFilterLongspanBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dTrendContinuationPullbackFilterLongspanConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-trend-continuation-pullback-filter-longspan-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
