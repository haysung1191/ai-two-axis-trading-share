from __future__ import annotations

from app.domains.experiments.btc_1d_trend_dip_reversal_breakout_overfitting_repair_batch import (
    Btc1dTrendDipReversalBreakoutOverfittingRepairBatchService,
    Btc1dTrendDipReversalBreakoutOverfittingRepairConfig,
    DEFAULT_VARIANTS,
)


def test_trend_dip_overfitting_repair_batch_runs(tmp_path) -> None:
    service = Btc1dTrendDipReversalBreakoutOverfittingRepairBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dTrendDipReversalBreakoutOverfittingRepairConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-trend-dip-overfitting-repair-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
