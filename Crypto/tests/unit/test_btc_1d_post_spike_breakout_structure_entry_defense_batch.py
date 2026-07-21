from __future__ import annotations

import json

from app.domains.experiments.btc_1d_post_spike_breakout_structure_entry_defense_batch import (
    Btc1dPostSpikeBreakoutStructureEntryDefenseBatchService,
    Btc1dPostSpikeBreakoutStructureEntryDefenseConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_breakout_structure_entry_defense_batch_runs(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text(json.dumps({"candidate_label": config.candidate_label}), encoding="utf-8")
            if "confirm2" in config.candidate_label and "retest" not in config.candidate_label:
                window2_cagr = -0.02
                window5_cagr = -0.01
                negative_window5 = -0.01
            else:
                window2_cagr = -0.07
                window5_cagr = -0.02
                negative_window5 = -0.02
            return {
                "base_metrics": {
                    "sharpe": 0.8,
                    "cagr": 0.15,
                    "max_drawdown": 0.33,
                },
                "overfitting": {
                    "walk_forward": [
                        {"window": 2, "metrics": {"trades": 4, "cagr": window2_cagr}},
                        {"window": 5, "metrics": {"trades": 4, "cagr": negative_window5}},
                    ],
                    "sensitivity_max_drift": 0.36,
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeBreakoutStructureEntryDefenseBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        Btc1dPostSpikeBreakoutStructureEntryDefenseConfig(),
        run_id="btc-1d-post-spike-breakout-structure-entry-defense-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["best_variant"]["variant_label"] == "confirm2"
    assert result["latest_json"].endswith("_latest.json")
    assert result["best_variant"]["entry_viable"] is True


def test_entry_defense_batch_demotes_all_idle_variants(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text(json.dumps({"candidate_label": config.candidate_label}), encoding="utf-8")
            if "retest1_tol001_confirm2" in config.candidate_label:
                walk_forward = [{"window": i, "metrics": {"trades": 0, "cagr": 0.0}} for i in range(1, 6)]
                base_metrics = {"sharpe": 0.0, "cagr": 0.0, "max_drawdown": 0.0}
                drift = 9999.0
            else:
                walk_forward = [
                    {"window": 2, "metrics": {"trades": 4, "cagr": -0.02}},
                    {"window": 5, "metrics": {"trades": 4, "cagr": -0.01}},
                ]
                base_metrics = {"sharpe": 0.8, "cagr": 0.15, "max_drawdown": 0.33}
                drift = 0.36
            return {
                "base_metrics": base_metrics,
                "overfitting": {
                    "walk_forward": walk_forward,
                    "sensitivity_max_drift": drift,
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeBreakoutStructureEntryDefenseBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        Btc1dPostSpikeBreakoutStructureEntryDefenseConfig(),
        run_id="btc-1d-post-spike-breakout-structure-entry-defense-demotion-test",
    )
    assert result["best_variant"]["variant_label"] != "retest1_tol001_confirm2"
    degenerate = next(row for row in result["results"] if row["variant_label"] == "retest1_tol001_confirm2")
    assert degenerate["entry_viable"] is False


def test_post_spike_breakout_structure_entry_defense_batch_contains_variants() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}
    assert "entry_anchor" in labels
    assert "confirm2" in labels
    assert "retest1_tol001" in labels
    assert "retest2_tol002" in labels
    assert "retest1_tol001_confirm2" in labels
    assert "exitconfirm2" in labels
