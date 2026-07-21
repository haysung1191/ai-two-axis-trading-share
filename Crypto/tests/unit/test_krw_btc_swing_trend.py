from __future__ import annotations

import pandas as pd

from app.domains.strategy.krw_btc_swing_trend import compute_swing_trend_signals


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


def test_krw_btc_swing_trend_enters_and_exits_on_ema_rules() -> None:
    rising = [100.0 + i for i in range(80)]
    falling_tail = [178.0, 176.0, 170.0, 160.0, 150.0, 140.0, 130.0, 120.0]
    frame = _build_frame(rising + falling_tail)

    signal = compute_swing_trend_signals(frame, fast_ema_window=20, slow_ema_window=72)

    assert signal.iloc[70] == 0.0
    assert signal.iloc[79] == 1.0
    assert signal.iloc[-1] == 0.0


def test_krw_btc_swing_trend_returns_flat_signal_when_history_is_short() -> None:
    frame = _build_frame([100.0 + i for i in range(20)])
    signal = compute_swing_trend_signals(frame, fast_ema_window=20, slow_ema_window=72)
    assert (signal == 0.0).all()
