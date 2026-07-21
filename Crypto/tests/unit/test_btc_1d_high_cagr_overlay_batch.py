from __future__ import annotations

from app.domains.experiments.btc_1d_high_cagr_overlay_batch import (
    Btc1dHighCagrOverlayBatchService,
    Btc1dHighCagrOverlayConfig,
    DEFAULT_VARIANTS,
)


def test_high_cagr_overlay_batch_runs_and_writes_outputs(tmp_path) -> None:
    service = Btc1dHighCagrOverlayBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dHighCagrOverlayConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-high-cagr-overlay-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")


def test_high_cagr_overlay_batch_includes_overlay_labels(tmp_path) -> None:
    service = Btc1dHighCagrOverlayBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dHighCagrOverlayConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-high-cagr-overlay-labels",
    )

    labels = {row["variant_label"] for row in result["results"]}
    assert "aggressive_reference" in labels
    assert "risk_off_overlay" in labels
