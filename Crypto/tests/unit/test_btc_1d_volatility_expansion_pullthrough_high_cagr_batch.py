from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_pullthrough_high_cagr_batch import (
    Btc1dVolatilityExpansionPullthroughHighCagrBatchService,
    Btc1dVolatilityExpansionPullthroughHighCagrConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_expansion_pullthrough_high_cagr_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilityExpansionPullthroughHighCagrBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dVolatilityExpansionPullthroughHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-pullthrough-high-cagr-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
