from __future__ import annotations

import json

from app.domains.experiments.btc_1d_post_spike_trend_gate_relaxation_batch import (
    Btc1dPostSpikeTrendGateRelaxationBatchService,
    Btc1dPostSpikeTrendGateRelaxationConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_trend_gate_relaxation_batch_runs(tmp_path) -> None:
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
                        {"window": 2, "metrics": {"trades": 1, "cagr": 0.02, "equity_curve_summary": {"end": 1.02}}},
                        {"window": 4, "metrics": {"trades": 2, "sharpe": -0.1, "cagr": -0.02, "equity_curve_summary": {"end": 0.98}}},
                    ],
                    "sensitivity_max_drift": 0.14,
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeTrendGateRelaxationBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        Btc1dPostSpikeTrendGateRelaxationConfig(),
        run_id="btc-1d-post-spike-trend-gate-relaxation-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["best_variant"]["window_2_trades"] == 1
    assert result["latest_json"].endswith("_latest.json")


def test_post_spike_trend_gate_relaxation_batch_contains_tolerance_variants() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}
    assert "trend_gate_anchor" in labels
    assert "trend_gate_tol0025" in labels
    assert "trend_gate_tol0050" in labels
    assert "trend_gate_tol0075" in labels
    assert "trend_gate_tol0100" in labels
    assert "trend_gate_tol0050_confirm2" in labels
