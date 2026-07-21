from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_pocket_breakout_high_cagr_batch import (
    Btc1dVolatilityPocketBreakoutHighCagrBatchService,
    Btc1dVolatilityPocketBreakoutHighCagrConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_pocket_breakout_high_cagr_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilityPocketBreakoutHighCagrBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dVolatilityPocketBreakoutHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-pocket-breakout-high-cagr-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
