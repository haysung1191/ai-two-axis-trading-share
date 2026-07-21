from __future__ import annotations

from app.domains.experiments.btc_1d_post_spike_consolidation_breakout_overfitting_repair_batch import (
    Btc1dPostSpikeConsolidationBreakoutOverfittingRepairBatchService,
    Btc1dPostSpikeConsolidationBreakoutOverfittingRepairConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_consolidation_breakout_overfitting_repair_batch_runs(tmp_path) -> None:
    service = Btc1dPostSpikeConsolidationBreakoutOverfittingRepairBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dPostSpikeConsolidationBreakoutOverfittingRepairConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-post-spike-consolidation-breakout-overfitting-repair-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
