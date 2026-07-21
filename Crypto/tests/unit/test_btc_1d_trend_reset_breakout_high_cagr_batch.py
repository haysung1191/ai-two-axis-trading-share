from __future__ import annotations

from app.domains.experiments.btc_1d_trend_reset_breakout_high_cagr_batch import (
    Btc1dTrendResetBreakoutHighCagrBatchService,
    Btc1dTrendResetBreakoutHighCagrConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_trend_reset_breakout_high_cagr_batch_runs(tmp_path) -> None:
    service = Btc1dTrendResetBreakoutHighCagrBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dTrendResetBreakoutHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-trend-reset-breakout-high-cagr-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")


def test_btc_1d_trend_reset_breakout_high_cagr_batch_labels_present(tmp_path) -> None:
    service = Btc1dTrendResetBreakoutHighCagrBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dTrendResetBreakoutHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-trend-reset-breakout-high-cagr-labels",
    )

    labels = {row["variant_label"] for row in result["results"]}
    assert "reference" in labels
    assert "cleaner_reset" in labels
