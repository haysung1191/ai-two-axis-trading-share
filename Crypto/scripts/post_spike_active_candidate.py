from __future__ import annotations

ACTIVE_CANDIDATE_LABEL = "post_spike_consolidation_breakout_trend960_depth055_volume100_hold36"
ACTIVE_CHALLENGER_LABEL = "post_spike_trend960_depth055_volume100_hold36"
ACTIVE_ARTIFACT_LABEL = "btcusdt_1d_2200_trend960_depth055_volume100_hold36"
ACTIVE_STRATEGY_NAME = "btc_1d_post_spike_consolidation_breakout_v4"
ACTIVE_HYPOTHESIS = (
    "BTCUSDT 1d post-spike consolidation breakout trend960_depth055_volume100_hold36 candidate "
    "aims to promote the approved attack challenger with stronger carry while preserving walk-forward cleanliness."
)
ACTIVE_EXTRA_PARAMETERS = {
    "trend_ema_window": 96.0,
    "spike_lookback": 24,
    "min_spike_pct": 0.085,
    "consolidation_window": 7,
    "max_consolidation_depth_pct": 0.055,
    "breakout_buffer_pct": 0.002,
    "volume_lookback": 20,
    "min_volume_ratio": 1.0,
    "stop_ema_window": 20,
    "max_hold_bars": 36.0,
}
