from __future__ import annotations

from app.domains.experiments.btc_1d_post_spike_consolidation_breakout_guardrail_repair_batch import (
    Btc1dPostSpikeConsolidationBreakoutGuardrailRepairBatchService,
    Btc1dPostSpikeConsolidationBreakoutGuardrailRepairConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_post_spike_consolidation_breakout_guardrail_repair_batch_runs(tmp_path) -> None:
    service = Btc1dPostSpikeConsolidationBreakoutGuardrailRepairBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dPostSpikeConsolidationBreakoutGuardrailRepairConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-post-spike-consolidation-breakout-guardrail-repair-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")
    assert "drift_guardrail_passed" in result["best_variant"]


def test_guardrail_repair_batch_targets_low_drift_negative_window_repairs() -> None:
    labels = {variant["label"] for variant in DEFAULT_VARIANTS}
    assert "low_drift_anchor" in labels
    assert "hold36_trend95_volume1069_bridge" in labels

    anchor = next(variant for variant in DEFAULT_VARIANTS if variant["label"] == "low_drift_anchor")
    combo = next(variant for variant in DEFAULT_VARIANTS if variant["label"] == "hold36_trend95_volume1069_bridge")

    assert anchor["parameters"]["trend_ema_window"] == 86.4
    assert anchor["parameters"]["min_volume_ratio"] == 0.972
    assert anchor["parameters"]["max_hold_bars"] == 32.4
    assert combo["parameters"]["trend_ema_window"] == 95.04
    assert combo["parameters"]["min_volume_ratio"] == 1.0692
    assert combo["parameters"]["max_hold_bars"] == 35.64
