from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


KST = ZoneInfo("Asia/Seoul")


def now_utc_ms() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)


def floor_to_interval_ms(ts_ms: int, interval_ms: int) -> int:
    return (ts_ms // interval_ms) * interval_ms


def latest_closed_candle_close_ts_ms(now_ms: int, interval_ms: int) -> int:
    # If it's 12:05, the latest fully closed 1h candle closed at 12:00.
    return floor_to_interval_ms(now_ms, interval_ms)


def run_id_for_close_ts(close_ts_ms: int) -> str:
    return f"1h:{close_ts_ms}"


def kst_day_str_from_utc_ms(ts_ms: int) -> str:
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).astimezone(KST)
    return dt.strftime("%Y-%m-%d")


def iso_utc(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()


@dataclass(frozen=True)
class Candle:
    start_ts_ms: int
    close_ts_ms: int
    o: float
    h: float
    l: float
    c: float
    v: float

