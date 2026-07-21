from __future__ import annotations

from app.domains.experiments.btc_1d_breakout_retest_compression_batch import (
    Btc1dBreakoutRetestCompressionBatchService,
    Btc1dBreakoutRetestCompressionConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_breakout_retest_compression_batch_runs(tmp_path) -> None:
    service = Btc1dBreakoutRetestCompressionBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dBreakoutRetestCompressionConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-breakout-retest-compression-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")


def test_btc_1d_breakout_retest_compression_batch_labels_present(tmp_path) -> None:
    service = Btc1dBreakoutRetestCompressionBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dBreakoutRetestCompressionConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-breakout-retest-compression-labels",
    )

    labels = {row["variant_label"] for row in result["results"]}
    assert "near_miss_reference" in labels
    assert "cleaner_retest" in labels
