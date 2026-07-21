from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_reclaim_reclaim_buffer_batch import (
    Btc1dVolatilityExpansionReclaimReclaimBufferBatchService,
    Btc1dVolatilityExpansionReclaimReclaimBufferConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_expansion_reclaim_reclaim_buffer_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilityExpansionReclaimReclaimBufferBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dVolatilityExpansionReclaimReclaimBufferConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-reclaim-reclaim-buffer-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")


def test_btc_1d_volatility_expansion_reclaim_reclaim_buffer_batch_labels_present(tmp_path) -> None:
    service = Btc1dVolatilityExpansionReclaimReclaimBufferBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dVolatilityExpansionReclaimReclaimBufferConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-reclaim-reclaim-buffer-labels",
    )
    labels = {row["variant_label"] for row in result["results"]}
    assert "top_reference" in labels
    assert "looser_buffer" in labels
