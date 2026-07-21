from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_trend_compression_batch import (
    Btc1dVolatilityExpansionTrendCompressionBatchService,
    Btc1dVolatilityExpansionTrendCompressionConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_expansion_trend_compression_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilityExpansionTrendCompressionBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dVolatilityExpansionTrendCompressionConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-trend-compression-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")


def test_btc_1d_volatility_expansion_trend_compression_batch_labels_present(tmp_path) -> None:
    service = Btc1dVolatilityExpansionTrendCompressionBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dVolatilityExpansionTrendCompressionConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-trend-compression-labels",
    )

    labels = {row["variant_label"] for row in result["results"]}
    assert "near_miss_reference" in labels
    assert "slower_trend_longer_hold" in labels
