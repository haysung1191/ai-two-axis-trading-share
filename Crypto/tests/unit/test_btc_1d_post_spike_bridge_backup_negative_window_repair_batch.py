from __future__ import annotations

from app.domains.experiments.btc_1d_post_spike_bridge_backup_negative_window_repair_batch import (
    Btc1dPostSpikeBridgeBackupNegativeWindowRepairBatchService,
    Btc1dPostSpikeBridgeBackupNegativeWindowRepairConfig,
    DEFAULT_VARIANTS,
)


def test_bridge_backup_negative_window_repair_batch_runs(tmp_path) -> None:
    class _StubDualValidationService:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def run_variant_validation(self, variant_label, parameters, *, config=None, run_id=None, emit_file=False):
            self.calls.append(variant_label)
            is_anchor = variant_label == "bridge_28_relief"
            negative_windows = [5] if is_anchor else []
            return {
                "bridge_backup_label": variant_label,
                "parameters": dict(parameters),
                "base_validation": {
                    "analysis_result_json": f"{variant_label}_base.json",
                    "base_cagr": 0.35726566 - (0.0 if is_anchor else 0.002),
                    "base_sharpe": 1.86,
                    "base_max_drawdown": 0.091,
                    "sensitivity_max_drift": 0.132,
                    "negative_windows": negative_windows,
                    "idle_windows": [2],
                    "negative_window_count": len(negative_windows),
                    "idle_window_count": 1,
                },
                "cost20_validation": {
                    "analysis_result_json": f"{variant_label}_cost20.json",
                    "cost20_cagr": 0.34639312 - (0.0 if is_anchor else 0.001),
                    "cost20_sharpe": 1.81,
                    "cost20_max_drawdown": 0.095,
                    "sensitivity_max_drift": 0.132,
                    "negative_windows": negative_windows,
                    "idle_windows": [2],
                    "negative_window_count": len(negative_windows),
                    "idle_window_count": 1,
                },
            }

    service = Btc1dPostSpikeBridgeBackupNegativeWindowRepairBatchService(
        analysis_results_dir=tmp_path,
        dual_validation_service=_StubDualValidationService(),
    )
    result = service.run_batch(
        Btc1dPostSpikeBridgeBackupNegativeWindowRepairConfig(periods=1200),
        run_id="btc-1d-post-spike-bridge-backup-negative-window-repair-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")
    assert result["best_variant"]["negative_window_repair_passed"] is True
    assert result["best_variant"]["variant_label"] != "bridge_28_relief"


def test_bridge_backup_negative_window_repair_batch_targets_local_bridge_axes() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}

    assert "bridge_28_relief" in labels
    assert "bridge_28_buffer022_hold34" in labels
    assert "bridge_27_buffer022_hold34" in labels
    assert "bridge_29_relief_hold34" in labels

    anchor = next(variant for variant in DEFAULT_VARIANTS if variant["label"] == "bridge_28_relief")
    repair = next(variant for variant in DEFAULT_VARIANTS if variant["label"] == "bridge_28_buffer022_hold34")

    assert anchor["parameters"]["spike_lookback"] == 28
    assert anchor["parameters"]["max_hold_bars"] == 36
    assert repair["parameters"]["breakout_buffer_pct"] == 0.0022
    assert repair["parameters"]["max_hold_bars"] == 34
