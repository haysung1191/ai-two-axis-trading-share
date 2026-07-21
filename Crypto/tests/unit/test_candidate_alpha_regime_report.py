from __future__ import annotations

import pandas as pd

from scripts.candidate_alpha_regime_report import (
    align_candidate_alpha_inputs,
    build_candidate_alpha_report,
    compute_candidate_alpha_frame,
    fetch_binance_1h,
)


class _MockResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


class _MockClient:
    def __init__(self, payloads):
        self._payloads = payloads
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def get(self, url, params=None):
        self.calls.append({"url": url, "params": params})
        return _MockResponse(self._payloads.pop(0))


def _frame(values: list[float], *, start: str = "2024-01-01T00:00:00Z") -> pd.DataFrame:
    idx = pd.date_range(start, periods=len(values), freq="h", tz="UTC")
    close = pd.Series(values, index=idx, dtype=float)
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


def test_align_candidate_alpha_inputs_uses_common_timestamps() -> None:
    krw_btc = _frame([100.0 + i for i in range(10)])
    krw_usdt = _frame([1400.0 + i for i in range(8)], start="2024-01-01T02:00:00Z")
    global_btc = _frame([70.0 + i for i in range(9)], start="2024-01-01T01:00:00Z")

    aligned = align_candidate_alpha_inputs(krw_btc, krw_usdt, global_btc, max_rows=100)

    assert len(aligned) == 8
    assert aligned.index.min().isoformat() == "2024-01-01T02:00:00+00:00"
    assert list(aligned.columns) == ["krw_btc_close", "krw_btc_volume", "krw_usdt_close", "global_btc_close"]


def test_compute_candidate_alpha_frame_builds_regime_and_forward_metrics() -> None:
    n = 90
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    aligned = pd.DataFrame(
        {
            "krw_btc_close": [100000.0 + i * 50.0 for i in range(n)],
            "krw_btc_volume": [1000.0 + i for i in range(n)],
            "krw_usdt_close": [1400.0 + (i % 3) for i in range(n)],
            "global_btc_close": [71.0 + i * 0.03 for i in range(n)],
        },
        index=idx,
    )

    frame = compute_candidate_alpha_frame(aligned)

    assert "dislocation" in frame.columns
    assert "tradable_regime" in frame.columns
    assert "avoidance_regime" in frame.columns
    assert "forward_return_1h" in frame.columns
    assert "forward_return_4h" in frame.columns
    assert "forward_vol_4h" in frame.columns
    assert frame["tradable_regime"].dtype == bool
    assert frame["avoidance_regime"].dtype == bool
    assert frame["tradable_regime"].iloc[-5:].isin([True, False]).all()


def test_build_candidate_alpha_report_summarizes_regimes() -> None:
    n = 100
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    aligned = pd.DataFrame(
        {
            "krw_btc_close": [100000.0 + i * 25.0 for i in range(n)],
            "krw_btc_volume": [1000.0 + i for i in range(n)],
            "krw_usdt_close": [1400.0 + ((i // 5) % 2) * 2.0 for i in range(n)],
            "global_btc_close": [71.0 + i * 0.02 for i in range(n)],
        },
        index=idx,
    )
    frame = compute_candidate_alpha_frame(aligned)
    report = build_candidate_alpha_report(frame)

    assert report["coverage"]["aligned_rows"] == n
    assert report["coverage"]["valid_rows"] > 0
    assert set(report["regime_comparison"].keys()) == {"tradable", "avoidance"}
    assert "mean_forward_return_4h" in report["regime_comparison"]["tradable"]


def test_fetch_binance_1h_paginates_when_limit_exceeds_single_request(monkeypatch) -> None:
    first = [
        [3600000 * (i + 1), str(1 + i), str(2 + i), str(0.5 + i), str(1.5 + i), str(10 + i)]
        for i in range(1000)
    ]
    second = [
        [0, "0.5", "1.5", "0.25", "1.0", "5"],
    ]
    mock_client = _MockClient([first, second])

    monkeypatch.setattr("scripts.candidate_alpha_regime_report.httpx.Client", lambda timeout=20.0: mock_client)

    frame = fetch_binance_1h("BTCUSDT", limit=1001)

    assert len(frame) == 1001
    assert frame.index.min().isoformat() == "1970-01-01T00:00:00+00:00"
    assert len(mock_client.calls) == 2
    assert "endTime" not in mock_client.calls[0]["params"]
    assert mock_client.calls[1]["params"]["endTime"] == 3600000 - 1
