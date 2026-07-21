from pathlib import Path
import types

import pandas as pd

from live_core.kis_screener_universe import (
    filter_krx_listing,
    get_current_stock_universe,
    get_etf_tickers,
    get_historical_market_tickers,
    get_market_tickers_from_latest_results,
    get_market_tickers_from_local_metadata,
    normalize_latest_results_universe,
    resolve_market_tickers,
)


def test_filter_krx_listing_keeps_common_stocks_only() -> None:
    df = pd.DataFrame(
        [
            {"Symbol": "005930", "Name": "삼성전자", "Market": "KOSPI"},
            {"Symbol": "123456", "Name": "테스트주", "Market": "KOSDAQ"},
            {"Symbol": "069500", "Name": "KODEX 200 ETF", "Market": "KOSPI"},
            {"Symbol": "ABCDEF", "Name": "invalid", "Market": "KOSPI"},
        ]
    )

    assert filter_krx_listing(df) == [("005930", "삼성전자"), ("123456", "테스트주")]


def test_normalize_latest_results_universe_sorts_and_zero_fills() -> None:
    df = pd.DataFrame(
        [
            {"Code": "5930", "Name": "삼성전자"},
            {"Code": "000660", "Name": "SK하이닉스"},
            {"Code": "5930", "Name": "삼성전자"},
        ]
    )

    assert normalize_latest_results_universe(df) == [
        ("000660", "SK하이닉스"),
        ("005930", "삼성전자"),
    ]


def test_get_market_tickers_from_latest_results_reads_local_fallback(tmp_path: Path) -> None:
    results_path = tmp_path / "momentum_results_20260416_0930.xlsx"
    results_path.write_text("stub", encoding="utf-8")

    fake_df = pd.DataFrame([{"Code": "5930", "Name": "삼성전자"}])
    fake_config = types.SimpleNamespace(GCS_BUCKET_NAME=None)

    tickers = get_market_tickers_from_latest_results(
        config_module=fake_config,
        repo_root=tmp_path,
        read_excel=lambda path: fake_df,
        print_fn=lambda _: None,
    )

    assert tickers == [("005930", "삼성전자")]


def test_get_market_tickers_from_local_metadata_reads_csv(tmp_path: Path) -> None:
    data_dir = tmp_path / "data" / "kr_metadata"
    data_dir.mkdir(parents=True)
    (data_dir / "kr_symbol_metadata.csv").write_text(
        "Symbol,Name,Market\n005930,삼성전자,KOSPI\n069500,KODEX 200 ETF,KOSPI\n",
        encoding="utf-8",
    )

    tickers = get_market_tickers_from_local_metadata(
        repo_root=tmp_path,
        print_fn=lambda _: None,
    )

    assert tickers == [("005930", "삼성전자")]


def test_resolve_market_tickers_uses_fallback_order() -> None:
    calls: list[str] = []

    tickers = resolve_market_tickers(
        pykrx_loader=lambda: calls.append("pykrx") or [],
        fdr_loader=lambda: calls.append("fdr") or [],
        latest_loader=lambda: calls.append("latest") or [("005930", "삼성전자")],
        print_fn=lambda _: None,
    )

    assert tickers == [("005930", "삼성전자")]
    assert calls == ["pykrx", "fdr", "latest"]


def test_get_current_stock_universe_uses_shared_resolution(monkeypatch, tmp_path: Path) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        "live_core.kis_screener_universe.get_market_tickers_pykrx",
        lambda **kwargs: calls.append("pykrx") or [],
    )
    monkeypatch.setattr(
        "live_core.kis_screener_universe.get_market_tickers_fdr",
        lambda **kwargs: calls.append("fdr") or [],
    )
    monkeypatch.setattr(
        "live_core.kis_screener_universe.get_market_tickers_from_latest_results",
        lambda **kwargs: calls.append("latest") or [("005930", "삼성전자")],
    )
    monkeypatch.setattr(
        "live_core.kis_screener_universe.get_market_tickers_from_local_metadata",
        lambda **kwargs: calls.append("metadata") or [],
    )

    tickers = get_current_stock_universe(
        config_module=types.SimpleNamespace(GCS_BUCKET_NAME=None),
        repo_root=tmp_path,
        print_fn=lambda _: None,
    )

    assert tickers == [("005930", "삼성전자")]
    assert calls == ["pykrx", "fdr", "latest"]


def test_get_historical_market_tickers_uses_fallback_when_empty(monkeypatch) -> None:
    class FakePykrxStock:
        @staticmethod
        def get_market_ticker_list(_date: str, market: str):
            return []

    import sys

    monkeypatch.setitem(sys.modules, "pykrx", types.SimpleNamespace(stock=FakePykrxStock))
    tickers = get_historical_market_tickers(
        "20260101",
        "20260131",
        step_days=30,
        fallback_loader=lambda: [("005930", "삼성전자")],
        print_fn=lambda _: None,
        sleep_sec=0.0,
        name_validator=lambda _: True,
    )

    assert tickers == [("005930", "삼성전자")]


def test_get_etf_tickers_sorts_symbols(monkeypatch) -> None:
    class FakeFdr:
        @staticmethod
        def StockListing(_market: str):
            return pd.DataFrame(
                [
                    {"Symbol": "357870", "Name": "TIGER CD금리"},
                    {"Symbol": "069500", "Name": "KODEX 200"},
                ]
            )

    import sys

    monkeypatch.setitem(sys.modules, "FinanceDataReader", FakeFdr)
    tickers = get_etf_tickers(print_fn=lambda _: None)
    assert tickers == [("069500", "KODEX 200"), ("357870", "TIGER CD금리")]
