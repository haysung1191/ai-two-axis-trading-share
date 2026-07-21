from __future__ import annotations

import pandas as pd

from app.domains.strategy.krw_low_vol_breakout import (
    compute_btc_filter_on,
    compute_breakout_pass,
    compute_contraction_pass,
    compute_low_vol_breakout_snapshot,
    compute_ranking_score,
    compute_volume_pass,
)


def _frame(
    closes: list[float],
    *,
    lows: list[float] | None = None,
    highs: list[float] | None = None,
    volumes: list[float] | None = None,
) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=len(closes), freq="h", tz="UTC")
    close = pd.Series(closes, index=index, dtype=float)
    low = pd.Series(lows if lows is not None else [value - 1.0 for value in closes], index=index, dtype=float)
    high = pd.Series(highs if highs is not None else [value + 1.0 for value in closes], index=index, dtype=float)
    volume = pd.Series(volumes if volumes is not None else [1000.0] * len(closes), index=index, dtype=float)
    return pd.DataFrame(
        {
            "open": close.shift(1).fillna(close),
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=index,
    )


def test_btc_filter_on_and_off() -> None:
    btc_up = _frame([100.0 + 0.5 * i for i in range(90)])
    btc_down = _frame([150.0 - 0.5 * i for i in range(90)])

    assert compute_btc_filter_on(btc_up, ema_window=72) is True
    assert compute_btc_filter_on(btc_down, ema_window=72) is False


def test_contraction_breakout_and_volume_pass_follow_mvp_rules() -> None:
    closes = [100.0] * 60 + [100.0 + 0.05 * i for i in range(20)] + [102.0] * 20 + [110.0]
    highs = [value + 5.0 for value in closes[:60]] + [value + 1.0 for value in closes[60:]]
    lows = [value - 5.0 for value in closes[:60]] + [value - 1.0 for value in closes[60:]]
    volumes = [100.0] * 100 + [250.0]
    asset = _frame(closes, lows=lows, highs=highs, volumes=volumes)

    assert compute_contraction_pass(asset, atr_window=20, history_window=60) is True
    assert compute_breakout_pass(asset, breakout_window=20) is True
    assert compute_volume_pass(asset, volume_window=20) is True


def test_ranking_score_uses_breakout_width_divided_by_atr_percent() -> None:
    closes = [100.0] * 60 + [100.0 + 0.05 * i for i in range(20)] + [102.0] * 20 + [110.0]
    highs = [value + 5.0 for value in closes[:60]] + [value + 1.0 for value in closes[60:]]
    lows = [value - 5.0 for value in closes[:60]] + [value - 1.0 for value in closes[60:]]
    asset = _frame(closes, lows=lows, highs=highs)

    score = compute_ranking_score(asset, breakout_window=20, atr_window=20)

    prior_highest_close = max(closes[-21:-1])
    breakout_width = closes[-1] - prior_highest_close
    true_ranges = []
    for idx, close in enumerate(closes):
        high = highs[idx]
        low = lows[idx]
        prev_close = closes[idx - 1] if idx > 0 else close
        true_ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    latest_atr = sum(true_ranges[-20:]) / 20.0
    latest_atr_pct = latest_atr / closes[-1]
    expected = breakout_width / latest_atr_pct

    assert score == expected


def test_snapshot_selects_top_three_candidates_by_ranking_score() -> None:
    btc = _frame([100.0 + 0.5 * i for i in range(90)])

    def asset(last_close: float, volume_now: float) -> pd.DataFrame:
        closes = [100.0] * 60 + [100.0 + 0.05 * i for i in range(20)] + [102.0] * 20 + [last_close]
        highs = [value + 5.0 for value in closes[:60]] + [value + 1.0 for value in closes[60:]]
        lows = [value - 5.0 for value in closes[:60]] + [value - 1.0 for value in closes[60:]]
        volumes = [100.0] * 100 + [volume_now]
        return _frame(closes, lows=lows, highs=highs, volumes=volumes)

    snapshot = compute_low_vol_breakout_snapshot(
        btc,
        {
            "KRW-AAA": asset(106.0, 250.0),
            "KRW-BBB": asset(108.0, 260.0),
            "KRW-CCC": asset(111.0, 270.0),
            "KRW-DDD": asset(109.0, 280.0),
        },
        btc_ema_window=72,
        atr_window=20,
        contraction_history_window=60,
        breakout_window=20,
        volume_window=20,
        top_k=3,
    )

    assert snapshot.btc_filter_on is True
    assert snapshot.candidate_symbols == ["KRW-AAA", "KRW-BBB", "KRW-CCC", "KRW-DDD"]
    assert snapshot.top_symbols == ["KRW-CCC", "KRW-DDD", "KRW-BBB"]
