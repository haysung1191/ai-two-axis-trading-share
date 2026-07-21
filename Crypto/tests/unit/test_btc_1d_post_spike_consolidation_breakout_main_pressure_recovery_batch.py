from __future__ import annotations

import app.domains.experiments.btc_1d_post_spike_consolidation_breakout_main_pressure_recovery_batch as mod
from app.domains.experiments.btc_1d_post_spike_consolidation_breakout_main_pressure_recovery_batch import (
    Btc1dPostSpikeConsolidationBreakoutMainPressureRecoveryBatchService,
    Btc1dPostSpikeConsolidationBreakoutMainPressureRecoveryConfig,
)


def test_btc_1d_post_spike_consolidation_breakout_main_pressure_recovery_batch_runs(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "DEFAULT_VARIANTS", mod.DEFAULT_VARIANTS[:2])
    service = Btc1dPostSpikeConsolidationBreakoutMainPressureRecoveryBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dPostSpikeConsolidationBreakoutMainPressureRecoveryConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-post-spike-consolidation-breakout-main-pressure-recovery-test",
    )

    assert len(result["results"]) == len(mod.DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")
    assert "base_cagr_gap_to_main" in result["best_variant"]
    assert "quality_pressure_passed" in result["best_variant"]
