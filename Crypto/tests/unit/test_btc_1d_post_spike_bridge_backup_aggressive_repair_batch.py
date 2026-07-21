from __future__ import annotations

from app.domains.experiments.btc_1d_post_spike_bridge_backup_aggressive_repair_batch import (
    AGGRESSIVE_REPAIR_VARIANTS,
    Btc1dPostSpikeBridgeBackupAggressiveRepairBatchService,
    Btc1dPostSpikeBridgeBackupAggressiveRepairConfig,
)


def test_bridge_backup_aggressive_repair_batch_runs(tmp_path) -> None:
    class _StubDualValidationService:
        def run_variant_validation(self, variant_label, parameters, *, config=None, run_id=None, emit_file=False):
            is_better = variant_label == "aggr_repair_trend864_depth055_volume104"
            return {
                "bridge_backup_label": variant_label,
                "parameters": dict(parameters),
                "base_validation": {
                    "analysis_result_json": f"{variant_label}_base.json",
                    "base_cagr": 0.395 if is_better else 0.315,
                    "base_sharpe": 1.95,
                    "base_max_drawdown": 0.09,
                    "sensitivity_max_drift": 0.12,
                    "negative_windows": [],
                    "idle_windows": [2],
                    "negative_window_count": 0,
                    "idle_window_count": 1,
                },
                "cost20_validation": {
                    "analysis_result_json": f"{variant_label}_cost20.json",
                    "cost20_cagr": 0.355 if is_better else 0.305,
                    "cost20_sharpe": 1.85,
                    "cost20_max_drawdown": 0.095,
                    "sensitivity_max_drift": 0.13,
                    "negative_windows": [],
                    "idle_windows": [2],
                    "negative_window_count": 0,
                    "idle_window_count": 1,
                },
            }

    service = Btc1dPostSpikeBridgeBackupAggressiveRepairBatchService(
        analysis_results_dir=tmp_path,
        dual_validation_service=_StubDualValidationService(),
    )
    result = service.run_batch(
        Btc1dPostSpikeBridgeBackupAggressiveRepairConfig(periods=1200),
        run_id="btc-1d-post-spike-bridge-backup-aggressive-repair-test",
    )

    assert len(result["results"]) == len(AGGRESSIVE_REPAIR_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")
    assert result["best_variant"]["variant_label"] == "aggr_repair_trend864_depth055_volume104"
    assert "base_cagr_gap_to_main" in result["best_variant"]
    assert "cost20_cagr_gap_to_main" in result["best_variant"]


def test_bridge_backup_aggressive_repair_batch_contains_repair_winner_seed() -> None:
    labels = {variant["label"] for variant in AGGRESSIVE_REPAIR_VARIANTS}

    assert "aggr_repair_trend864_depth055_volume108" in labels
    assert "aggr_repair_trend864_depth055_volume104" in labels
    assert "aggr_repair_trend96_depth058_volume104_hold40" in labels
