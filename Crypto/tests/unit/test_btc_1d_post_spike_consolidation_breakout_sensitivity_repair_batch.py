from __future__ import annotations

from app.domains.experiments.btc_1d_post_spike_consolidation_breakout_sensitivity_repair_batch import (
    Btc1dPostSpikeConsolidationBreakoutSensitivityRepairBatchService,
    Btc1dPostSpikeConsolidationBreakoutSensitivityRepairConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_consolidation_breakout_sensitivity_repair_batch_runs(tmp_path) -> None:
    service = Btc1dPostSpikeConsolidationBreakoutSensitivityRepairBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dPostSpikeConsolidationBreakoutSensitivityRepairConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-post-spike-consolidation-breakout-sensitivity-repair-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")


def test_sensitivity_repair_batch_variants_follow_repair_winner_micro_axes() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}
    assert "active_baseline_depth050_volume108_hold36" in labels
    assert "depth055_volume108_hold36" in labels
    assert "depth055_volume0972_hold36" in labels

    baseline = next(
        variant for variant in DEFAULT_VARIANTS if variant["label"] == "active_baseline_depth050_volume108_hold36"
    )
    bridge = next(
        variant for variant in DEFAULT_VARIANTS if variant["label"] == "depth055_volume104_hold36"
    )
    floor = next(
        variant for variant in DEFAULT_VARIANTS if variant["label"] == "depth055_volume0972_hold36"
    )

    assert baseline["parameters"]["trend_ema_window"] == 96
    assert baseline["parameters"]["max_consolidation_depth_pct"] == 0.05
    assert baseline["parameters"]["min_volume_ratio"] == 1.08
    assert bridge["parameters"]["trend_ema_window"] == 96
    assert bridge["parameters"]["max_consolidation_depth_pct"] == 0.055
    assert bridge["parameters"]["min_volume_ratio"] == 1.04
    assert floor["parameters"]["max_hold_bars"] == 36
    assert floor["parameters"]["min_volume_ratio"] == 0.972
