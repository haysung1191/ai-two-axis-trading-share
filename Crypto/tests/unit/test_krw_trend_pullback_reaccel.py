from __future__ import annotations

import math

import pandas as pd

from app.domains.strategy.krw_trend_pullback_reaccel import (
    compute_btc_filter_on,
    compute_pullback_pass,
    compute_ranking_score,
    compute_reaccel_pass,
    compute_trend_pass,
    compute_trend_pullback_reaccel_snapshot,
)


def _frame_from_closes_lows_and_offsets(
    closes: list[float],
    *,
    lows: list[float] | None = None,
    high_offset: float = 1.0,
    low_offset: float = 1.0,
) -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=len(closes), freq="h", tz="UTC")
    close = pd.Series(closes, index=idx, dtype=float)
    frame = pd.DataFrame(index=idx)
    frame["open"] = close
    frame["high"] = close + high_offset
    if lows is None:
        frame["low"] = close - low_offset
    else:
        frame["low"] = pd.Series(lows, index=idx, dtype=float)
    frame["close"] = close
    frame["volume"] = 1000.0
    return frame


def test_btc_regime_filter_on_and_off() -> None:
    btc_on = _frame_from_closes_lows_and_offsets([100.0 + i for i in range(80)])
    btc_off = _frame_from_closes_lows_and_offsets([180.0 - i for i in range(80)])

    assert compute_btc_filter_on(btc_on) is True
    assert compute_btc_filter_on(btc_off) is False


def test_trend_pass_requires_close_above_ema72_and_ema20_above_ema72() -> None:
    trend_on = _frame_from_closes_lows_and_offsets([100.0 + i for i in range(80)])
    trend_off = _frame_from_closes_lows_and_offsets([180.0 - i for i in range(80)])

    assert compute_trend_pass(trend_on) is True
    assert compute_trend_pass(trend_off) is False


def test_pullback_and_reaccel_pass_follow_mvp_rules() -> None:
    closes = [100.0 + i for i in range(74)]
    closes += [172.0, 173.0, 174.0, 175.0, 176.0, 177.0]
    closes += [178.0, 179.0, 182.0]
    lows = closes[:-9] + [170.0, 171.0, 172.0, 173.0, 174.0, 175.0, 177.0, 178.0, 181.0]
    frame = _frame_from_closes_lows_and_offsets(closes, lows=lows)

    assert compute_pullback_pass(frame) is True
    assert compute_reaccel_pass(frame) is True


def test_ranking_score_uses_12h_return_divided_by_atr14_percent() -> None:
    closes = [100.0 + i for i in range(15)]
    frame = _frame_from_closes_lows_and_offsets(closes)

    score = compute_ranking_score(frame)

    expected_return = (114.0 / 102.0) - 1.0
    expected_atr_pct = 2.0 / 114.0
    expected_score = expected_return / expected_atr_pct
    assert math.isclose(score, expected_score, rel_tol=1e-9)


def test_snapshot_selects_top_three_candidates_by_ranking_score() -> None:
    btc = _frame_from_closes_lows_and_offsets([100.0 + i for i in range(80)])

    def asset(slope: float) -> pd.DataFrame:
        closes = [100.0 + (i * slope) for i in range(74)]
        closes += [
            190.0 + slope,
            190.5 + slope,
            191.0 + slope,
            191.5 + slope,
            192.0 + slope,
            193.0 + slope,
        ]
        lows = [value - 1.0 for value in closes]
        lows[-6] = 188.0
        lows[-5] = 188.5
        lows[-4] = 189.0
        lows[-3] = 189.5
        lows[-2] = 190.0
        lows[-1] = 191.0
        return _frame_from_closes_lows_and_offsets(closes, lows=lows)

    snapshot = compute_trend_pullback_reaccel_snapshot(
        btc,
        {
            "KRW-ALPHA": asset(1.8),
            "KRW-BETA": asset(1.6),
            "KRW-GAMMA": asset(1.4),
            "KRW-DELTA": asset(1.2),
        },
    )

    assert snapshot.btc_filter_on is True
    assert snapshot.trend_pass["KRW-ALPHA"] is True
    assert snapshot.pullback_pass["KRW-ALPHA"] is True
    assert snapshot.reaccel_pass["KRW-ALPHA"] is True
    assert {"KRW-ALPHA", "KRW-BETA", "KRW-GAMMA"}.issubset(set(snapshot.candidate_symbols))
    expected_top_symbols = sorted(
        snapshot.candidate_symbols,
        key=lambda symbol: (-snapshot.ranking_score[symbol], symbol),
    )[:3]
    assert snapshot.top_symbols == expected_top_symbols
