from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_reclaim_cooldown_bridge_v2_batch import (
    Btc1dVolatilityExpansionReclaimCooldownBridgeV2BatchService,
    Btc1dVolatilityExpansionReclaimCooldownBridgeV2Config,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_expansion_reclaim_cooldown_bridge_v2_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilityExpansionReclaimCooldownBridgeV2BatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dVolatilityExpansionReclaimCooldownBridgeV2Config(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-reclaim-cooldown-bridge-v2-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
