from __future__ import annotations

import json

import submit_kis_stock_etf_order_intents as submitter


class FakeKisApi:
    def __init__(self, price: float = 10000.0, holdings: list[dict] | None = None) -> None:
        self.price = price
        self.holdings = holdings or []
        self.orders: list[tuple[str, str, int, str]] = []

    def get_domestic_balance(self) -> list[dict]:
        return self.holdings

    def get_domestic_quote(self, symbol: str) -> dict:
        return {"symbol": symbol, "price": self.price}

    def place_domestic_cash_order(self, symbol: str, side: str, quantity: int, *, order_type: str = "market") -> dict:
        self.orders.append((symbol, side, quantity, order_type))
        return {"rt_cd": "0", "output": {"ODNO": "1"}}


class FakeFractionalKisApi(FakeKisApi):
    domestic_fractional_orders_supported = True

    def __init__(self, price: float = 10000.0, holdings: list[dict] | None = None) -> None:
        super().__init__(price=price, holdings=holdings)
        self.fractional_orders: list[dict] = []

    def place_domestic_fractional_order(
        self,
        symbol: str,
        side: str,
        *,
        notional_krw: float,
        quantity: float,
        order_type: str = "market",
    ) -> dict:
        self.fractional_orders.append(
            {
                "symbol": symbol,
                "side": side,
                "notional_krw": notional_krw,
                "quantity": quantity,
                "order_type": order_type,
            }
        )
        return {"rt_cd": "0", "output": {"ODNO": "fractional-1"}}


