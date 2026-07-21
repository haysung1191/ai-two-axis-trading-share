from __future__ import annotations

import app.domains.experiments.btc_1d_post_spike_backup_base_gap_recovery_batch as mod
from app.domains.experiments.btc_1d_post_spike_backup_base_gap_recovery_batch import (
    Btc1dPostSpikeBackupBaseGapRecoveryBatchService,
    Btc1dPostSpikeBackupBaseGapRecoveryConfig,
)


def test_btc_1d_post_spike_backup_base_gap_recovery_batch_runs(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "DEFAULT_VARIANTS", mod.DEFAULT_VARIANTS[:3])
    service = Btc1dPostSpikeBackupBaseGapRecoveryBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dPostSpikeBackupBaseGapRecoveryConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-post-spike-backup-base-gap-recovery-test",
    )

    assert len(result["results"]) == len(mod.DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")
    assert "base_cagr_gap_to_main" in result["best_variant"]
    assert "replacement_open_passed" in result["best_variant"]
