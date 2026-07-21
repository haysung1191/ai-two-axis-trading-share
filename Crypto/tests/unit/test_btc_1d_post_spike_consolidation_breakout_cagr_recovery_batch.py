from __future__ import annotations

from app.domains.experiments.btc_1d_post_spike_consolidation_breakout_cagr_recovery_batch import (
    Btc1dPostSpikeConsolidationBreakoutCagrRecoveryBatchService,
    Btc1dPostSpikeConsolidationBreakoutCagrRecoveryConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_consolidation_breakout_cagr_recovery_batch_runs(tmp_path) -> None:
    service = Btc1dPostSpikeConsolidationBreakoutCagrRecoveryBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dPostSpikeConsolidationBreakoutCagrRecoveryConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-post-spike-consolidation-breakout-cagr-recovery-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")
    assert "rotation_gap_to_backup" in result["best_variant"]
