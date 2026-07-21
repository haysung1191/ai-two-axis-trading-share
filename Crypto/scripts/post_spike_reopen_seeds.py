from __future__ import annotations

SEED_DEFINITIONS: dict[str, dict] = {
    "post_spike_walk_forward_repair::trend84_depth055_volume104_hold34": {
        "artifact_label": "btcusdt_1d_2200_trend84_depth055_volume104_hold34_reopen_seed",
        "candidate_label": "post_spike_walk_forward_repair::trend84_depth055_volume104_hold34",
        "strategy_name": "btc_1d_post_spike_consolidation_breakout_v4",
        "hypothesis": (
            "Trend84 depth055 volume104 hold34 repair winner is the first reopen seed because it previously"
            " cleared validation, friction, and walk-forward stage gates."
        ),
        "parameters": {
            "trend_ema_window": 84,
            "spike_lookback": 28,
            "min_spike_pct": 0.095,
            "consolidation_window": 8,
            "max_consolidation_depth_pct": 0.058,
            "breakout_buffer_pct": 0.0025,
            "volume_lookback": 22,
            "min_volume_ratio": 1.05,
            "stop_ema_window": 20,
            "max_hold_bars": 36,
        },
    },
    "trend92_stronger_spike_hold34": {
        "artifact_label": "btcusdt_1d_2200_trend92_stronger_spike_hold34_reopen_seed",
        "candidate_label": "trend92_stronger_spike_hold34",
        "strategy_name": "btc_1d_post_spike_consolidation_breakout_v4",
        "hypothesis": (
            "Trend92 stronger spike hold34 is the backup reopen seed because it remains on the post-spike"
            " frontier with drift guardrail intact."
        ),
        "parameters": {
            "trend_ema_window": 92,
            "spike_lookback": 28,
            "min_spike_pct": 0.1045,
            "consolidation_window": 8,
            "max_consolidation_depth_pct": 0.058,
            "breakout_buffer_pct": 0.0025,
            "volume_lookback": 22,
            "min_volume_ratio": 1.05,
            "stop_ema_window": 20,
            "max_hold_bars": 34,
        },
    },
}


PREFERRED_REOPEN_SEED = "post_spike_walk_forward_repair::trend84_depth055_volume104_hold34"
BACKUP_REOPEN_SEED = "trend92_stronger_spike_hold34"
