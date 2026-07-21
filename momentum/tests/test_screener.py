import pandas as pd

from live_core import kis_screener as kis_screener_impl
import screener


def test_momentum_screener_run_delegates_to_screening_service(monkeypatch) -> None:
    captured = {}

    class FakeApi:
        pass

    def fake_run_default_screening(**kwargs):
        captured.update(kwargs)
        return pd.DataFrame([{"Code": "005930"}])

    monkeypatch.setattr(kis_screener_impl, "KISApi", FakeApi)
    monkeypatch.setattr(kis_screener_impl, "run_default_screening", fake_run_default_screening)

    runner = screener.MomentumScreener()
    df = runner.run(max_items=123, etf_mode=True)

    assert list(df["Code"]) == ["005930"]
    assert captured["etf_mode"] is True
    assert captured["max_items"] == 123
    assert captured["config_module"] is kis_screener_impl.config
    assert captured["repo_root"] == kis_screener_impl.Path(kis_screener_impl.__file__).resolve().parents[1]
    assert captured["api_factory"]() is runner.api
    assert captured["momentum_calculator"].__self__ is runner
    assert captured["momentum_calculator"].__func__ is runner.calculate_momentum.__func__


def test_momentum_screener_public_helpers_delegate(monkeypatch) -> None:
    captured = {}

    class FakeApi:
        pass

    def fake_market(**kwargs):
        captured["market"] = kwargs
        return [("005930", "삼성전자")]

    def fake_historical(*args, **kwargs):
        captured["historical"] = (args, kwargs)
        return [("000660", "SK하이닉스")]

    monkeypatch.setattr(
        kis_screener_impl,
        "get_current_stock_universe",
        fake_market,
    )
    monkeypatch.setattr(
        kis_screener_impl,
        "get_historical_market_tickers",
        fake_historical,
    )
    monkeypatch.setattr(
        kis_screener_impl,
        "get_etf_tickers",
        lambda: [("069500", "KODEX 200")],
    )
    monkeypatch.setattr(kis_screener_impl, "KISApi", FakeApi)

    runner = screener.MomentumScreener()

    assert runner.get_market_tickers() == [("005930", "삼성전자")]
    assert runner.get_historical_market_tickers("20250101", "20250131") == [("000660", "SK하이닉스")]
    assert runner.get_etf_tickers() == [("069500", "KODEX 200")]
    assert captured["market"]["config_module"] is kis_screener_impl.config
    assert captured["market"]["repo_root"] == kis_screener_impl.Path(kis_screener_impl.__file__).resolve().parents[1]
    assert captured["market"]["name_validator"] is runner._is_valid_name
    assert captured["historical"][0] == ("20250101", "20250131")


def test_root_screener_module_is_compatibility_shim() -> None:
    assert screener.MomentumScreener is kis_screener_impl.MomentumScreener


def test_momentum_screener_run_passes_stock_sort_column(monkeypatch) -> None:
    captured = {}

    class FakeApi:
        pass

    def fake_run_default_screening(**kwargs):
        captured.update(kwargs)
        return pd.DataFrame([{"Code": "005930"}])

    monkeypatch.setattr(kis_screener_impl, "KISApi", FakeApi)
    monkeypatch.setattr(kis_screener_impl, "run_default_screening", fake_run_default_screening)

    runner = screener.MomentumScreener()
    runner.run(max_items=10, etf_mode=False, stock_sort_column="MAD_gap_pct")

    assert captured["stock_sort_column"] == "MAD_gap_pct"
