from __future__ import annotations

import json

from app.domains.experiments.btc_1d_post_spike_breakout_structure_profit_lock_micro_batch import (
    Btc1dPostSpikeBreakoutStructureProfitLockMicroBatchService,
    Btc1dPostSpikeBreakoutStructureProfitLockMicroConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_breakout_structure_profit_lock_micro_batch_runs(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir

        def run_diagnostic(self, config, *, run_id=None):
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text(json.dumps({"candidate_label": config.candidate_label}), encoding="utf-8")
            if "050_015" in config.candidate_label:
                window2_cagr = -0.03
                window5_cagr = -0.01
                drawdown = 0.28
            else:
                window2_cagr = -0.07
                window5_cagr = -0.03
                drawdown = 0.34
            return {
                "base_metrics": {
                    "sharpe": 0.8,
                    "cagr": 0.15,
                    "max_drawdown": drawdown,
                },
                "overfitting": {
                    "walk_forward": [
                        {"window": 2, "metrics": {"trades": 4, "cagr": window2_cagr}},
                        {"window": 5, "metrics": {"trades": 4, "cagr": window5_cagr}},
                    ],
                    "sensitivity_max_drift": 0.36,
                },
                "analysis_result_json": str(analysis_path),
            }

    service = Btc1dPostSpikeBreakoutStructureProfitLockMicroBatchService(
        analysis_results_dir=tmp_path,
        diagnostic_service=_StubDiagnosticService(tmp_path),
    )
    result = service.run_batch(
        Btc1dPostSpikeBreakoutStructureProfitLockMicroConfig(),
        run_id="btc-1d-post-spike-breakout-structure-profit-lock-micro-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["best_variant"]["variant_label"] == "profit_lock_050_015"
    assert result["latest_json"].endswith("_latest.json")


def test_post_spike_breakout_structure_profit_lock_micro_batch_contains_variants() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}
    assert "profit_lock_anchor_060_020" in labels
    assert "profit_lock_050_020" in labels
    assert "profit_lock_050_015" in labels
    assert "profit_lock_060_015" in labels
    assert "profit_lock_070_020" in labels
    assert "profit_lock_off" in labels
