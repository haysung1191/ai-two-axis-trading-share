from __future__ import annotations

from typing import Any

import pandas as pd

from app.domains.market_data.binance_client import fetch_ohlcv


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeClient:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _ = (args, kwargs)

    def __enter__(self) -> "_FakeClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)

    def get(self, url: str, params: dict[str, Any] | None = None) -> _FakeResponse:
        self.last_url = url
        self.last_params = params
        return _FakeResponse(
            {
                "status": "0000",
                "data": [
                    [1704067200000, "100", "105", "110", "90", "1000"],
                    [1704070800000, "105", "108", "115", "95", "1200"],
                ],
            }
        )


def test_binance_ohlcv_loader_uses_bithumb_krw_path(monkeypatch) -> None:
    fake_client = _FakeClient()
    monkeypatch.setattr("app.domains.market_data.binance_client.httpx.Client", lambda *args, **kwargs: fake_client)

    frame = fetch_ohlcv(
        symbol="KRW-BTC",
        interval="1h",
        start_ts=1704067200000,
        end_ts=1704074400000,
    )

    assert list(frame.columns) == ["open", "high", "low", "close", "volume"]
    assert len(frame) == 2
    assert float(frame.iloc[0]["open"]) == 100.0
    assert float(frame.iloc[1]["close"]) == 108.0
    assert isinstance(frame.index, pd.DatetimeIndex)
    assert fake_client.last_url == "https://api.bithumb.com/public/candlestick/BTC_KRW/1h"


def test_binance_ohlcv_loader_accepts_krw_eth_and_krw_sol_symbols(monkeypatch) -> None:
    urls: list[str] = []

    class _TrackingClient(_FakeClient):
        def get(self, url: str, params: dict[str, Any] | None = None) -> _FakeResponse:
            urls.append(url)
            return super().get(url, params=params)

    monkeypatch.setattr("app.domains.market_data.binance_client.httpx.Client", _TrackingClient)

    fetch_ohlcv(symbol="KRW-ETH", interval="1h", start_ts=1704067200000, end_ts=1704074400000)
    fetch_ohlcv(symbol="KRW-SOL", interval="1h", start_ts=1704067200000, end_ts=1704074400000)

    assert urls == [
        "https://api.bithumb.com/public/candlestick/ETH_KRW/1h",
        "https://api.bithumb.com/public/candlestick/SOL_KRW/1h",
    ]


def test_binance_ohlcv_loader_supports_4h_interval(monkeypatch) -> None:
    fake_client = _FakeClient()
    monkeypatch.setattr("app.domains.market_data.binance_client.httpx.Client", lambda *args, **kwargs: fake_client)

    frame = fetch_ohlcv(
        symbol="KRW-BTC",
        interval="4h",
        start_ts=1704067200000,
        end_ts=1704074400000,
    )

    assert len(frame) == 2
    assert fake_client.last_url == "https://api.bithumb.com/public/candlestick/BTC_KRW/4h"


def test_binance_ohlcv_loader_supports_1d_interval(monkeypatch) -> None:
    class _BinanceClient(_FakeClient):
        def get(self, url: str, params: dict[str, Any] | None = None) -> _FakeResponse:
            self.last_url = url
            self.last_params = params
            return _FakeResponse(
                [
                    [1704067200000, "100", "110", "95", "108", "1000"],
                    [1704153600000, "108", "112", "101", "109", "1500"],
                ]
            )

    fake_client = _BinanceClient()
    monkeypatch.setattr("app.domains.market_data.binance_client.httpx.Client", lambda *args, **kwargs: fake_client)

    frame = fetch_ohlcv(
        symbol="BTCUSDT",
        interval="1d",
        start_ts=1704067200000,
        end_ts=1704240000000,
    )

    assert len(frame) == 2
    assert fake_client.last_url == "https://api.binance.com/api/v3/klines"
    assert fake_client.last_params["interval"] == "1d"


def test_binance_ohlcv_loader_uses_binance_path_for_btcusdt(monkeypatch) -> None:
    class _BinanceClient(_FakeClient):
        def get(self, url: str, params: dict[str, Any] | None = None) -> _FakeResponse:
            self.last_url = url
            self.last_params = params
            return _FakeResponse(
                [
                    [1704067200000, "100", "110", "95", "108", "1000"],
                    [1704081600000, "108", "112", "101", "109", "1500"],
                ]
            )

    fake_client = _BinanceClient()
    monkeypatch.setattr("app.domains.market_data.binance_client.httpx.Client", lambda *args, **kwargs: fake_client)

    frame = fetch_ohlcv(
        symbol="BTCUSDT",
        interval="4h",
        start_ts=1704067200000,
        end_ts=1704096000000,
    )

    assert len(frame) == 2
    assert fake_client.last_url == "https://api.binance.com/api/v3/klines"
    assert fake_client.last_params["symbol"] == "BTCUSDT"
    assert fake_client.last_params["interval"] == "4h"
