from __future__ import annotations

from app.domains.experiments.btc_1d_shallow_liquidity_void_refill_continuation_exit_compression_batch import (
    Btc1dShallowLiquidityVoidRefillContinuationExitCompressionBatchService,
    Btc1dShallowLiquidityVoidRefillContinuationExitCompressionConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_shallow_liquidity_void_refill_continuation_exit_compression_batch_runs(tmp_path) -> None:
    service = Btc1dShallowLiquidityVoidRefillContinuationExitCompressionBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dShallowLiquidityVoidRefillContinuationExitCompressionConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-shallow-liquidity-void-refill-continuation-exit-compression-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
