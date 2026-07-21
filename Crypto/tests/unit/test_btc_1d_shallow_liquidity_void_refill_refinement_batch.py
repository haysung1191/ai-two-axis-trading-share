from __future__ import annotations

from app.domains.experiments.btc_1d_shallow_liquidity_void_refill_refinement_batch import (
    Btc1dShallowLiquidityVoidRefillRefinementBatchService,
    Btc1dShallowLiquidityVoidRefillRefinementConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_shallow_liquidity_void_refill_refinement_batch_runs(tmp_path) -> None:
    service = Btc1dShallowLiquidityVoidRefillRefinementBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dShallowLiquidityVoidRefillRefinementConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-shallow-liquidity-void-refill-refinement-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
