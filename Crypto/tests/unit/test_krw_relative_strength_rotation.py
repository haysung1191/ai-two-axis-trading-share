from __future__ import annotations

import math

import pandas as pd

from app.domains.strategy.krw_relative_strength_rotation import (
    compute_btc_filter_on,
    compute_relative_strength_score,
    compute_rotation_snapshot,
)


def _frame_from_closes(closes: list[float]) -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=len(closes), freq="h", tz="UTC")
    close = pd.Series(closes, index=idx, dtype=float)
    frame = pd.DataFrame(index=idx)
    frame["open"] = close
    frame["high"] = close + 1.0
    frame["low"] = close - 1.0
    frame["close"] = close
    frame["volume"] = 1000.0
    return frame


def test_btc_regime_filter_on_and_off() -> None:
    btc_on = _frame_from_closes([100.0 + i for i in range(80)])
    btc_off = _frame_from_closes([180.0 - i for i in range(80)])

    assert compute_btc_filter_on(btc_on) is True
    assert compute_btc_filter_on(btc_off) is False


def test_relative_strength_score_uses_24h_return_divided_by_24h_atr_percent() -> None:
    asset = _frame_from_closes([100.0 + i for i in range(25)])

    score = compute_relative_strength_score(asset)

    expected_return = (124.0 / 100.0) - 1.0
    expected_atr_pct = 2.0 / 124.0
    expected_score = expected_return / expected_atr_pct
    assert math.isclose(score, expected_score, rel_tol=1e-9)


def test_rotation_snapshot_selects_top_three_symbols_by_score() -> None:
    btc = _frame_from_closes([100.0 + i for i in range(80)])
    snapshot = compute_rotation_snapshot(
        btc,
        {
            "KRW-ALPHA": _frame_from_closes([100.0 + (i * 2.0) for i in range(25)]),
            "KRW-BETA": _frame_from_closes([100.0 + (i * 1.5) for i in range(25)]),
            "KRW-GAMMA": _frame_from_closes([100.0 + (i * 1.0) for i in range(25)]),
            "KRW-DELTA": _frame_from_closes([100.0 + (i * 0.5) for i in range(25)]),
        },
    )

    assert snapshot.btc_filter_on is True
    assert set(snapshot.scores.keys()) == {"KRW-ALPHA", "KRW-BETA", "KRW-GAMMA", "KRW-DELTA"}
    assert snapshot.top_symbols == ["KRW-ALPHA", "KRW-BETA", "KRW-GAMMA"]
