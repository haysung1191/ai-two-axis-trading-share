from __future__ import annotations

from app.domains.experiments.btc_1d_post_spike_consolidation_breakout_exit_defense_batch import (
    Btc1dPostSpikeConsolidationBreakoutExitDefenseBatchService,
    Btc1dPostSpikeConsolidationBreakoutExitDefenseConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_consolidation_breakout_exit_defense_batch_runs(tmp_path) -> None:
    service = Btc1dPostSpikeConsolidationBreakoutExitDefenseBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dPostSpikeConsolidationBreakoutExitDefenseConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-post-spike-consolidation-breakout-exit-defense-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")
    assert "rotation_gap_passed" in result["best_variant"]
