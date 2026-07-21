from __future__ import annotations

import json

from app.domains.experiments.btc_1d_post_spike_breakout_structure_exit_defense_batch import (
    Btc1dPostSpikeBreakoutStructureExitDefenseBatchService,
    Btc1dPostSpikeBreakoutStructureExitDefenseConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_breakout_structure_exit_defense_batch_runs(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text(json.dumps({"candidate_label": config.candidate_label}), encoding="utf-8")
            if "hold28_stop24" in config.candidate_label:
                window2_cagr = -0.01
                window5_cagr = -0.005
                drawdown = 0.30
            else:
                window2_cagr = -0.11
                window5_cagr = -0.04
                drawdown = 0.50
            return {
                "base_metrics": {
                    "sharpe": 1.0,
                    "cagr": 0.20,
                    "max_drawdown": drawdown,
                },
                "overfitting": {
                    "walk_forward": [
                        {"window": 2, "metrics": {"trades": 4, "cagr": window2_cagr}},
                        {"window": 5, "metrics": {"trades": 3, "cagr": window5_cagr}},
                    ],
                    "sensitivity_max_drift": 0.25,
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeBreakoutStructureExitDefenseBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        Btc1dPostSpikeBreakoutStructureExitDefenseConfig(),
        run_id="btc-1d-post-spike-breakout-structure-exit-defense-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["best_variant"]["variant_label"] == "hold28_stop24"
    assert result["latest_json"].endswith("_latest.json")


def test_post_spike_breakout_structure_exit_defense_batch_contains_expected_variants() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}
    assert "structure_exit_anchor" in labels
    assert "hold28" in labels
    assert "hold24" in labels
    assert "stop24" in labels
    assert "hold28_stop24" in labels
    assert "hold24_stop24" in labels
    assert "profit_lock_060_020" in labels
