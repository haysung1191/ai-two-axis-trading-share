from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from src.timeutil import Candle

log = logging.getLogger(__name__)

INTERVAL_1H_MS = 3600000


@dataclass(frozen=True)
class Ticker24h:
    symbol: str  # e.g. BTC
    acc_trade_value_24h: float  # KRW


class BithumbPublicClient:
    def __init__(self, timeout_s: float = 10.0) -> None:
        self._client = httpx.Client(timeout=timeout_s)
        self._base = "https://api.bithumb.com"

    def close(self) -> None:
        self._client.close()

    @retry(stop=stop_after_attempt(4), wait=wait_exponential_jitter(initial=0.5, max=4.0))
    def _get_json(self, path: str) -> dict[str, Any]:
        url = f"{self._base}{path}"
        r = self._client.get(url)
        r.raise_for_status()
        j = r.json()
        if str(j.get("status")) != "0000":
            raise RuntimeError(f"bithumb api error: {j.get('status')} {j.get('message')}")
        return j

    def list_krw_tickers_by_quote_volume(self, min_quote_krw_24h: float, max_symbols: int) -> list[Ticker24h]:
        # Public endpoint: /public/ticker/ALL_KRW
        j = self._get_json("/public/ticker/ALL_KRW")
        data = j.get("data") or {}
        out: list[Ticker24h] = []
        for sym, row in data.items():
            if sym == "date":
                continue
            try:
                v = float(row.get("acc_trade_value_24H") or row.get("acc_trade_value_24h") or 0.0)
            except Exception:
                v = 0.0
            if v >= float(min_quote_krw_24h):
                out.append(Ticker24h(symbol=sym, acc_trade_value_24h=v))
        out.sort(key=lambda x: x.acc_trade_value_24h, reverse=True)
        return out[: int(max_symbols)]

    def get_current_price_krw(self, symbol: str) -> float:
        j = self._get_json(f"/public/ticker/{str(symbol).upper()}_KRW")
        data = j.get("data") or {}
        for key in ("closing_price", "trade_price", "last_price"):
            value = data.get(key)
            if value is None:
                continue
            return float(value)
        raise RuntimeError(f"missing current price for {symbol}")

    def fetch_1h_candles(self, symbol: str) -> list[tuple[int, float, float, float, float, float]]:
        # Public endpoint: /public/candlestick/{symbol}_KRW/1h
        # Response row order is commonly: [timestamp, open, close, high, low, volume]
        #
        # IMPORTANT (empirical): Bithumb returns the candle timestamp as the candle START time (ms),
        # and includes the in-progress current candle. For a run processing candle_close_ts_ms,
        # the "just-closed" candle is the row whose ts == candle_close_ts_ms - interval_ms.
        j = self._get_json(f"/public/candlestick/{symbol}_KRW/1h")
        rows = j.get("data") or []
        out: list[tuple[int, float, float, float, float, float]] = []
        for r in rows:
            if not isinstance(r, (list, tuple)) or len(r) < 6:
                continue
            ts = int(float(r[0]))
            o = float(r[1])
            c = float(r[2])
            h = float(r[3])
            l = float(r[4])
            v = float(r[5])
            out.append((ts, o, h, l, c, v))
        out.sort(key=lambda x: x[0])
        return out

    @staticmethod
    def pick_closed_candle_for_close_ts(
        rows: list[tuple[int, float, float, float, float, float]],
        close_ts_ms: int,
        interval_ms: int,
    ) -> Candle | None:
        """
        Pick the fully closed candle that ends at close_ts_ms.

        Bithumb's public 1h candlestick endpoint uses candle START timestamps (ms) and typically includes
        the in-progress candle whose start_ts == close_ts_ms. Therefore the closed candle ending at
        close_ts_ms is the row whose ts == close_ts_ms - interval_ms.
        """
        start_ts_ms = close_ts_ms - interval_ms
        for ts, o, h, l, c, v in rows:
            if ts == start_ts_ms:
                return Candle(
                    start_ts_ms=start_ts_ms,
                    close_ts_ms=close_ts_ms,
                    o=o,
                    h=h,
                    l=l,
                    c=c,
                    v=v,
                )
        return None

    @staticmethod
    def pick_candle_for_start_ts(
        rows: list[tuple[int, float, float, float, float, float]],
        start_ts_ms: int,
        interval_ms: int,
    ) -> Candle | None:
        for ts, o, h, l, c, v in rows:
            if ts == start_ts_ms:
                return Candle(
                    start_ts_ms=ts,
                    close_ts_ms=ts + interval_ms,
                    o=o,
                    h=h,
                    l=l,
                    c=c,
                    v=v,
                )
        return None

    @staticmethod
    def diagnose_1h_semantics(
        rows_a: list[tuple[int, float, float, float, float, float]],
        rows_b: list[tuple[int, float, float, float, float, float]],
    ) -> dict[str, Any]:
        """
        Best-effort diagnostic: if the last row changes across two fetches, the endpoint includes an
        in-progress candle and timestamps are candle-start semantics.
        """
        if not rows_a:
            return {"ok": False, "reason": "no_rows"}
        last_a = rows_a[-1]
        last_b = rows_b[-1] if rows_b else None
        return {
            "ok": True,
            "last_ts_ms": int(last_a[0]),
            "last_changed": bool(last_b is not None and last_b != last_a),
        }
