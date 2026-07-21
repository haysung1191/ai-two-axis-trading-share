from __future__ import annotations

import pandas as pd

from scripts.candidate_alpha_overlay_attribution import build_overlay_attribution_report


def _build_ohlcv() -> pd.DataFrame:
    idx = pd.date_range("2026-01-01 00:00:00+00:00", periods=8, freq="4h")
    close = pd.Series([100, 101, 95, 96, 110, 111, 112, 113], index=idx, dtype=float)
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


def test_overlay_attribution_counts_blocked_and_reentry_events() -> None:
    ohlcv = _build_ohlcv()
    baseline_signal = pd.Series([0, 1, 1, 1, 1, 1, 0, 0], index=ohlcv.index, dtype=float)
    overlay_signal = pd.Series([0, 0, 0, 1, 1, 1, 0, 0], index=ohlcv.index, dtype=float)
    avoidance = pd.Series([False, True, True, False, False, False, False, False], index=ohlcv.index)

    report = build_overlay_attribution_report(ohlcv, baseline_signal, overlay_signal, avoidance)

    assert report["event_counts"]["entries_blocked_by_overlay"] == 1
    assert report["event_counts"]["additional_reentries_due_to_overlay"] == 1
    assert report["event_counts"]["baseline_trade_count"] == 1
    assert report["event_counts"]["overlay_trade_count"] == 1
    assert report["pnl_attribution"]["baseline_only_segment_count"] >= 1
