from __future__ import annotations

import math

import pandas as pd

from app.domains.strategy.krw_volume_surge_breakout import (
    compute_btc_filter_on,
    compute_breakout_pass,
    compute_volume_breakout_snapshot,
    compute_volume_surge_ratio,
)


def _frame_from_closes_and_volume(closes: list[float], volumes: list[float]) -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=len(closes), freq="h", tz="UTC")
    close = pd.Series(closes, index=idx, dtype=float)
    volume = pd.Series(volumes, index=idx, dtype=float)
    frame = pd.DataFrame(index=idx)
    frame["open"] = close
    frame["high"] = close + 1.0
    frame["low"] = close - 1.0
    frame["close"] = close
    frame["volume"] = volume
    return frame


def test_btc_regime_filter_on_and_off() -> None:
    btc_on = _frame_from_closes_and_volume([100.0 + i for i in range(80)], [1000.0] * 80)
    btc_off = _frame_from_closes_and_volume([180.0 - i for i in range(80)], [1000.0] * 80)

    assert compute_btc_filter_on(btc_on) is True
    assert compute_btc_filter_on(btc_off) is False


def test_volume_surge_ratio_uses_current_traded_value_over_prior_24_hour_average() -> None:
    closes = [100.0] * 24 + [110.0]
    volumes = [10.0] * 24 + [60.0]
    asset = _frame_from_closes_and_volume(closes, volumes)

    ratio = compute_volume_surge_ratio(asset)

    expected = (110.0 * 60.0) / (100.0 * 10.0)
    assert math.isclose(ratio, expected, rel_tol=1e-9)


def test_breakout_pass_requires_close_above_prior_20_hour_highest_close() -> None:
    breakout_asset = _frame_from_closes_and_volume([100.0 + i for i in range(20)] + [125.0], [1000.0] * 21)
    no_breakout_asset = _frame_from_closes_and_volume([100.0 + i for i in range(20)] + [119.0], [1000.0] * 21)

    assert compute_breakout_pass(breakout_asset) is True
    assert compute_breakout_pass(no_breakout_asset) is False


def test_volume_breakout_snapshot_selects_top_three_candidates_by_volume_surge_ratio() -> None:
    btc = _frame_from_closes_and_volume([100.0 + i for i in range(80)], [1000.0] * 80)
    base_closes = [100.0 + i for i in range(24)] + [130.0]
    snapshot = compute_volume_breakout_snapshot(
        btc,
        {
            "KRW-ALPHA": _frame_from_closes_and_volume(base_closes, [10.0] * 24 + [80.0]),
            "KRW-BETA": _frame_from_closes_and_volume(base_closes, [10.0] * 24 + [70.0]),
            "KRW-GAMMA": _frame_from_closes_and_volume(base_closes, [10.0] * 24 + [60.0]),
            "KRW-DELTA": _frame_from_closes_and_volume(base_closes, [10.0] * 24 + [50.0]),
            "KRW-EPSILON": _frame_from_closes_and_volume(base_closes, [10.0] * 24 + [20.0]),
        },
    )

    assert snapshot.btc_filter_on is True
    assert snapshot.breakout_pass["KRW-ALPHA"] is True
    assert snapshot.breakout_pass["KRW-BETA"] is True
    assert snapshot.breakout_pass["KRW-GAMMA"] is True
    assert snapshot.breakout_pass["KRW-DELTA"] is True
    assert snapshot.breakout_pass["KRW-EPSILON"] is True
    assert snapshot.candidate_symbols == ["KRW-ALPHA", "KRW-BETA", "KRW-GAMMA", "KRW-DELTA"]
    assert snapshot.top_symbols == ["KRW-ALPHA", "KRW-BETA", "KRW-GAMMA"]
