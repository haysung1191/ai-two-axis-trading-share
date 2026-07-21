from __future__ import annotations

from app.domains.experiments.btc_1d_trend_dip_reversal_breakout_exit_compression_batch import (
    Btc1dTrendDipReversalBreakoutExitCompressionBatchService,
    Btc1dTrendDipReversalBreakoutExitCompressionConfig,
    DEFAULT_VARIANTS,
    build_seed_aligned_variants,
)


def test_btc_1d_trend_dip_reversal_breakout_exit_compression_batch_runs(tmp_path) -> None:
    service = Btc1dTrendDipReversalBreakoutExitCompressionBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dTrendDipReversalBreakoutExitCompressionConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-trend-dip-reversal-breakout-exit-compression-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")


def test_build_seed_aligned_variants_overrides_attack_seed_axes() -> None:
    variants = build_seed_aligned_variants(
        {
            "trend_ema_window": 72,
            "volume_lookback": 18,
            "min_volume_ratio": 1.08,
            "stop_ema_window": 20,
            "max_hold_bars": 34,
        }
    )

    assert len(variants) == len(DEFAULT_VARIANTS)
    assert variants[0]["label"] == "current_reference_seeded"
    assert variants[0]["parameters"]["trend_ema_window"] == 72
    assert variants[0]["parameters"]["volume_lookback"] == 20
    assert variants[0]["parameters"]["min_volume_ratio"] == 1.08
    assert variants[0]["parameters"]["stop_ema_window"] == 20
    assert variants[0]["parameters"]["max_hold_bars"] == 32
    assert variants[1]["parameters"]["reversal_strength_threshold"] == 0.71
    assert variants[1]["parameters"]["min_volume_ratio"] == 1.08
    assert variants[1]["parameters"]["stop_ema_window"] == 20
    assert variants[1]["parameters"]["max_hold_bars"] == 32
    assert variants[2]["parameters"]["volume_lookback"] == 16
    assert variants[2]["parameters"]["max_hold_bars"] == 32
    assert variants[3]["parameters"]["volume_lookback"] == 24
    assert variants[3]["parameters"]["max_hold_bars"] == 32
    assert variants[4]["parameters"]["pullback_window"] == 5
    assert variants[5]["parameters"]["pullback_window"] == 7
    assert variants[6]["parameters"]["swing_lookback"] == 26
    assert variants[7]["parameters"]["swing_lookback"] == 26
    assert variants[7]["parameters"]["pullback_window"] == 5
