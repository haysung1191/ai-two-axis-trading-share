from __future__ import annotations

import json

from app.domains.experiments.btc_1d_post_spike_breakout_structure_mode_batch import (
    Btc1dPostSpikeBreakoutStructureModeBatchService,
    Btc1dPostSpikeBreakoutStructureModeConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_breakout_structure_mode_batch_runs(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text(json.dumps({"candidate_label": config.candidate_label}), encoding="utf-8")
            if "close_range_close_ref_high_trigger" in config.candidate_label:
                trades = 2
                cagr = 0.03
            else:
                trades = 0
                cagr = 0.0
            return {
                "base_metrics": {
                    "sharpe": 1.2,
                    "cagr": 0.25,
                    "max_drawdown": 0.11,
                },
                "overfitting": {
                    "walk_forward": [
                        {"window": 2, "metrics": {"trades": trades, "cagr": cagr, "equity_curve_summary": {"end": 1.0 + cagr}}},
                        {"window": 4, "metrics": {"trades": 2, "sharpe": -0.1, "cagr": -0.02, "equity_curve_summary": {"end": 0.98}}},
                    ],
                    "sensitivity_max_drift": 0.14,
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeBreakoutStructureModeBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        Btc1dPostSpikeBreakoutStructureModeConfig(),
        run_id="btc-1d-post-spike-breakout-structure-mode-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["best_variant"]["window_2_trades"] == 2
    assert result["best_variant"]["variant_label"].startswith("close_range_close_ref_high_trigger")
    assert result["latest_json"].endswith("_latest.json")


def test_post_spike_breakout_structure_mode_batch_contains_expected_variants() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}
    assert "structure_anchor" in labels
    assert "close_range_close_ref_high_trigger" in labels
    assert "close_range_close_ref_close_trigger" in labels
    assert "close_range_high_ref_high_trigger" in labels
    assert "close_range_close_ref_high_trigger_above_or_rising" in labels