def patch_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(submitter, "ORDER_INTENT_CSV", tmp_path / "orders.csv")
    monkeypatch.setattr(submitter, "LIMITED_LIVE_POLICY_PATH", tmp_path / "limited.json")
    monkeypatch.setattr(submitter, "BROKER_POLICY_PATH", tmp_path / "broker.json")
    monkeypatch.setattr(submitter, "LEDGER_PATH", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(submitter, "LATEST_PATH", tmp_path / "latest.json")
    monkeypatch.setattr(submitter, "ACCOUNT_ENGINE_LOCK", tmp_path / "axis.lock")
    monkeypatch.setattr(submitter, "ACCOUNT_ENGINE_ROOT", tmp_path)


def write_ready_policy(tmp_path) -> None:
    (tmp_path / "limited.json").write_text(
        json.dumps(
            {
                "live_enabled": True,
                "broker_submit_allowed": True,
                "real_orders_allowed": True,
                "stock_cap_krw": 100000,
                "max_order_krw": 100000,
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "broker.json").write_text(
        json.dumps({"live_enabled": True, "broker_submit_allowed": True, "real_orders_allowed": True}),
        encoding="utf-8",
    )


def test_submit_order_intents_places_one_domestic_order(monkeypatch, tmp_path) -> None:
    patch_paths(monkeypatch, tmp_path)
    write_ready_policy(tmp_path)
    (tmp_path / "orders.csv").write_text(
        "\n".join(
            [
                "CandidateId,Market,AssetType,Symbol,TargetNotionalKRW,CurrentPrice,ExecutionSide,SubmitAllowed",
                "cid,KR,STOCK,005930,25000,10000,BUY,True",
            ]
        ),
        encoding="utf-8",
    )
    api = FakeKisApi(price=10000)

    payload = submitter.submit_order_intents(execute=True, api=api, enforce_market_session=False)

    assert payload["status"] == "KIS_ORDER_SUBMITTED"
    assert payload["submitted_count"] == 1
    assert api.orders == [("005930", "BUY", 2, "market")]
    assert payload["safety"]["effective_cap_krw"] == 100000


def test_submit_order_intents_uses_realized_profit_effective_stock_cap(monkeypatch, tmp_path) -> None:
    patch_paths(monkeypatch, tmp_path)
    write_ready_policy(tmp_path)
    (tmp_path / "ledger.jsonl").write_text(
        json.dumps({"status": "SUBMITTED", "realized_pnl_krw": 10000}) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "orders.csv").write_text(
        "\n".join(
            [
                "CandidateId,Market,AssetType,Symbol,TargetNotionalKRW,CurrentPrice,ExecutionSide,SubmitAllowed",
                "cid,KR,STOCK,005930,120000,10000,BUY,True",
            ]
        ),
        encoding="utf-8",
    )
    api = FakeKisApi(price=10000)

    payload = submitter.submit_order_intents(execute=False, api=api, enforce_market_session=False)

    assert payload["safety"]["base_cap_krw"] == 100000
    assert payload["safety"]["effective_cap_krw"] == 105000
    assert payload["safety"]["cap_ratchet"]["realized_profit_krw"] == 10000


def test_submit_order_intents_skips_existing_success_ledger(monkeypatch, tmp_path) -> None:
    patch_paths(monkeypatch, tmp_path)
    write_ready_policy(tmp_path)
    (tmp_path / "orders.csv").write_text(
        "\n".join(
            [
                "CandidateId,Market,AssetType,Symbol,TargetNotionalKRW,CurrentPrice,ExecutionSide,SubmitAllowed",
                "cid,KR,STOCK,005930,25000,10000,BUY,True",
            ]
        ),
        encoding="utf-8",
    )
    key = submitter.idempotency_key({"CandidateId": "cid", "Market": "KR", "Symbol": "005930", "ExecutionSide": "BUY"})
    (tmp_path / "ledger.jsonl").write_text(json.dumps({"status": "SUBMITTED", "idempotency_key": key}) + "\n", encoding="utf-8")
    api = FakeKisApi(price=10000)

    payload = submitter.submit_order_intents(execute=True, api=api, enforce_market_session=False)

    assert payload["status"] == "KIS_ORDER_NO_SUBMITTABLE_QUANTITY"
    assert api.orders == []


def test_submit_order_intents_buys_only_position_delta(monkeypatch, tmp_path) -> None:
    patch_paths(monkeypatch, tmp_path)
    write_ready_policy(tmp_path)
    (tmp_path / "orders.csv").write_text(
        "\n".join(
            [
                "CandidateId,Market,AssetType,Symbol,TargetNotionalKRW,CurrentPrice,ExecutionSide,SubmitAllowed",
                "cid,KR,STOCK,005930,25000,10000,BUY,True",
            ]
        ),
        encoding="utf-8",
    )
    api = FakeKisApi(price=10000, holdings=[{"pdno": "005930", "hldg_qty": "1", "evlu_amt": "10000"}])

    payload = submitter.submit_order_intents(execute=True, api=api, enforce_market_session=False)

    assert payload["status"] == "KIS_ORDER_SUBMITTED"
    assert payload["submitted_count"] == 1
    assert api.orders == [("005930", "BUY", 1, "market")]
    assert payload["events"][0]["target_quantity"] == 2
    assert payload["events"][0]["current_quantity"] == 1


def test_submit_order_intents_skips_when_target_already_held(monkeypatch, tmp_path) -> None:
    patch_paths(monkeypatch, tmp_path)
    write_ready_policy(tmp_path)
    (tmp_path / "orders.csv").write_text(
        "\n".join(
            [
                "CandidateId,Market,AssetType,Symbol,TargetNotionalKRW,CurrentPrice,ExecutionSide,SubmitAllowed",
                "cid,KR,STOCK,005930,25000,10000,BUY,True",
            ]
        ),
        encoding="utf-8",
    )
    api = FakeKisApi(price=10000, holdings=[{"pdno": "005930", "hldg_qty": "2", "evlu_amt": "20000"}])

    payload = submitter.submit_order_intents(execute=True, api=api, enforce_market_session=False)

    assert payload["status"] == "KIS_ORDER_NO_SUBMITTABLE_QUANTITY"
    assert payload["events"][0]["status"] == "SKIPPED_TARGET_ALREADY_HELD"
    assert api.orders == []


def test_submit_order_intents_uses_fractional_path_when_api_supports_it(monkeypatch, tmp_path) -> None:
    patch_paths(monkeypatch, tmp_path)
    write_ready_policy(tmp_path)
    (tmp_path / "orders.csv").write_text(
        "\n".join(
            [
                "CandidateId,Market,AssetType,Symbol,TargetNotionalKRW,CurrentPrice,ExecutionSide,SubmitAllowed",
                "cid,KR,STOCK,005930,25000,100000,BUY,True",
            ]
        ),
        encoding="utf-8",
    )
    api = FakeFractionalKisApi(price=100000)

    payload = submitter.submit_order_intents(execute=True, api=api, enforce_market_session=False)

    assert payload["status"] == "KIS_ORDER_SUBMITTED"
    assert payload["submitted_count"] == 1
    assert api.orders == []
    assert api.fractional_orders == [
        {
            "symbol": "005930",
            "side": "BUY",
            "notional_krw": 25000.0,
            "quantity": 0.25,
            "order_type": "market",
        }
    ]
    assert payload["events"][0]["quantity_mode"] == "fractional"


def test_submit_order_intents_fractional_path_buys_only_missing_notional(monkeypatch, tmp_path) -> None:
    patch_paths(monkeypatch, tmp_path)
    write_ready_policy(tmp_path)
    (tmp_path / "orders.csv").write_text(
        "\n".join(
            [
                "CandidateId,Market,AssetType,Symbol,TargetNotionalKRW,CurrentPrice,ExecutionSide,SubmitAllowed",
                "cid,KR,STOCK,005930,25000,100000,BUY,True",
            ]
        ),
        encoding="utf-8",
    )
    api = FakeFractionalKisApi(price=100000, holdings=[{"pdno": "005930", "hldg_qty": "0.10", "evlu_amt": "10000"}])

    payload = submitter.submit_order_intents(execute=True, api=api, enforce_market_session=False)

    assert payload["status"] == "KIS_ORDER_SUBMITTED"
    assert api.fractional_orders[0]["quantity"] == 0.15
    assert api.fractional_orders[0]["notional_krw"] == 15000.0
