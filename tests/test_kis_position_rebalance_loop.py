from __future__ import annotations

import json

import run_kis_position_rebalance_loop as rebalance


class FakeKisApi:
    def __init__(self) -> None:
        self.orders: list[tuple[str, str, int, str]] = []

    def get_domestic_balance(self) -> list[dict]:
        return [
            {"pdno": "005930", "hldg_qty": "3", "evlu_amt": "210000"},
            {"pdno": "000660", "hldg_qty": "2", "evlu_amt": "300000"},
        ]

    def place_domestic_cash_order(self, symbol: str, side: str, quantity: int, *, order_type: str = "market") -> dict:
        self.orders.append((symbol, side, quantity, order_type))
        return {"rt_cd": "0", "output": {"ODNO": "2"}}


def patch_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(rebalance, "LATEST_JSON", tmp_path / "latest.json")
    monkeypatch.setattr(rebalance, "LATEST_ORDERS_CSV", tmp_path / "orders.csv")
    monkeypatch.setattr(rebalance, "LEDGER_PATH", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(rebalance, "TARGET_BOOK_CSV", tmp_path / "target.csv")
    monkeypatch.setattr(rebalance, "LIMITED_LIVE_POLICY_PATH", tmp_path / "limited.json")
    monkeypatch.setattr(rebalance, "BROKER_POLICY_PATH", tmp_path / "broker.json")
    monkeypatch.setattr(rebalance, "ACCOUNT_ENGINE_LOCK", tmp_path / "axis.lock")
    monkeypatch.setattr(rebalance, "ACCOUNT_ENGINE_ROOT", tmp_path)


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


def test_rebalance_sells_only_managed_symbol_missing_from_target(monkeypatch, tmp_path) -> None:
    patch_paths(monkeypatch, tmp_path)
    write_ready_policy(tmp_path)
    (tmp_path / "ledger.jsonl").write_text(
        json.dumps({"status": "SUBMITTED", "symbol": "005930"}) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "target.csv").write_text("Symbol\n000660\n", encoding="utf-8")
    api = FakeKisApi()

    payload = rebalance.run_once(execute=True, api=api, enforce_market_session=False)

    assert payload["status"] == "KIS_POSITION_REBALANCE_SUBMITTED"
    assert payload["submitted_count"] == 1
    assert api.orders == [("005930", "SELL", 3, "market")]


def test_rebalance_does_not_sell_unmanaged_holdings(monkeypatch, tmp_path) -> None:
    patch_paths(monkeypatch, tmp_path)
    write_ready_policy(tmp_path)
    (tmp_path / "target.csv").write_text("Symbol\n\n", encoding="utf-8")
    api = FakeKisApi()

    payload = rebalance.run_once(execute=True, api=api, enforce_market_session=False)

    assert payload["status"] == "KIS_POSITION_REBALANCE_OK"
    assert payload["submitted_count"] == 0
    assert api.orders == []


def test_rebalance_sells_only_excess_quantity_for_managed_target_symbol(monkeypatch, tmp_path) -> None:
    patch_paths(monkeypatch, tmp_path)
    write_ready_policy(tmp_path)
    (tmp_path / "ledger.jsonl").write_text(
        json.dumps({"status": "SUBMITTED", "symbol": "005930"}) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "target.csv").write_text("Symbol,TargetNotionalKRW,CurrentPrice\n005930,140000,70000\n", encoding="utf-8")
    api = FakeKisApi()

    payload = rebalance.run_once(execute=True, api=api, enforce_market_session=False)

    assert payload["status"] == "KIS_POSITION_REBALANCE_SUBMITTED"
    assert payload["submitted_count"] == 1
    assert payload["orders"][0]["reason"] == "ABOVE_TARGET_QUANTITY"
    assert payload["orders"][0]["quantity"] == 1
    assert api.orders == [("005930", "SELL", 1, "market")]
