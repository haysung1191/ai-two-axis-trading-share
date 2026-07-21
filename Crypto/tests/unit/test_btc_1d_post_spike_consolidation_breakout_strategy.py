from __future__ import annotations

import pandas as pd

from strategies.btc_1d_post_spike_consolidation_breakout import (
    _breakout_level,
    _breakout_trigger_passes,
    _consolidation_depth,
    _trend_gate_passes,
    compute_btc_1d_post_spike_consolidation_breakout_signals,
)


def test_post_spike_strategy_exit_confirmation_bars_delays_exit() -> None:
    idx = pd.date_range("2024-01-01", periods=12, freq="D", tz="UTC")
    close = [100, 102, 105, 109, 112, 116, 120, 124, 118, 117, 125, 128]
    frame = pd.DataFrame(
        {
            "open": close,
            "high": [value + 1 for value in close],
            "low": [value - 1 for value in close],
            "close": close,
            "volume": [1000] * len(close),
        },
        index=idx,
    )

    fast_exit = compute_btc_1d_post_spike_consolidation_breakout_signals(
        frame,
        trend_ema_window=3,
        spike_lookback=2,
        min_spike_pct=0.01,
        consolidation_window=2,
        max_consolidation_depth_pct=0.20,
        breakout_buffer_pct=0.0,
        volume_lookback=2,
        min_volume_ratio=0.0,
        stop_ema_window=2,
        max_hold_bars=10,
        exit_confirmation_bars=1,
    )
    delayed_exit = compute_btc_1d_post_spike_consolidation_breakout_signals(
        frame,
        trend_ema_window=3,
        spike_lookback=2,
        min_spike_pct=0.01,
        consolidation_window=2,
        max_consolidation_depth_pct=0.20,
        breakout_buffer_pct=0.0,
        volume_lookback=2,
        min_volume_ratio=0.0,
        stop_ema_window=2,
        max_hold_bars=10,
        exit_confirmation_bars=2,
    )

    assert fast_exit.iloc[8] == 0.0
    assert delayed_exit.iloc[8] == 1.0


def test_post_spike_strategy_entry_confirmation_bars_delays_entry() -> None:
    idx = pd.date_range("2024-01-01", periods=12, freq="D", tz="UTC")
    close = [100, 102, 105, 109, 112, 116, 120, 124, 125, 126, 127, 128]
    frame = pd.DataFrame(
        {
            "open": close,
            "high": [value + 1 for value in close],
            "low": [value - 1 for value in close],
            "close": close,
            "volume": [1000] * len(close),
        },
        index=idx,
    )

    fast_entry = compute_btc_1d_post_spike_consolidation_breakout_signals(
        frame,
        trend_ema_window=3,
        spike_lookback=2,
        min_spike_pct=0.01,
        consolidation_window=2,
        max_consolidation_depth_pct=0.20,
        breakout_buffer_pct=0.0,
        volume_lookback=2,
        min_volume_ratio=0.0,
        stop_ema_window=2,
        max_hold_bars=10,
        entry_confirmation_bars=1,
    )
    delayed_entry = compute_btc_1d_post_spike_consolidation_breakout_signals(
        frame,
        trend_ema_window=3,
        spike_lookback=2,
        min_spike_pct=0.01,
        consolidation_window=2,
        max_consolidation_depth_pct=0.20,
        breakout_buffer_pct=0.0,
        volume_lookback=2,
        min_volume_ratio=0.0,
        stop_ema_window=2,
        max_hold_bars=10,
        entry_confirmation_bars=2,
    )

    assert fast_entry.iloc[6] == 1.0
    assert delayed_entry.iloc[6] == 0.0
    assert delayed_entry.iloc[7] == 1.0


def test_post_spike_strategy_retest_entry_waits_for_pullback_hold() -> None:
    idx = pd.date_range("2024-01-01", periods=12, freq="D", tz="UTC")
    close = [100, 102, 105, 109, 112, 116, 120, 124, 123, 126, 127, 128]
    low = [value - 1 for value in close]
    low[8] = 116.5
    frame = pd.DataFrame(
        {
            "open": close,
            "high": [value + 1 for value in close],
            "low": low,
            "close": close,
            "volume": [1000] * len(close),
        },
        index=idx,
    )

    fast_entry = compute_btc_1d_post_spike_consolidation_breakout_signals(
        frame,
        trend_ema_window=3,
        spike_lookback=2,
        min_spike_pct=0.01,
        consolidation_window=2,
        max_consolidation_depth_pct=0.20,
        breakout_buffer_pct=0.0,
        volume_lookback=2,
        min_volume_ratio=0.0,
        stop_ema_window=2,
        max_hold_bars=10,
        retest_entry_bars=0,
    )
    retest_entry = compute_btc_1d_post_spike_consolidation_breakout_signals(
        frame,
        trend_ema_window=3,
        spike_lookback=2,
        min_spike_pct=0.01,
        consolidation_window=2,
        max_consolidation_depth_pct=0.20,
        breakout_buffer_pct=0.0,
        volume_lookback=2,
        min_volume_ratio=0.0,
        stop_ema_window=2,
        max_hold_bars=10,
        retest_entry_bars=2,
        retest_tolerance_pct=0.01,
    )

    assert fast_entry.iloc[6] == 1.0
    assert retest_entry.iloc[6] == 0.0
    assert retest_entry.iloc[7] == 0.0
    assert retest_entry.iloc[8] == 1.0


