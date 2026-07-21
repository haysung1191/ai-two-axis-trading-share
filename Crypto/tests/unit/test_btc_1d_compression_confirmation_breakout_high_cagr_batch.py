from __future__ import annotations

from app.domains.experiments.btc_1d_compression_confirmation_breakout_high_cagr_batch import (
    Btc1dCompressionConfirmationBreakoutHighCagrBatchService,
    Btc1dCompressionConfirmationBreakoutHighCagrConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_compression_confirmation_breakout_high_cagr_batch_runs(tmp_path) -> None:
    service = Btc1dCompressionConfirmationBreakoutHighCagrBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dCompressionConfirmationBreakoutHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-compression-confirmation-breakout-high-cagr-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")


def test_btc_1d_compression_confirmation_breakout_high_cagr_batch_labels_present(tmp_path) -> None:
    service = Btc1dCompressionConfirmationBreakoutHighCagrBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dCompressionConfirmationBreakoutHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-compression-confirmation-breakout-high-cagr-labels",
    )

    labels = {row["variant_label"] for row in result["results"]}
    assert "reference" in labels
    assert "slower_trend" in labels
