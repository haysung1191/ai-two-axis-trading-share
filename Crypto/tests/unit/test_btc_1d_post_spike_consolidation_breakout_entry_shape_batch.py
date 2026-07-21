from __future__ import annotations

from app.domains.experiments.btc_1d_post_spike_consolidation_breakout_entry_shape_batch import (
    Btc1dPostSpikeConsolidationBreakoutEntryShapeBatchService,
    Btc1dPostSpikeConsolidationBreakoutEntryShapeConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_consolidation_breakout_entry_shape_batch_runs(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text("{}", encoding="utf-8")
            return {
                "base_metrics": {
                    "sharpe": 1.4,
                    "cagr": 0.31,
                    "max_drawdown": 0.11,
                },
                "overfitting": {
                    "walk_forward": [
                        {"window": 2, "metrics": {"trades": 0, "sharpe": 0.0, "cagr": 0.0}},
                        {"window": 5, "metrics": {"trades": 2, "sharpe": 0.4, "cagr": 0.08}},
                    ],
                    "sensitivity_max_drift": 0.18,
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeConsolidationBreakoutEntryShapeBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        Btc1dPostSpikeConsolidationBreakoutEntryShapeConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-post-spike-consolidation-breakout-entry-shape-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")
    assert "cagr_delta_vs_entry_anchor" in result["best_variant"]
    assert "repair_profile_kept" in result["best_variant"]
    assert result["latest_json"].endswith("_latest.json")


def test_entry_shape_batch_targets_current_repair_anchor_profile() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}
    assert "anchor_entry_shape" in labels
    assert "volume_memory_relief_entry_shape" in labels

    anchor = next(variant for variant in DEFAULT_VARIANTS if variant["label"] == "anchor_entry_shape")
    relief = next(
        variant for variant in DEFAULT_VARIANTS if variant["label"] == "volume_memory_relief_entry_shape"
    )

    assert anchor["parameters"]["trend_ema_window"] == 105.6
    assert anchor["parameters"]["max_hold_bars"] == 36
    assert anchor["parameters"]["min_spike_pct"] == 0.085
    assert anchor["parameters"]["stop_ema_window"] == 22.0
    assert relief["parameters"]["volume_lookback"] == 18
    assert relief["parameters"]["min_volume_ratio"] == 1.02
