from __future__ import annotations

from app.domains.experiments.btc_1d_post_spike_bridge_backup_wider_family_batch import (
    Btc1dPostSpikeBridgeBackupWiderFamilyBatchService,
    Btc1dPostSpikeBridgeBackupWiderFamilyConfig,
    WIDER_FAMILY_VARIANTS,
)


def test_bridge_backup_wider_family_batch_runs(tmp_path) -> None:
    class _StubDualValidationService:
        def run_variant_validation(self, variant_label, parameters, *, config=None, run_id=None, emit_file=False):
            is_better = variant_label == "bridge_wide_trend84_spike24_buffer018"
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

    service = Btc1dPostSpikeBridgeBackupWiderFamilyBatchService(
        analysis_results_dir=tmp_path,
        dual_validation_service=_StubDualValidationService(),
    )
    result = service.run_batch(
        Btc1dPostSpikeBridgeBackupWiderFamilyConfig(periods=1200),
        run_id="btc-1d-post-spike-bridge-backup-wider-family-test",
    )

    assert len(result["results"]) == len(WIDER_FAMILY_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")
    assert result["best_variant"]["variant_label"] == "bridge_wide_trend84_spike24_buffer018"
    assert "base_cagr_gap_to_main" in result["best_variant"]
    assert "cost20_cagr_gap_to_main" in result["best_variant"]


def test_bridge_backup_wider_family_batch_contains_structural_variants() -> None:
    labels = {variant["label"] for variant in WIDER_FAMILY_VARIANTS}

    assert "bridge_28_relief" in labels
    assert "bridge_wide_trend84_spike24_buffer018" in labels
    assert "bridge_wide_trend108_spike32_consol10" in labels
    assert "bridge_wide_slow_stop24_hold40" in labels
