from __future__ import annotations

from app.domains.experiments.btc_1d_narrow_range_expansion_drift_high_cagr_batch import (
    Btc1dNarrowRangeExpansionDriftHighCagrBatchService,
    Btc1dNarrowRangeExpansionDriftHighCagrConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_narrow_range_expansion_drift_high_cagr_batch_runs(tmp_path) -> None:
    service = Btc1dNarrowRangeExpansionDriftHighCagrBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dNarrowRangeExpansionDriftHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-narrow-range-expansion-drift-high-cagr-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
