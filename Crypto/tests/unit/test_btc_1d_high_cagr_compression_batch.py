from __future__ import annotations

from app.domains.experiments.btc_1d_high_cagr_compression_batch import (
    Btc1dHighCagrCompressionBatchService,
    Btc1dHighCagrCompressionConfig,
    DEFAULT_VARIANTS,
)


def test_high_cagr_compression_batch_runs_and_writes_outputs(tmp_path) -> None:
    service = Btc1dHighCagrCompressionBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dHighCagrCompressionConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-high-cagr-compression-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")


def test_high_cagr_compression_batch_includes_near_miss_reference(tmp_path) -> None:
    service = Btc1dHighCagrCompressionBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dHighCagrCompressionConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-high-cagr-compression-labels",
    )

    labels = {row["variant_label"] for row in result["results"]}
    assert "near_miss_reference" in labels
    assert "near_miss_plus_stagnation_exit" in labels
