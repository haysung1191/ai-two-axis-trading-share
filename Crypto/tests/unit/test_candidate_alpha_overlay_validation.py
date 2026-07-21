from __future__ import annotations

import pandas as pd

from scripts.candidate_alpha_overlay_validation import (
    build_4h_avoidance_overlay,
    build_overlay_signals,
)


def _build_1h_alpha_frame() -> pd.DataFrame:
    idx = pd.date_range("2026-01-01 00:00:00+00:00", periods=12, freq="1h")
    return pd.DataFrame(
        {
            "avoidance_regime": [
                False,
                False,
                False,
                True,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                True,
            ]
        },
        index=idx,
    )


def _build_4h_btc() -> pd.DataFrame:
    idx = pd.date_range("2026-01-01 00:00:00+00:00", periods=3, freq="4h")
    close = pd.Series([100.0, 120.0, 130.0], index=idx)
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


def test_build_4h_avoidance_overlay_uses_last_hour_within_4h_window() -> None:
    alpha_frame = _build_1h_alpha_frame()
    btc_4h = _build_4h_btc()

    overlay = build_4h_avoidance_overlay(alpha_frame, btc_4h)

    assert overlay.tolist() == [True, False, True]


def test_overlay_forces_flat_during_avoidance_regime() -> None:
    alpha_frame = _build_1h_alpha_frame()
    btc_4h = _build_4h_btc()
    avoidance = build_4h_avoidance_overlay(alpha_frame, btc_4h)

    baseline_signal, overlay_signal = build_overlay_signals(btc_4h, avoidance)

    assert baseline_signal.tolist() == [0.0, 0.0, 0.0]
    assert overlay_signal.tolist() == [0.0, 0.0, 0.0]
