from __future__ import annotations

import json
from pathlib import Path

from scripts import run_bithumb_live_exit_check as exit_runner


def _write_live_artifacts(base: Path) -> Path:
    plan_path = base / "plan.json"
    summary_path = base / "summary.json"
    plan_path.write_text(
        json.dumps(
            {
                "run_id": "1h:demo",
                "order_intents": [
                    {
                        "symbol": "BTC",
                        "market": "KRW-BTC",
                        "suggested_stop_price_krw": 145000000.0,
                        "suggested_take_profit_price_krw": 160000000.0,
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps(
            {
                "run_id": "1h:demo",
                "submitted_orders": [
                    {
                        "symbol": "BTC",
                        "market": "KRW-BTC",
                        "client_order_id": "live-btc-01",
                        "response": {"order_id": "entry-order-1"},
                        "order_status": {
                            "order": {
                                "executed_volume": "0.00088869",
                                "trades": [
                                    {
                                        "price": "112300000",
                                        "volume": "0.00088869",
                                    }
                                ],
                            }
                        },
                    }
                ],
                "artifacts": {"plan_json": str(plan_path)},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return summary_path


def test_decide_exit_triggers_take_profit() -> None:
    payload = exit_runner.decide_exit(
        {
            "entry_price_krw": 112300000.0,
            "suggested_stop_price_krw": 145000000.0,
            "suggested_take_profit_price_krw": 160000000.0,
        },
        current_price_krw=161000000.0,
    )
    assert payload["should_exit"] is True
    assert payload["exit_reason"] == "TAKE_PROFIT"


def test_decide_exit_ignores_invalid_stop_above_entry() -> None:
    payload = exit_runner.decide_exit(
        {
            "entry_price_krw": 112300000.0,
            "suggested_stop_price_krw": 145000000.0,
            "suggested_take_profit_price_krw": 160000000.0,
        },
        current_price_krw=112469000.0,
    )
    assert payload["should_exit"] is False
    assert payload["stop_price_krw"] is None
    assert "stop_price" in payload["invalid_thresholds"]


def test_run_live_exit_check_submits_market_sell_on_take_profit(monkeypatch, tmp_path: Path) -> None:
    summary_path = _write_live_artifacts(tmp_path)

    class FakePublicClient:
        def get_current_price_krw(self, symbol: str) -> float:
            assert symbol == "BTC"
            return 161000000.0

    class FakePrivateClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key
            self.created_order = None

        def has_credentials(self) -> bool:
            return True

        @staticmethod
        def get_accounts() -> dict[str, object]:
            return {"data": [{"currency": "BTC", "balance": "0.00088869"}]}

        @staticmethod
        def get_order(*, uuid: str | None = None, client_order_id: str | None = None) -> dict[str, object]:
            if client_order_id == "live-btc-01-exit" and uuid is None:
                raise RuntimeError("not found")
            return {"uuid": uuid, "client_order_id": client_order_id, "state": "done"}

        @staticmethod
        def build_market_sell_order_body(order_intent: dict[str, object], *, client_order_id: str | None = None) -> dict[str, str]:
            return {
                "market": str(order_intent["market"]),
                "side": "ask",
                "order_type": "market",
                "volume": str(order_intent["volume"]),
                "client_order_id": str(client_order_id),
            }

        def create_order(self, order_body: dict[str, str]) -> dict[str, str]:
            self.created_order = order_body
            return {"order_id": "exit-order-1", "client_order_id": order_body["client_order_id"]}

    monkeypatch.setattr(exit_runner, "BithumbPublicClient", FakePublicClient)
    monkeypatch.setattr(exit_runner, "BithumbPrivateClient", FakePrivateClient)

    payload = exit_runner.run_live_exit_check(
        summary_path=summary_path,
        access_key="ak",
        secret_key="sk",
        min_asset_balance=0.000001,
        submit=True,
    )

    assert payload["decision"]["should_exit"] is True
    assert payload["decision"]["exit_reason"] == "TAKE_PROFIT"
    assert payload["submitted"] is True
    assert payload["sell_order"]["order_id"] == "exit-order-1"
    assert payload["sell_order_request"]["client_order_id"] == "live-btc-01-exit"


def test_run_live_exit_check_skips_when_price_is_inside_band(monkeypatch, tmp_path: Path) -> None:
    summary_path = _write_live_artifacts(tmp_path)

    class FakePublicClient:
        def get_current_price_krw(self, symbol: str) -> float:
            assert symbol == "BTC"
            return 150000000.0

    class FakePrivateClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

        @staticmethod
        def get_accounts() -> dict[str, object]:
            return {"data": [{"currency": "BTC", "balance": "0.00088869"}]}

    monkeypatch.setattr(exit_runner, "BithumbPublicClient", FakePublicClient)
    monkeypatch.setattr(exit_runner, "BithumbPrivateClient", FakePrivateClient)

    payload = exit_runner.run_live_exit_check(
        summary_path=summary_path,
        access_key="ak",
        secret_key="sk",
        min_asset_balance=0.000001,
        submit=False,
    )

    assert payload["decision"]["should_exit"] is False
    assert payload["submitted"] is False
    assert payload["sell_order"] is None
