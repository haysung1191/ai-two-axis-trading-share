from __future__ import annotations

from app.domains.experiments.btc_1d_failed_retest_acceleration_high_cagr_batch import (
    Btc1dFailedRetestAccelerationHighCagrBatchService,
    Btc1dFailedRetestAccelerationHighCagrConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_failed_retest_acceleration_high_cagr_batch_runs(tmp_path) -> None:
    service = Btc1dFailedRetestAccelerationHighCagrBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dFailedRetestAccelerationHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-failed-retest-acceleration-high-cagr-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
