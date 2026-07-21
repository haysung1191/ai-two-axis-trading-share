from __future__ import annotations

import pandas as pd

from strategies.btc_4h_trend_regime_persistence_strength_filter_mvp import (
    compute_btc_4h_trend_regime_persistence_strength_filter_signals,
)


def _build_frame(closes: list[float]) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=len(closes), freq="4h", tz="UTC")
    close = pd.Series(closes, index=idx, dtype=float)
    return pd.DataFrame(
        {
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )


def test_btc_4h_strategy_enters_on_trend_persistence_and_strength() -> None:
    frame = _build_frame([100.0 + (i * 1.2) for i in range(120)])

    signal = compute_btc_4h_trend_regime_persistence_strength_filter_signals(frame)

    assert signal.iloc[60] == 0.0
    assert signal.iloc[90] == 1.0
    assert signal.iloc[-1] == 1.0


def test_btc_4h_strategy_rejects_when_strength_filter_is_not_met() -> None:
    frame = _build_frame([100.0 + (i * 0.03) for i in range(120)])

    signal = compute_btc_4h_trend_regime_persistence_strength_filter_signals(frame)

    assert (signal == 0.0).all()


def test_btc_4h_strategy_exits_on_regime_breakdown() -> None:
    rising = [100.0 + (i * 1.5) for i in range(120)]
    breakdown = [rising[-1] - 5.0, rising[-1] - 12.0, rising[-1] - 24.0, rising[-1] - 40.0]
    frame = _build_frame(rising + breakdown)

    signal = compute_btc_4h_trend_regime_persistence_strength_filter_signals(frame)

    assert signal.iloc[100] == 1.0
    assert signal.iloc[-1] == 0.0


def test_btc_4h_strategy_waits_for_confirmed_fast_break_before_exit() -> None:
    rising = [100.0 + (i * 1.5) for i in range(120)]
    tail = [rising[-1] - 25.0, rising[-1] + 5.0, rising[-1] - 30.0, rising[-1] - 40.0]
    frame = _build_frame(rising + tail)

    signal = compute_btc_4h_trend_regime_persistence_strength_filter_signals(
        frame,
        fast_break_confirmation_bars=2,
    )

    assert signal.iloc[120] == 1.0
    assert signal.iloc[121] == 1.0
    assert signal.iloc[-1] == 0.0


def test_btc_4h_strategy_returns_flat_signal_when_history_is_short() -> None:
    frame = _build_frame([100.0 + i for i in range(20)])
    signal = compute_btc_4h_trend_regime_persistence_strength_filter_signals(frame)
    assert (signal == 0.0).all()
