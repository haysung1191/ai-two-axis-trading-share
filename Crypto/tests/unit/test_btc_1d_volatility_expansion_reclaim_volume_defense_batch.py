from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_reclaim_volume_defense_batch import (
    Btc1dVolatilityExpansionReclaimVolumeDefenseBatchService,
    Btc1dVolatilityExpansionReclaimVolumeDefenseConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_expansion_reclaim_volume_defense_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilityExpansionReclaimVolumeDefenseBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dVolatilityExpansionReclaimVolumeDefenseConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-reclaim-volume-defense-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")


def test_btc_1d_volatility_expansion_reclaim_volume_defense_batch_labels_present(tmp_path) -> None:
    service = Btc1dVolatilityExpansionReclaimVolumeDefenseBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dVolatilityExpansionReclaimVolumeDefenseConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-reclaim-volume-defense-labels",
    )
    labels = {row["variant_label"] for row in result["results"]}
    assert "top_reference" in labels
    assert "longer_and_stricter_volume" in labels
