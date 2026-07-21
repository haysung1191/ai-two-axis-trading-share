from __future__ import annotations

import pandas as pd

from app.domains.strategy.krw_btc_mean_reversion import compute_mean_reversion_signals


def _build_frame(closes: list[float]) -> pd.DataFrame:
    idx = pd.date_range('2024-01-01', periods=len(closes), freq='h', tz='UTC')
    close = pd.Series(closes, index=idx, dtype=float)
    return pd.DataFrame(
        {
            'open': close,
            'high': close + 1.0,
            'low': close - 1.0,
            'close': close,
            'volume': 1000.0,
        },
        index=idx,
    )


def test_krw_btc_mean_reversion_enters_on_oversold_and_exits_on_sma_reclaim() -> None:
    stable = [100.0] * 20
    dump = [90.0, 88.0, 87.0, 89.0, 93.0, 98.0, 101.0, 103.0]
    frame = _build_frame(stable + dump)

    signal = compute_mean_reversion_signals(frame)

    assert signal.iloc[19] == 0.0
    assert signal.iloc[22] == 1.0
    assert signal.iloc[-1] == 0.0


def test_krw_btc_mean_reversion_stays_flat_when_history_is_short() -> None:
    frame = _build_frame([100.0 + i for i in range(10)])
    signal = compute_mean_reversion_signals(frame)
    assert (signal == 0.0).all()
