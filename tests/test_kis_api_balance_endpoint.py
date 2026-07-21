from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "momentum"))

import kis_api


def test_get_domestic_balance_uses_documented_balance_endpoint(monkeypatch) -> None:
    api = object.__new__(kis_api.KISApi)
    calls: list[dict] = []

    def fake_request(method, path, tr_id, *, params=None, payload=None, need_hashkey=False):
        calls.append({"method": method, "path": path, "tr_id": tr_id, "params": params, "payload": payload, "need_hashkey": need_hashkey})
        return {"rt_cd": "0", "output1": [{"pdno": "005930", "hldg_qty": "1"}]}

    monkeypatch.setattr(kis_api.config, "ENV", "PROD")
    monkeypatch.setattr(api, "_request", fake_request)

    rows = api.get_domestic_balance()

    assert rows == [{"pdno": "005930", "hldg_qty": "1"}]
    assert calls[0]["method"] == "GET"
    assert calls[0]["path"] == "/uapi/domestic-stock/v1/trading/inquire-balance"
    assert calls[0]["tr_id"] == "TTTC8434R"
    assert calls[0]["params"]["INQR_DVSN"] == "02"
