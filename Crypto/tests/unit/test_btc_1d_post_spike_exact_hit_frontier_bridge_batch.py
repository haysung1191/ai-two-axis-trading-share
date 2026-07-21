from __future__ import annotations

from app.domains.experiments.btc_1d_post_spike_exact_hit_frontier_bridge_batch import (
    Btc1dPostSpikeExactHitFrontierBridgeBatchService,
    DEFAULT_VARIANTS,
)


def test_exact_hit_frontier_bridge_batch_runs(tmp_path) -> None:
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

    service = Btc1dPostSpikeExactHitFrontierBridgeBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(run_id="btc-1d-post-spike-exact-hit-frontier-bridge-test")

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert "cost20_cagr_edge_vs_promoted_backup" in result["best_variant"]


def test_exact_hit_frontier_bridge_batch_contains_bridge_variants() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}
    assert "exact_hit_anchor" in labels
    assert "gap_anchor_hold36" in labels
    assert "bridge_27_firm" in labels
    assert "bridge_28_relief" in labels
