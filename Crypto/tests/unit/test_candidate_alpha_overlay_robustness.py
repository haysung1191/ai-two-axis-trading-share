from __future__ import annotations

import pandas as pd

from scripts.candidate_alpha_overlay_robustness import build_overlay_robustness_memo


def _build_ohlcv() -> pd.DataFrame:
    idx = pd.date_range("2026-01-01 00:00:00+00:00", periods=12, freq="4h")
    close = pd.Series([100, 101, 102, 103, 104, 105, 100, 99, 98, 97, 96, 95], index=idx, dtype=float)
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


def test_overlay_robustness_memo_produces_chunk_consistency_and_decision() -> None:
    ohlcv = _build_ohlcv()
    baseline_signal = pd.Series([1.0] * len(ohlcv), index=ohlcv.index)
    overlay_signal = pd.Series([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], index=ohlcv.index)

    memo = build_overlay_robustness_memo(ohlcv, baseline_signal, overlay_signal, chunks=3)

    assert memo["coverage"]["chunks"] == 3
    assert set(memo["subperiods"].keys()) == {"chunk_1", "chunk_2", "chunk_3"}
    assert memo["consistency"]["drawdown_improved_chunks"] >= 1
    assert memo["final_decision"] in {"continue", "pause", "stop"}
