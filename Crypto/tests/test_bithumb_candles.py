from __future__ import annotations

from src.data.bithumb_client import BithumbPublicClient


def test_pick_closed_candle_for_close_ts_ignores_in_progress() -> None:
    interval_ms = 3600000
    close_ts_ms = 10 * interval_ms

    # Bithumb includes the in-progress candle at ts == close_ts_ms (start of current hour).
    rows = [
        (close_ts_ms - interval_ms, 100.0, 110.0, 90.0, 105.0, 123.0),  # closed candle
        (close_ts_ms, 105.0, 120.0, 100.0, 115.0, 10.0),  # in-progress candle (must be ignored)
    ]

    c = BithumbPublicClient.pick_closed_candle_for_close_ts(rows, close_ts_ms, interval_ms)
    assert c is not None
    assert c.start_ts_ms == close_ts_ms - interval_ms
    assert c.close_ts_ms == close_ts_ms
    assert c.o == 100.0
    assert c.h == 110.0
    assert c.l == 90.0
    assert c.c == 105.0
    assert c.v == 123.0

