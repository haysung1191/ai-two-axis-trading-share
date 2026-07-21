from __future__ import annotations

import json

from app.domains.experiments.btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch import (
    Btc1dPostSpikeConsolidationBreakoutWalkForwardRepairBatchService,
    Btc1dPostSpikeConsolidationBreakoutWalkForwardRepairConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch_runs(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text(json.dumps({"candidate_label": config.candidate_label}), encoding="utf-8")
            return {
                "base_metrics": {
                    "sharpe": 1.2,
                    "cagr": 0.25,
                    "max_drawdown": 0.11,
                },
                "overfitting": {
                    "walk_forward": [
                        {"window": 1, "metrics": {"trades": 2, "sharpe": 1.0, "cagr": 0.2}},
                        {"window": 2, "metrics": {"trades": 0, "sharpe": 0.0, "cagr": 0.0}},
                    ],
                    "sensitivity_max_drift": 0.14,
                    "unstable_parameters": [],
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeConsolidationBreakoutWalkForwardRepairBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        Btc1dPostSpikeConsolidationBreakoutWalkForwardRepairConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-post-spike-walk-forward-repair-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["best_variant"]["variant_label"] in {variant["label"] for variant in DEFAULT_VARIANTS}
    assert result["analysis_result_json"].endswith(".json")
    payload = json.loads((tmp_path / "btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch_latest.json").read_text(encoding="utf-8"))
    assert payload["repair_focus"]["active_anchor"] == "post_spike_consolidation_breakout_trend960_depth055_volume100_hold36"
    assert payload["repair_focus"]["target_negative_windows"] == []
    assert payload["repair_focus"]["target_idle_windows"] == [2]


def test_btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch_can_filter_variants(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text(json.dumps({"candidate_label": config.candidate_label}), encoding="utf-8")
            return {
                "base_metrics": {
                    "sharpe": 1.2,
                    "cagr": 0.25,
                    "max_drawdown": 0.11,
                },
                "overfitting": {
                    "walk_forward": [
                        {"window": 1, "metrics": {"trades": 2, "sharpe": 1.0, "cagr": 0.2}},
                    ],
                    "sensitivity_max_drift": 0.14,
                    "unstable_parameters": [],
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeConsolidationBreakoutWalkForwardRepairBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        Btc1dPostSpikeConsolidationBreakoutWalkForwardRepairConfig(
            periods=1200,
            variant_labels=(
                "active_baseline",
                "trend9504_depth055_volume100_hold36",
            ),
        ),
        run_id="btc-1d-post-spike-walk-forward-repair-filtered-test",
    )

    assert [row["variant_label"] for row in result["results"]] == [
        "active_baseline",
        "trend9504_depth055_volume100_hold36",
    ]
    assert result["latest_json"].endswith("_latest.json")


def test_walk_forward_repair_batch_contains_active_trend_family_idle_recovery_axes() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}

    assert "active_baseline" in labels
    assert "trend960_depth055_volume100_hold36" in labels
    assert "trend9504_depth055_volume100_hold36" in labels
    assert "trend9504_depth055_volume104_hold36" in labels
    assert "trend9504_depth055_volume100_stop22_hold36" in labels
    assert "trend9504_depth055_volume100_hold32" in labels
    assert "trend9504_depth055_volume104_stop22_hold36" in labels
    assert "trend9504_depth055_volume104_hold32" in labels
    assert "trend9504_depth055_volume104_stop22_hold32" in labels
    assert "trend9696_depth055_volume100_hold36" in labels
    assert "trend1056_depth055_volume100_hold36" in labels
    assert "trend1056_depth055_volume104_hold36" in labels
    assert "trend1056_depth055_volume100_stop22_hold36" in labels
    assert "trend1056_depth055_volume100_hold32" in labels
    assert "trend1056_depth055_volume104_stop22_hold36" in labels
    assert "trend1056_depth055_volume104_stop22_hold36_buffer0015" in labels
    assert "trend1056_depth055_volume104_stop22_hold36_buffer0025" in labels
    assert "trend1056_depth055_volume104_stop22_hold36_consol6" in labels
    assert "trend1056_depth055_volume104_stop22_hold36_consol8" in labels
    assert "trend1056_depth055_volume104_stop22_hold36_spike20" in labels
    assert "trend1056_depth055_volume104_stop22_hold36_spike28" in labels
    assert "trend1056_depth055_volume104_stop22_hold36_minspike080" in labels
    assert "trend1056_depth055_volume104_stop22_hold36_minspike090" in labels
    assert "trend1056_depth055_volume108_stop22_hold36" in labels
    assert "trend1056_depth0605_volume104_stop22_hold36" in labels
    assert "trend1056_depth055_volume104_stop24_hold36" in labels
    assert "trend1056_depth055_volume104_stop22_hold40" in labels
    assert "trend1056_depth055_volume100_stop22_hold32" in labels
    assert "trend1056_depth055_volume104_stop22_hold32" in labels
    assert "trend960_depth055_volume100_hold32" in labels
    assert "trend960_depth055_volume100_hold40" in labels
    assert "trend960_depth055_volume100_stop18_hold36" in labels
    assert "trend960_depth055_volume100_stop22_hold36" in labels
    assert "trend960_depth0605_volume100_hold36" in labels


def test_walk_forward_repair_batch_supports_custom_artifact_stem(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text(json.dumps({"candidate_label": config.candidate_label}), encoding="utf-8")
            return {
                "base_metrics": {
                    "sharpe": 1.0,
                    "cagr": 0.2,
                    "max_drawdown": 0.1,
                },
                "overfitting": {
                    "walk_forward": [
                        {"window": 1, "metrics": {"trades": 1, "sharpe": 1.0, "cagr": 0.2}},
                    ],
                    "sensitivity_max_drift": 0.1,
                    "unstable_parameters": [],
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeConsolidationBreakoutWalkForwardRepairBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )

    result = service.run_batch(
        Btc1dPostSpikeConsolidationBreakoutWalkForwardRepairConfig(
            variant_labels=("trend9504_depth055_volume100_hold36",),
            artifact_stem="btc_1d_post_spike_idle_window_followup_batch",
        ),
        run_id="btc-1d-post-spike-idle-window-followup-test",
    )

    assert "btc_1d_post_spike_idle_window_followup_batch_" in result["analysis_result_json"]
    assert result["latest_json"].endswith("btc_1d_post_spike_idle_window_followup_batch_latest.json")
    assert (tmp_path / "btc_1d_post_spike_idle_window_followup_batch_latest.json").exists()
    assert (tmp_path / "btc_1d_post_spike_idle_window_followup_batch_latest.csv").exists()
