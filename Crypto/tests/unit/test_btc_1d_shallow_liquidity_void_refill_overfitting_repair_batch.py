from __future__ import annotations

from app.domains.experiments.btc_1d_shallow_liquidity_void_refill_overfitting_repair_batch import (
    Btc1dShallowLiquidityVoidRefillOverfittingRepairBatchService,
    Btc1dShallowLiquidityVoidRefillOverfittingRepairConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_shallow_liquidity_void_refill_overfitting_repair_batch_runs(tmp_path) -> None:
    service = Btc1dShallowLiquidityVoidRefillOverfittingRepairBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dShallowLiquidityVoidRefillOverfittingRepairConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-shallow-liquidity-void-refill-overfitting-repair-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
