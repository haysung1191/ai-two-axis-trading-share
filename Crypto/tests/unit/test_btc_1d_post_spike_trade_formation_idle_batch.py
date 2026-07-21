from __future__ import annotations

import json

from app.domains.experiments.btc_1d_post_spike_trade_formation_idle_batch import (
    Btc1dPostSpikeTradeFormationIdleBatchService,
    Btc1dPostSpikeTradeFormationIdleConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_trade_formation_idle_batch_runs(tmp_path) -> None:
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

    service = Btc1dPostSpikeTradeFormationIdleBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        Btc1dPostSpikeTradeFormationIdleConfig(),
        run_id="btc-1d-post-spike-trade-formation-idle-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["best_variant"]["window_2_trades"] == 1
    assert result["latest_json"].endswith("_latest.json")


def test_trade_formation_idle_batch_demotes_degenerate_all_idle_variant(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text(json.dumps({"candidate_label": config.candidate_label}), encoding="utf-8")
            label = config.candidate_label.split("::")[-1]
            if label == "retest1_tol001_confirm2":
                return {
                    "base_metrics": {
                        "sharpe": 0.0,
                        "cagr": 0.0,
                        "max_drawdown": 0.0,
                    },
                    "overfitting": {
                        "walk_forward": [
                            {"window": 1, "metrics": {"trades": 0, "sharpe": 0.0, "cagr": 0.0, "equity_curve_summary": {"start": 1.0, "end": 1.0}}},
                            {"window": 2, "metrics": {"trades": 0, "sharpe": 0.0, "cagr": 0.0, "equity_curve_summary": {"start": 1.0, "end": 1.0}}},
                            {"window": 3, "metrics": {"trades": 0, "sharpe": 0.0, "cagr": 0.0, "equity_curve_summary": {"start": 1.0, "end": 1.0}}},
                            {"window": 4, "metrics": {"trades": 0, "sharpe": 0.0, "cagr": 0.0, "equity_curve_summary": {"start": 1.0, "end": 1.0}}},
                            {"window": 5, "metrics": {"trades": 0, "sharpe": 0.0, "cagr": 0.0, "equity_curve_summary": {"start": 1.0, "end": 1.0}}},
                        ],
                        "sensitivity_max_drift": 999999.0,
                    },
                    "analysis_result_json": str(analysis_path),
                }
            return {
                "base_metrics": {
                    "sharpe": 1.3,
                    "cagr": 0.27,
                    "max_drawdown": 0.12,
                },
                "overfitting": {
                    "walk_forward": [
                        {"window": 2, "metrics": {"trades": 0, "sharpe": 0.0, "cagr": 0.0, "equity_curve_summary": {"start": 1.0, "end": 1.0}}},
                        {"window": 4, "metrics": {"trades": 2, "sharpe": -0.1, "cagr": -0.02, "equity_curve_summary": {"start": 1.0, "end": 0.98}}},
                    ],
                    "sensitivity_max_drift": 0.2,
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeTradeFormationIdleBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        Btc1dPostSpikeTradeFormationIdleConfig(),
        run_id="btc-1d-post-spike-trade-formation-idle-degenerate-test",
    )

    assert result["best_variant"]["variant_label"] != "retest1_tol001_confirm2"
    degenerate = next(row for row in result["results"] if row["variant_label"] == "retest1_tol001_confirm2")
    assert degenerate["formation_viable"] is False


def test_post_spike_trade_formation_idle_batch_contains_retest_and_confirmation_variants() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}

    assert "formation_anchor" in labels
    assert "retest1_tol001" in labels
    assert "retest2_tol002" in labels
    assert "confirm2" in labels
    assert "retest1_tol001_confirm2" in labels
    assert "exitconfirm2" in labels
