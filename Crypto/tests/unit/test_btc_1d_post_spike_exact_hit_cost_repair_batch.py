from __future__ import annotations

from app.domains.experiments.btc_1d_post_spike_exact_hit_cost_repair_batch import (
    Btc1dPostSpikeExactHitCostRepairBatchService,
    Btc1dPostSpikeExactHitCostRepairConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_exact_hit_cost_repair_batch_runs(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text("{}", encoding="utf-8")
            return {
                "base_metrics": {
                    "sharpe": 1.8,
                    "cagr": 0.345,
                    "max_drawdown": 0.095,
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

    service = Btc1dPostSpikeExactHitCostRepairBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        Btc1dPostSpikeExactHitCostRepairConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-post-spike-exact-hit-cost-repair-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")
    assert "cost20_cagr_edge_vs_promoted_backup" in result["best_variant"]
    assert "drift_guardrail_passed" in result["best_variant"]


def test_exact_hit_cost_repair_batch_includes_cost_retention_axes() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}
    assert "exact_hit_anchor" in labels
    assert "volume100_hold34" in labels
    assert "buffer020_volume100" in labels

    volume_hold = next(variant for variant in DEFAULT_VARIANTS if variant["label"] == "volume100_hold34")
    depth_stop = next(variant for variant in DEFAULT_VARIANTS if variant["label"] == "depth058_stop18")

    assert volume_hold["parameters"]["min_volume_ratio"] == 1.0
    assert volume_hold["parameters"]["max_hold_bars"] == 34
    assert depth_stop["parameters"]["max_consolidation_depth_pct"] == 0.058
    assert depth_stop["parameters"]["stop_ema_window"] == 18


def test_exact_hit_cost_repair_batch_can_filter_variants(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text("{}", encoding="utf-8")
            return {
                "base_metrics": {
                    "sharpe": 1.8,
                    "cagr": 0.345,
                    "max_drawdown": 0.095,
                },
                "overfitting": {
                    "walk_forward": [],
                    "sensitivity_max_drift": 0.18,
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeExactHitCostRepairBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        run_id="btc-1d-post-spike-exact-hit-cost-repair-filter-test",
        variant_labels=["exact_hit_anchor", "stop22"],
    )

    assert [row["variant_label"] for row in result["results"]] == ["exact_hit_anchor", "stop22"]
