from __future__ import annotations

import pandas as pd

from scripts.candidate_alpha_overlay_friction_report import build_overlay_friction_report


def _build_ohlcv() -> pd.DataFrame:
    idx = pd.date_range("2026-01-01 00:00:00+00:00", periods=12, freq="4h")
    close = pd.Series([100, 101, 102, 103, 104, 103, 102, 101, 100, 99, 98, 97], index=idx, dtype=float)
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


def test_friction_report_emits_multiple_cost_levels_and_decision() -> None:
    ohlcv = _build_ohlcv()
    baseline_signal = pd.Series([0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0], index=ohlcv.index, dtype=float)
    overlay_signal = pd.Series([0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0], index=ohlcv.index, dtype=float)

    report = build_overlay_friction_report(ohlcv, baseline_signal, overlay_signal, cost_levels_bps=[0.0, 5.0, 10.0])

    assert report["cost_levels_bps"] == [0.0, 5.0, 10.0]
    assert set(report["levels"].keys()) == {"0bps", "5bps", "10bps"}
    assert report["final_decision"] in {"continue", "continue with caution", "pause"}
