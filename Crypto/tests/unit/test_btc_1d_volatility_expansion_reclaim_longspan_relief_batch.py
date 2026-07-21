from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_reclaim_longspan_relief_batch import (
    Btc1dVolatilityExpansionReclaimLongspanReliefBatchService,
    Btc1dVolatilityExpansionReclaimLongspanReliefConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_expansion_reclaim_longspan_relief_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilityExpansionReclaimLongspanReliefBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dVolatilityExpansionReclaimLongspanReliefConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-reclaim-longspan-relief-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
