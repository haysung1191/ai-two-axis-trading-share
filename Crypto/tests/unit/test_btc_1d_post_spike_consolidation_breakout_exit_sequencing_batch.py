from __future__ import annotations

from app.domains.experiments.btc_1d_post_spike_consolidation_breakout_exit_sequencing_batch import (
    Btc1dPostSpikeConsolidationBreakoutExitSequencingBatchService,
    Btc1dPostSpikeConsolidationBreakoutExitSequencingConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_consolidation_breakout_exit_sequencing_batch_runs(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text("{}", encoding="utf-8")
            return {
                "base_metrics": {
                    "sharpe": 1.1,
                    "cagr": 0.25,
                    "max_drawdown": 0.12,
                },
                "overfitting": {
                    "walk_forward": [
                        {"window": 1, "metrics": {"trades": 2, "sharpe": 0.8, "cagr": 0.2}},
                        {"window": 2, "metrics": {"trades": 0, "sharpe": 0.0, "cagr": 0.0}},
                        {"window": 5, "metrics": {"trades": 1, "sharpe": -0.1, "cagr": -0.01}},
                    ],
                    "sensitivity_max_drift": 0.14,
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeConsolidationBreakoutExitSequencingBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        Btc1dPostSpikeConsolidationBreakoutExitSequencingConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-post-spike-consolidation-breakout-exit-sequencing-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")
    assert "negative_window_count" in result["best_variant"]
    assert "overlay_axis_effective" in result["best_variant"]


def test_exit_sequencing_batch_includes_overlay_exit_axes() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}
    assert "stagnation_exit" in labels
    assert "decay_sizing" in labels
    assert "regime1_stagnation_decay" in labels

    combo = next(variant for variant in DEFAULT_VARIANTS if variant["label"] == "regime1_stagnation_decay")
    assert combo["parameters"]["regime_exit_confirmation_bars"] == 1
    assert combo["parameters"]["stagnation_exit_bars"] == 10
    assert combo["parameters"]["decay_start_bars"] == 6
    assert combo["parameters"]["decay_rate"] == 0.06


def test_exit_sequencing_batch_marks_inert_axes_when_metrics_do_not_change(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text("{}", encoding="utf-8")
            return {
                "base_metrics": {
                    "sharpe": 1.2,
                    "cagr": 0.3,
                    "max_drawdown": 0.1,
                },
                "overfitting": {
                    "walk_forward": [
                        {"window": 2, "metrics": {"trades": 0, "sharpe": 0.0, "cagr": 0.0}},
                        {"window": 5, "metrics": {"trades": 1, "sharpe": -0.1, "cagr": -0.01}},
                    ],
                    "sensitivity_max_drift": 0.15,
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeConsolidationBreakoutExitSequencingBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(run_id="btc-1d-post-spike-consolidation-breakout-exit-sequencing-inert-test")

    assert result["best_variant"]["overlay_axis_effective"] is False
    assert all(row["overlay_axis_effective"] is False for row in result["results"])
