from __future__ import annotations

import json

from app.domains.experiments.btc_1d_post_spike_trend_gate_mode_batch import (
    Btc1dPostSpikeTrendGateModeBatchService,
    Btc1dPostSpikeTrendGateModeConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_trend_gate_mode_batch_runs(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text(json.dumps({"candidate_label": config.candidate_label}), encoding="utf-8")
            if "above_or_rising" in config.candidate_label:
                window2_trades = 2
                window2_cagr = 0.04
            else:
                window2_trades = 0
                window2_cagr = 0.0
            return {
                "base_metrics": {
                    "sharpe": 1.2,
                    "cagr": 0.25,
                    "max_drawdown": 0.11,
                },
                "overfitting": {
                    "walk_forward": [
                        {
                            "window": 2,
                            "metrics": {
                                "trades": window2_trades,
                                "cagr": window2_cagr,
                                "equity_curve_summary": {"end": 1.0 + window2_cagr},
                            },
                        },
                        {"window": 4, "metrics": {"trades": 2, "sharpe": -0.1, "cagr": -0.02, "equity_curve_summary": {"end": 0.98}}},
                    ],
                    "sensitivity_max_drift": 0.14,
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeTrendGateModeBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        Btc1dPostSpikeTrendGateModeConfig(),
        run_id="btc-1d-post-spike-trend-gate-mode-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["best_variant"]["window_2_trades"] == 2
    assert result["best_variant"]["variant_label"].startswith("trend_gate_mode_above_or_rising")
    assert result["latest_json"].endswith("_latest.json")


def test_post_spike_trend_gate_mode_batch_contains_mode_variants() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}
    assert "trend_gate_mode_anchor" in labels
    assert "trend_gate_mode_ema_rising" in labels
    assert "trend_gate_mode_above_or_rising" in labels
    assert "trend_gate_mode_above_or_rising_tol0050" in labels
    assert "trend_gate_mode_ema_rising_confirm2" in labels
