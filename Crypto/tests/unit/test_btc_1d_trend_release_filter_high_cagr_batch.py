from __future__ import annotations

from app.domains.experiments.btc_1d_trend_release_filter_high_cagr_batch import (
    Btc1dTrendReleaseFilterHighCagrBatchService,
    Btc1dTrendReleaseFilterHighCagrConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_trend_release_filter_high_cagr_batch_runs(tmp_path) -> None:
    service = Btc1dTrendReleaseFilterHighCagrBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dTrendReleaseFilterHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-trend-release-filter-high-cagr-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")


def test_btc_1d_trend_release_filter_high_cagr_batch_labels_present(tmp_path) -> None:
    service = Btc1dTrendReleaseFilterHighCagrBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dTrendReleaseFilterHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-trend-release-filter-high-cagr-labels",
    )

    labels = {row["variant_label"] for row in result["results"]}
    assert "reference" in labels
    assert "cleaner_release" in labels
