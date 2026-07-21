from __future__ import annotations

import pandas as pd
from argparse import Namespace

from tools.data_ingestion.full_market_history_backfill import (
    existing_bar_count,
    explicit_symbol_rows,
    apply_window,
    download_us_one_yahoo_chart,
    download_us_one,
    filter_symbols,
    is_supported_us_security,
    is_supported_us_symbol,
    normalize_price_frame,
    select_rows,
    backfill_us,
)


def test_normalize_price_frame_outputs_contract_columns() -> None:
    raw = pd.DataFrame(
        {
            "Date": ["2020-01-02", "2020-01-03"],
            "Close": [10, 11],
            "Volume": [100, 200],
        }
    ).set_index("Date")

    out = normalize_price_frame(raw)

    assert list(out.columns) == ["date", "close", "volume"]
    assert out["close"].tolist() == [10, 11]


def test_normalize_price_frame_accepts_pykrx_korean_date_index() -> None:
    raw = pd.DataFrame(
        {
            "종가": [55200, 55500],
            "거래량": [12993228, 15422255],
        },
        index=pd.to_datetime(["2020-01-02", "2020-01-03"]),
    )
    raw.index.name = "날짜"

    out = normalize_price_frame(raw.rename(columns={"종가": "close", "거래량": "volume"}))

    assert len(out) == 2
    assert out["close"].tolist() == [55200, 55500]


def test_normalize_price_frame_handles_duplicate_column_names() -> None:
    raw = pd.DataFrame(
        [
            ["2020-01-02", 10, 11, 100],
            ["2020-01-03", 12, 13, 200],
        ],
        columns=["date", "close", "close", "volume"],
    )

    out = normalize_price_frame(raw)

    assert out["close"].tolist() == [10, 12]


def test_select_rows_filters_asset_types_and_allows_smoke_limit() -> None:
    df = pd.DataFrame(
        [
            {"symbol": "AAA", "asset_type": "stock"},
            {"symbol": "BBB", "asset_type": "etf"},
            {"symbol": "CCC", "asset_type": "stock"},
        ]
    )

    out = apply_window(select_rows(df, {"stock"}, 0), 0, 1)

    assert out["symbol"].tolist() == ["AAA"]


def test_apply_window_supports_offset_and_limit() -> None:
    df = pd.DataFrame([{"symbol": "A"}, {"symbol": "B"}, {"symbol": "C"}])

    out = apply_window(df, 1, 1)

    assert out["symbol"].tolist() == ["B"]


def test_filter_symbols_preserves_requested_order() -> None:
    df = pd.DataFrame(
        [
            {"symbol": "MSFT", "asset_type": "stock"},
            {"symbol": "AAPL", "asset_type": "stock"},
            {"symbol": "SPY", "asset_type": "etf"},
        ]
    )

    out = filter_symbols(df, "SPY,AAPL")

    assert out["symbol"].tolist() == ["SPY", "AAPL"]


def test_explicit_symbol_rows_builds_targeted_override_universe() -> None:
    out = explicit_symbol_rows("005930,000660", "stock", "explicit_symbols")

    assert out["symbol"].tolist() == ["005930", "000660"]
    assert out["asset_type"].tolist() == ["stock", "stock"]


def test_us_symbol_filter_skips_preferred_share_style_symbols() -> None:
    assert is_supported_us_symbol("AAPL")
    assert is_supported_us_symbol("BRK.B")
    assert not is_supported_us_symbol("ABR$E")


def test_us_security_filter_skips_units_and_warrants() -> None:
    assert is_supported_us_security(pd.Series({"symbol": "AAPL", "asset_type": "stock", "name": "Apple Inc. Common Stock"}))
    assert not is_supported_us_security(pd.Series({"symbol": "AACIU", "asset_type": "stock", "name": "Armada Acquisition Corp. I Unit"}))
    assert not is_supported_us_security(pd.Series({"symbol": "AACIW", "asset_type": "stock", "name": "Armada Acquisition Corp. I Warrant"}))


def test_existing_bar_count_reads_gzip_price_file(tmp_path) -> None:
    path = tmp_path / "A.csv.gz"
    pd.DataFrame({"date": ["2020-01-02", "2020-01-03"], "close": [1, 2], "volume": [3, 4]}).to_csv(
        path,
        index=False,
        compression="gzip",
    )

    assert existing_bar_count(path) == 2


def test_backfill_us_can_use_local_universe_path_for_universe_only(tmp_path) -> None:
    universe = tmp_path / "universe.csv"
    pd.DataFrame(
        [
            {"symbol": "AAPL", "yahoo_ticker": "AAPL", "name": "Apple Inc. Common Stock", "asset_type": "stock", "source": "test"},
            {"symbol": "SPY", "yahoo_ticker": "SPY", "name": "SPDR ETF", "asset_type": "etf", "source": "test"},
        ]
    ).to_csv(universe, index=False)

    out = backfill_us(
        Namespace(
            universe_path=str(universe),
            offset=0,
            max_items=0,
            symbols="",
            universe_only=True,
            out_base_us=str(tmp_path / "prices"),
            skip_existing_min_bars=0,
            batch_size=5,
            start="2020-01-01",
            end="2020-02-01",
            sleep_sec=0,
        ),
        {"stock"},
    )

    assert out["symbol"].tolist() == ["AAPL"]


def test_download_us_one_yahoo_chart_returns_empty_on_http_error(monkeypatch) -> None:
    class Response:
        status_code = 404

        def json(self):
            return {}

    monkeypatch.setattr("tools.data_ingestion.full_market_history_backfill.requests.get", lambda *args, **kwargs: Response())

    out = download_us_one_yahoo_chart("NOPE", "2020-01-01", "2020-01-31")

    assert out.empty


def test_download_us_one_falls_back_to_yahoo_chart(monkeypatch) -> None:
    def fail_reader(*args, **kwargs):
        raise RuntimeError("fdr fail")

    monkeypatch.setattr("FinanceDataReader.DataReader", fail_reader)
    monkeypatch.setattr(
        "tools.data_ingestion.full_market_history_backfill.download_us_one_yahoo_chart",
        lambda *args, **kwargs: pd.DataFrame({"date": ["2020-01-02"], "close": [1], "volume": [2]}),
    )

    out = download_us_one("AAPL", "2020-01-01", "2020-01-31")

    assert len(out) == 1
