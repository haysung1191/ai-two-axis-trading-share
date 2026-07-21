from __future__ import annotations

from app.domains.experiments.btc_1d_shallow_liquidity_void_refill_micro_refinement_batch import (
    Btc1dShallowLiquidityVoidRefillMicroRefinementBatchService,
    Btc1dShallowLiquidityVoidRefillMicroRefinementConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_shallow_liquidity_void_refill_micro_refinement_batch_runs(tmp_path) -> None:
    service = Btc1dShallowLiquidityVoidRefillMicroRefinementBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dShallowLiquidityVoidRefillMicroRefinementConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-shallow-liquidity-void-refill-micro-refinement-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
