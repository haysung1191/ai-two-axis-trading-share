from __future__ import annotations

from app.domains.experiments.btc_1d_post_spike_bridge_backup_main_gap_recovery_batch import (
    Btc1dPostSpikeBridgeBackupMainGapRecoveryBatchService,
    Btc1dPostSpikeBridgeBackupMainGapRecoveryConfig,
    DEFAULT_VARIANTS,
)


def test_bridge_backup_main_gap_recovery_batch_runs(tmp_path) -> None:
    class _StubDualValidationService:
        def run_variant_validation(self, variant_label, parameters, *, config=None, run_id=None, emit_file=False):
            is_better = variant_label == "bridge_28_volume100"
            return {
                "bridge_backup_label": variant_label,
                "parameters": dict(parameters),
                "base_validation": {
                    "analysis_result_json": f"{variant_label}_base.json",
                    "base_cagr": 0.39 if is_better else 0.31,
                    "base_sharpe": 1.9,
                    "base_max_drawdown": 0.09,
                    "sensitivity_max_drift": 0.12,
                    "negative_windows": [],
                    "idle_windows": [2],
                    "negative_window_count": 0,
                    "idle_window_count": 1,
                },
                "cost20_validation": {
                    "analysis_result_json": f"{variant_label}_cost20.json",
                    "cost20_cagr": 0.35 if is_better else 0.30,
                    "cost20_sharpe": 1.8,
                    "cost20_max_drawdown": 0.095,
                    "sensitivity_max_drift": 0.13,
                    "negative_windows": [],
                    "idle_windows": [2],
                    "negative_window_count": 0,
                    "idle_window_count": 1,
                },
            }

    service = Btc1dPostSpikeBridgeBackupMainGapRecoveryBatchService(
        analysis_results_dir=tmp_path,
        dual_validation_service=_StubDualValidationService(),
    )
    result = service.run_batch(
        Btc1dPostSpikeBridgeBackupMainGapRecoveryConfig(periods=1200),
        run_id="btc-1d-post-spike-bridge-backup-main-gap-recovery-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")
    assert result["best_variant"]["variant_label"] == "bridge_28_volume100"
    assert "base_cagr_gap_to_main" in result["best_variant"]
    assert "cost20_cagr_gap_to_main" in result["best_variant"]


def test_bridge_backup_main_gap_recovery_batch_contains_gap_variants() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}

    assert "bridge_28_relief" in labels
    assert "bridge_28_volume100" in labels
    assert "bridge_28_spike103_volume100" in labels
    assert "bridge_28_depth061_volume100" in labels
