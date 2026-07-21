from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_reclaim_survivability_batch import (
    Btc1dVolatilityExpansionReclaimSurvivabilityBatchService,
    Btc1dVolatilityExpansionReclaimSurvivabilityConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_expansion_reclaim_survivability_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilityExpansionReclaimSurvivabilityBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dVolatilityExpansionReclaimSurvivabilityConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-reclaim-survivability-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
