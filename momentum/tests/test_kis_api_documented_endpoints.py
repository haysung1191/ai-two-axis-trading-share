from __future__ import annotations

import config
from kis_api import KISApi


def make_api():
    api = object.__new__(KISApi)
    calls = []

    def fake_request(method, path, tr_id, *, params=None, payload=None, need_hashkey=False):
        calls.append(
            {
                "method": method,
                "path": path,
                "tr_id": tr_id,
                "params": params or {},
                "payload": payload,
                "need_hashkey": need_hashkey,
            }
        )
        return {"output": [{"ok": "1"}], "output2": [{"bar": "1"}]}

    api._request = fake_request
    return api, calls


def test_overseas_daily_prices_uses_documented_endpoint() -> None:
    api, calls = make_api()

    out = api.get_overseas_daily_prices("NAS", "AAPL", base_date="20260507")

    assert out == [{"bar": "1"}]
    assert calls[0]["path"] == "/uapi/overseas-price/v1/quotations/dailyprice"
    assert calls[0]["tr_id"] == "HHDFS76240000"
    assert calls[0]["params"]["EXCD"] == "NAS"
    assert calls[0]["params"]["SYMB"] == "AAPL"


def test_overseas_search_uses_documented_endpoint() -> None:
    api, calls = make_api()

    out = api.search_overseas_stocks("NAS", name="AAPL")

    assert out == [{"bar": "1"}]
    assert calls[0]["path"] == "/uapi/overseas-price/v1/quotations/inquire-search"
    assert calls[0]["tr_id"] == "HHDFS76410000"


def test_overseas_product_info_uses_documented_endpoint() -> None:
    api, calls = make_api()

    out = api.get_overseas_product_info("NAS", "AAPL")

    assert out == {"ok": "1"}
    assert calls[0]["path"] == "/uapi/overseas-price/v1/quotations/search-info"
    assert calls[0]["tr_id"] == "CTPF1702R"
    assert calls[0]["params"]["PDNO"] == "AAPL"


def test_domestic_fractional_order_is_disabled_without_verified_endpoint(monkeypatch) -> None:
    api, _ = make_api()
    monkeypatch.setattr(config, "DOMESTIC_FRACTIONAL_ORDER_PATH", "")
    monkeypatch.setattr(config, "DOMESTIC_FRACTIONAL_BUY_TR_ID", "")
    monkeypatch.setattr(config, "DOMESTIC_FRACTIONAL_SELL_TR_ID", "")

    assert api.domestic_fractional_orders_supported is False

    try:
        api.place_domestic_fractional_order("005930", "BUY", notional_krw=25000, quantity=0.25)
    except NotImplementedError as exc:
        assert "not configured" in str(exc)
    else:
        raise AssertionError("expected NotImplementedError")


def test_domestic_fractional_order_uses_configured_endpoint(monkeypatch) -> None:
    api, calls = make_api()
    monkeypatch.setattr(config, "CANO", "12345678")
    monkeypatch.setattr(config, "ACNT_PRDT_CD", "01")
    monkeypatch.setattr(config, "DOMESTIC_FRACTIONAL_ORDER_PATH", "/uapi/domestic-stock/v1/trading/fractional-order")
    monkeypatch.setattr(config, "DOMESTIC_FRACTIONAL_BUY_TR_ID", "TTTCF001U")
    monkeypatch.setattr(config, "DOMESTIC_FRACTIONAL_SELL_TR_ID", "TTTCF002U")
    monkeypatch.setattr(config, "DOMESTIC_FRACTIONAL_ORDER_DVSN", "01")

    out = api.place_domestic_fractional_order("005930", "BUY", notional_krw=25000, quantity=0.25)

    assert out == {"output": [{"ok": "1"}], "output2": [{"bar": "1"}]}
    assert api.domestic_fractional_orders_supported is True
    assert calls[0]["method"] == "POST"
    assert calls[0]["path"] == "/uapi/domestic-stock/v1/trading/fractional-order"
    assert calls[0]["tr_id"] == "TTTCF001U"
    assert calls[0]["need_hashkey"] is True
    assert calls[0]["payload"] == {
        "CANO": "12345678",
        "ACNT_PRDT_CD": "01",
        "PDNO": "005930",
        "ORD_DVSN": "01",
        "ORD_AMT": "25000",
        "ORD_UNPR": "0",
        "ORD_QTY": "0.25",
    }
