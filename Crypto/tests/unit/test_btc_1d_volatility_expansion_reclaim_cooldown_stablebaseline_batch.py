from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_reclaim_cooldown_stablebaseline_batch import (
    Btc1dVolatilityExpansionReclaimCooldownStablebaselineBatchService,
    Btc1dVolatilityExpansionReclaimCooldownStablebaselineConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_expansion_reclaim_cooldown_stablebaseline_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilityExpansionReclaimCooldownStablebaselineBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dVolatilityExpansionReclaimCooldownStablebaselineConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-reclaim-cooldown-stablebaseline-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
