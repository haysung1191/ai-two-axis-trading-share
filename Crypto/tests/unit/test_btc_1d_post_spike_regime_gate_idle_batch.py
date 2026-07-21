from __future__ import annotations

import json

from app.domains.experiments.btc_1d_post_spike_regime_gate_idle_batch import (
    Btc1dPostSpikeRegimeGateIdleBatchService,
    Btc1dPostSpikeRegimeGateIdleConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_regime_gate_idle_batch_runs(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text(json.dumps({"candidate_label": config.candidate_label}), encoding="utf-8")
            return {
                "base_metrics": {
                    "sharpe": 1.3,
                    "cagr": 0.27,
                    "max_drawdown": 0.12,
                },
                "overfitting": {
                    "walk_forward": [
                        {"window": 2, "metrics": {
                            "trades": 1,
                            "sharpe": 0.2,
                            "cagr": 0.03,
                            "equity_curve_summary": {"start": 1.0, "end": 1.03},
                        }},
                        {"window": 4, "metrics": {"trades": 2, "sharpe": -0.1, "cagr": -0.02}},
                    ],
                    "sensitivity_max_drift": 0.2,
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeRegimeGateIdleBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        Btc1dPostSpikeRegimeGateIdleConfig(),
        run_id="btc-1d-post-spike-regime-gate-idle-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["best_variant"]["window_2_trades"] == 1
    assert result["latest_json"].endswith("_latest.json")


def test_post_spike_regime_gate_idle_batch_contains_anchor_and_reentry_variants() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}

    assert "anchor_regime_gate" in labels
    assert "faster_recovery_gate" in labels
    assert "short_memory_gate" in labels
    assert "looser_risk_gate" in labels
    assert "higher_floor_gate" in labels
    assert "cooldown_reentry_gate" in labels