def test_post_spike_strategy_profit_lock_exits_after_pullback_from_peak() -> None:
    idx = pd.date_range("2024-01-01", periods=12, freq="D", tz="UTC")
    close = [100, 102, 105, 109, 112, 116, 120, 125, 130, 127, 128, 129]
    frame = pd.DataFrame(
        {
            "open": close,
            "high": [value + 1 for value in close],
            "low": [value - 1 for value in close],
            "close": close,
            "volume": [1000] * len(close),
        },
        index=idx,
    )

    baseline = compute_btc_1d_post_spike_consolidation_breakout_signals(
        frame,
        trend_ema_window=5,
        spike_lookback=2,
        min_spike_pct=0.01,
        consolidation_window=2,
        max_consolidation_depth_pct=0.20,
        breakout_buffer_pct=0.0,
        volume_lookback=2,
        min_volume_ratio=0.0,
        stop_ema_window=5,
        max_hold_bars=10,
    )
    locked = compute_btc_1d_post_spike_consolidation_breakout_signals(
        frame,
        trend_ema_window=5,
        spike_lookback=2,
        min_spike_pct=0.01,
        consolidation_window=2,
        max_consolidation_depth_pct=0.20,
        breakout_buffer_pct=0.0,
        volume_lookback=2,
        min_volume_ratio=0.0,
        stop_ema_window=5,
        max_hold_bars=10,
        profit_lock_trigger_pct=0.05,
        profit_lock_drawdown_pct=0.02,
    )

    assert baseline.iloc[9] == 1.0
    assert locked.iloc[9] == 0.0


def test_post_spike_strategy_trend_gate_mode_ema_rising_allows_below_ema_gate() -> None:
    assert (
        _trend_gate_passes(
            close_value=99.0,
            trend_value=100.0,
            previous_trend_value=98.0,
            tolerance_pct=0.0,
            mode="above_ema",
        )
        is False
    )
    assert (
        _trend_gate_passes(
            close_value=99.0,
            trend_value=100.0,
            previous_trend_value=98.0,
            tolerance_pct=0.0,
            mode="ema_rising",
        )
        is True
    )
    assert (
        _trend_gate_passes(
            close_value=99.0,
            trend_value=100.0,
            previous_trend_value=98.0,
            tolerance_pct=0.0,
            mode="above_or_rising",
        )
        is True
    )


def test_post_spike_strategy_rejects_unknown_trend_gate_mode() -> None:
    idx = pd.date_range("2024-01-01", periods=10, freq="D", tz="UTC")
    close = [100, 102, 105, 109, 112, 116, 120, 124, 123, 126]
    frame = pd.DataFrame(
        {
            "open": close,
            "high": [value + 1 for value in close],
            "low": [value - 1 for value in close],
            "close": close,
            "volume": [1000] * len(close),
        },
        index=idx,
    )

    try:
        compute_btc_1d_post_spike_consolidation_breakout_signals(
            frame,
            trend_ema_window=3,
            spike_lookback=2,
            min_spike_pct=0.01,
            consolidation_window=2,
            max_consolidation_depth_pct=0.20,
            breakout_buffer_pct=0.0,
            volume_lookback=2,
            min_volume_ratio=0.0,
            stop_ema_window=2,
            max_hold_bars=10,
            trend_gate_mode="bad_mode",
        )
    except ValueError as exc:
        assert "trend_gate_mode" in str(exc)
    else:
        raise AssertionError("expected ValueError for unknown trend_gate_mode")


def test_post_spike_strategy_structure_modes_change_depth_and_trigger_logic() -> None:
    assert _consolidation_depth(
        consolidation_high=106.0,
        consolidation_low=100.0,
        consolidation_close_high=104.0,
        consolidation_close_low=102.0,
        mode="close_range",
    ) < _consolidation_depth(
        consolidation_high=106.0,
        consolidation_low=100.0,
        consolidation_close_high=104.0,
        consolidation_close_low=102.0,
        mode="high_low",
    )
    breakout_level = _breakout_level(
        consolidation_high=106.0,
        consolidation_close_high=104.0,
        breakout_buffer_pct=0.0,
        mode="consolidation_close_high",
    )
    assert _breakout_trigger_passes(
        close_value=103.5,
        high_value=104.5,
        breakout_level=breakout_level,
        mode="high",
    ) is True
    assert _breakout_trigger_passes(
        close_value=103.5,
        high_value=104.5,
        breakout_level=breakout_level,
        mode="close",
    ) is False
