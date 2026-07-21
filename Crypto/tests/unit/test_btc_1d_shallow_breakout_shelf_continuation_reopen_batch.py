from __future__ import annotations

from app.domains.experiments.btc_1d_shallow_breakout_shelf_continuation_reopen_batch import (
    Btc1dShallowBreakoutShelfContinuationReopenBatchService,
    Btc1dShallowBreakoutShelfContinuationReopenConfig,
    DEFAULT_VARIANTS,
)


def test_shallow_breakout_shelf_continuation_reopen_batch_runs(tmp_path) -> None:
    service = Btc1dShallowBreakoutShelfContinuationReopenBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dShallowBreakoutShelfContinuationReopenConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-shallow-breakout-shelf-continuation-reopen-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
