from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_reclaim_cooldown_r120s_stabilization_batch import (
    Btc1dVolatilityExpansionReclaimCooldownR120sStabilizationBatchService,
    Btc1dVolatilityExpansionReclaimCooldownR120sStabilizationConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_expansion_reclaim_cooldown_r120s_stabilization_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilityExpansionReclaimCooldownR120sStabilizationBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dVolatilityExpansionReclaimCooldownR120sStabilizationConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-reclaim-cooldown-r120s-stabilization-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
