from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from scripts import execute_bithumb_execution_plan as execution_script
from scripts.execute_bithumb_execution_plan import (
    _extract_krw_available_from_order_chance,
    _extract_krw_balance_from_accounts,
    _fetch_existing_exchange_order_by_client_order_id,
    _extract_order_identifier,
    _extract_order_state,
    append_execution_log,
    assert_no_exchange_duplicate_submission,
    assert_no_duplicate_submission,
    build_planned_client_order_ids,
    build_execution_log_record,
    build_signed_request_preview,
    load_execution_log,
    submit_execution_plan,
)


def _write_execution_plan(path: Path) -> None:
    payload = {
        "run_id": "1h:test",
        "candle_close_utc": "2026-04-16T12:00:00Z",
        "strategy_track": "operating",
        "intent_count": 1,
        "order_intents": [
            {
                "symbol": "BTC",
                "market": "KRW-BTC",
                "side": "buy",
                "order_type": "market",
                "quote_amount_krw": 250000.0,
            }
        ],
        "standard_check_order_reference": ["practical", "research", "contract", "brief"],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_signed_request_preview_uses_client_order_prefix() -> None:
    preview = build_signed_request_preview(
        {
            "run_id": "1h:test",
            "candle_close_utc": "2026-04-16T12:00:00Z",
            "strategy_track": "attack",
            "order_intents": [
                {
                    "symbol": "BTC",
                    "market": "KRW-BTC",
                    "quote_amount_krw": 250000.0,
                }
            ],
            "standard_check_order_reference": ["practical", "research", "contract", "brief"],
        },
        access_key="ak",
        secret_key="sk",
        client_order_prefix="nightly",
    )
    assert preview["intent_count"] == 1
    signed = preview["signed_requests"][0]
    assert signed["client_order_id"] == "nightly-btc-01"
    assert signed["request"]["path"] == "/v2/orders"
    assert signed["request"]["json_body"]["client_order_id"] == "nightly-btc-01"


def test_execute_bithumb_execution_plan_script_outputs_json(tmp_path: Path) -> None:
    plan_path = tmp_path / "execution_plan.json"
    _write_execution_plan(plan_path)

    cmd = [
        sys.executable,
        str(Path("scripts/execute_bithumb_execution_plan.py")),
        "--plan-json",
        str(plan_path),
        "--access-key",
        "ak",
        "--secret-key",
        "sk",
        "--client-order-prefix",
        "nightly",
        "--format",
        "json",
    ]
    result = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    assert payload["intent_count"] == 1
    assert payload["signed_requests"][0]["market"] == "KRW-BTC"
    assert payload["signed_requests"][0]["client_order_id"] == "nightly-btc-01"
    assert payload["signed_requests"][0]["request"]["headers"]["Authorization"].startswith("Bearer ")


def test_submit_execution_plan_submits_order_when_guards_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    created_orders: list[dict[str, str]] = []

    class FakeClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

        @staticmethod
        def build_market_buy_order_body(order_intent: dict[str, object], *, client_order_id: str | None = None) -> dict[str, str]:
            return {
                "market": str(order_intent["market"]),
                "side": "bid",
                "order_type": "price",
                "price": "250000",
                "client_order_id": str(client_order_id),
            }

        def create_order(self, order_body: dict[str, str]) -> dict[str, str]:
            created_orders.append(order_body)
            return {"status": "0000", "order_id": "order-1"}

        @staticmethod
        def get_order_chance(market: str) -> dict[str, object]:
            return {"bid_account": {"currency": "KRW", "balance": "300000"}}

        @staticmethod
        def get_order(*, uuid: str | None = None, client_order_id: str | None = None) -> dict[str, str | None]:
            if uuid is None and client_order_id == "live-btc-01":
                request = httpx.Request("GET", "https://api.bithumb.com/v1/order")
                response = httpx.Response(404, request=request)
                raise httpx.HTTPStatusError("not found", request=request, response=response)
            return {
                "uuid": uuid,
                "client_order_id": client_order_id,
                "state": "done",
            }

    monkeypatch.setattr(execution_script, "BithumbPrivateClient", FakeClient)

    payload = submit_execution_plan(
        {
            "run_id": "1h:test",
            "candle_close_utc": "2026-04-16T12:00:00Z",
            "strategy_track": "operating",
            "order_intents": [
                {
                    "symbol": "BTC",
                    "market": "KRW-BTC",
                    "quote_amount_krw": 250000.0,
                }
            ],
            "standard_check_order_reference": ["practical", "research", "contract", "brief"],
        },
        access_key="ak",
        secret_key="sk",
        client_order_prefix="live",
        allowed_markets=["KRW-BTC"],
        max_total_quote_krw=300000.0,
    )

    assert payload["submitted_count"] == 1
    assert payload["total_quote_krw"] == 250000.0
    assert payload["funding_checks"][0]["balance_source"] == "order_chance"
    assert created_orders[0]["client_order_id"] == "live-btc-01"
    assert payload["submitted_orders"][0]["order_status"]["order"]["state"] == "done"
    assert payload["submitted_orders"][0]["order_status"]["lookup_uuid"] == "order-1"


def test_submit_execution_plan_rejects_market_outside_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

    monkeypatch.setattr(execution_script, "BithumbPrivateClient", FakeClient)

    with pytest.raises(RuntimeError, match="allowed_markets"):
        submit_execution_plan(
            {
                "order_intents": [
                    {
                        "symbol": "ETH",
                        "market": "KRW-ETH",
                        "quote_amount_krw": 100000.0,
                    }
                ]
            },
            access_key="ak",
            secret_key="sk",
            allowed_markets=["KRW-BTC"],
            max_total_quote_krw=200000.0,
        )


def test_submit_execution_plan_blocks_exchange_side_duplicate_before_order_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

        @staticmethod
        def get_order(*, uuid: str | None = None, client_order_id: str | None = None) -> dict[str, str]:
            return {"client_order_id": str(client_order_id), "state": "wait"}

    monkeypatch.setattr(execution_script, "BithumbPrivateClient", FakeClient)

    with pytest.raises(RuntimeError, match="exchange duplicate submission blocked"):
        submit_execution_plan(
            {
                "order_intents": [
                    {
                        "symbol": "BTC",
                        "market": "KRW-BTC",
                        "quote_amount_krw": 250000.0,
                    }
                ]
            },
            access_key="ak",
            secret_key="sk",
            client_order_prefix="live",
            allowed_markets=["KRW-BTC"],
            max_total_quote_krw=300000.0,
        )


def test_submit_execution_plan_rejects_quote_cap_before_submitting(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

    monkeypatch.setattr(execution_script, "BithumbPrivateClient", FakeClient)

    with pytest.raises(RuntimeError, match="exceeds max_total_quote_krw"):
        submit_execution_plan(
            {
                "order_intents": [
                    {
                        "symbol": "BTC",
                        "market": "KRW-BTC",
                        "quote_amount_krw": 250000.0,
                    }
                ]
            },
            access_key="ak",
            secret_key="sk",
            allowed_markets=["KRW-BTC"],
            max_total_quote_krw=200000.0,
        )


def test_submit_execution_plan_requires_live_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

    monkeypatch.setattr(execution_script, "BithumbPrivateClient", FakeClient)

    with pytest.raises(RuntimeError, match="allowed_markets is required"):
        submit_execution_plan(
            {
                "order_intents": [
                    {
                        "symbol": "BTC",
                        "market": "KRW-BTC",
                        "quote_amount_krw": 250000.0,
                    }
                ]
            },
            access_key="ak",
            secret_key="sk",
            max_total_quote_krw=300000.0,
        )

    with pytest.raises(RuntimeError, match="max_total_quote_krw is required"):
        submit_execution_plan(
            {
                "order_intents": [
                    {
                        "symbol": "BTC",
                        "market": "KRW-BTC",
                        "quote_amount_krw": 250000.0,
                    }
                ]
            },
            access_key="ak",
            secret_key="sk",
            allowed_markets=["KRW-BTC"],
        )


def test_extract_krw_available_from_order_chance_prefers_bid_account_balance() -> None:
    assert (
        _extract_krw_available_from_order_chance(
            {
                "bid_account": {
                    "currency": "KRW",
                    "balance": "123456.78",
                }
            }
        )
        == 123456.78
    )


def test_extract_krw_balance_from_accounts_supports_wrapped_payloads() -> None:
    assert (
        _extract_krw_balance_from_accounts(
            {
                "data": [
                    {"currency": "BTC", "balance": "0.1"},
                    {"currency": "KRW", "balance": "987654.0"},
                ]
            }
        )
        == 987654.0
    )


def test_submit_execution_plan_falls_back_to_accounts_when_order_chance_omits_balance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

        @staticmethod
        def get_order_chance(market: str) -> dict[str, object]:
            return {"market": {"id": market}}

        @staticmethod
        def get_accounts() -> dict[str, object]:
            return {"data": [{"currency": "KRW", "balance": "500000"}]}

        @staticmethod
        def build_market_buy_order_body(order_intent: dict[str, object], *, client_order_id: str | None = None) -> dict[str, str]:
            return {
                "market": str(order_intent["market"]),
                "side": "bid",
                "order_type": "price",
                "price": "250000",
                "client_order_id": str(client_order_id),
            }

        @staticmethod
        def create_order(order_body: dict[str, str]) -> dict[str, str]:
            return {"status": "0000", "order_id": "order-2"}

        @staticmethod
        def get_order(*, uuid: str | None = None, client_order_id: str | None = None) -> dict[str, str | None]:
            if uuid is None and client_order_id == "codex-btc-01":
                request = httpx.Request("GET", "https://api.bithumb.com/v1/order")
                response = httpx.Response(404, request=request)
                raise httpx.HTTPStatusError("not found", request=request, response=response)
            return {"uuid": uuid, "client_order_id": client_order_id, "state": "wait"}

    monkeypatch.setattr(execution_script, "BithumbPrivateClient", FakeClient)

    payload = submit_execution_plan(
        {
            "order_intents": [
                {
                    "symbol": "BTC",
                    "market": "KRW-BTC",
                    "quote_amount_krw": 250000.0,
                }
            ]
        },
        access_key="ak",
        secret_key="sk",
        allowed_markets=["KRW-BTC"],
        max_total_quote_krw=300000.0,
    )

    assert payload["funding_checks"][0]["balance_source"] == "accounts"
    assert payload["submitted_orders"][0]["order_status"]["order"]["state"] == "wait"


def test_submit_execution_plan_rejects_when_available_balance_is_insufficient(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

        @staticmethod
        def get_order_chance(market: str) -> dict[str, object]:
            return {"bid_account": {"currency": "KRW", "balance": "100000"}}

    monkeypatch.setattr(execution_script, "BithumbPrivateClient", FakeClient)

    with pytest.raises(RuntimeError, match="insufficient KRW balance"):
        submit_execution_plan(
            {
                "order_intents": [
                    {
                        "symbol": "BTC",
                        "market": "KRW-BTC",
                        "quote_amount_krw": 250000.0,
                    }
                ]
            },
            access_key="ak",
            secret_key="sk",
            allowed_markets=["KRW-BTC"],
            max_total_quote_krw=300000.0,
        )


def test_extract_order_identifier_supports_multiple_response_shapes() -> None:
    assert _extract_order_identifier({"uuid": "order-1", "client_order_id": "cid-1"}) == {
        "uuid": "order-1",
        "client_order_id": "cid-1",
    }
    assert _extract_order_identifier({"order_id": "order-2", "identifier": "cid-2"}) == {
        "uuid": "order-2",
        "client_order_id": "cid-2",
    }


def test_extract_order_state_reads_nested_state() -> None:
    assert _extract_order_state({"order": {"state": "DONE"}}) == "done"


def test_append_execution_log_writes_jsonl_record(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "execution.jsonl"
    append_execution_log(log_path, {"run_id": "1h:test", "mode": "submit"})
    rows = log_path.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    assert json.loads(rows[0]) == {"run_id": "1h:test", "mode": "submit"}


def test_load_execution_log_reads_multiple_records(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "execution.jsonl"
    append_execution_log(log_path, {"run_id": "1h:test-1", "mode": "preview"})
    append_execution_log(log_path, {"run_id": "1h:test-2", "mode": "submit"})
    rows = load_execution_log(log_path)
    assert [row["run_id"] for row in rows] == ["1h:test-1", "1h:test-2"]


def test_build_execution_log_record_includes_execution_summary() -> None:
    payload = build_execution_log_record(
        {
            "run_id": "1h:test",
            "candle_close_utc": "2026-04-19T00:00:00Z",
            "strategy_track": "operating",
            "intent_count": 1,
            "submitted_count": 1,
            "total_quote_krw": 250000.0,
            "submitted_orders": [{"market": "KRW-BTC"}],
            "funding_checks": [{"market": "KRW-BTC"}],
            "standard_check_order_reference": ["practical", "research", "contract", "brief"],
        },
        plan_path="C:\\AI\\Crypto\\logs\\execution_plan.json",
        mode="submit",
    )
    assert payload["mode"] == "submit"
    assert payload["plan_path"] == "C:\\AI\\Crypto\\logs\\execution_plan.json"
    assert payload["submitted_orders"][0]["market"] == "KRW-BTC"
    assert payload["logged_at_utc"].endswith("Z")


def test_build_planned_client_order_ids_matches_submission_convention() -> None:
    assert build_planned_client_order_ids(
        {
            "order_intents": [
                {"symbol": "BTC"},
                {"symbol": "ETH"},
            ]
        },
        client_order_prefix="live",
    ) == ["live-btc-01", "live-eth-02"]


def test_fetch_existing_exchange_order_by_client_order_id_returns_none_on_404() -> None:
    class FakeClient:
        @staticmethod
        def get_order(*, client_order_id: str | None = None, uuid: str | None = None) -> dict[str, str]:
            request = httpx.Request("GET", "https://api.bithumb.com/v1/order")
            response = httpx.Response(404, request=request)
            raise httpx.HTTPStatusError("not found", request=request, response=response)

    assert _fetch_existing_exchange_order_by_client_order_id(FakeClient(), client_order_id="live-btc-01") is None


def test_assert_no_exchange_duplicate_submission_blocks_active_exchange_order() -> None:
    class FakeClient:
        @staticmethod
        def get_order(*, client_order_id: str | None = None, uuid: str | None = None) -> dict[str, str]:
            return {"client_order_id": str(client_order_id), "state": "wait"}

    with pytest.raises(RuntimeError, match="exchange duplicate submission blocked"):
        assert_no_exchange_duplicate_submission(
            {"order_intents": [{"symbol": "BTC"}]},
            client=FakeClient(),
            client_order_prefix="live",
        )


def test_assert_no_exchange_duplicate_submission_ignores_missing_or_terminal_orders() -> None:
    class FakeClient:
        @staticmethod
        def get_order(*, client_order_id: str | None = None, uuid: str | None = None) -> dict[str, str]:
            if client_order_id == "live-btc-01":
                return {"client_order_id": "live-btc-01", "state": "done"}
            request = httpx.Request("GET", "https://api.bithumb.com/v1/order")
            response = httpx.Response(404, request=request)
            raise httpx.HTTPStatusError("not found", request=request, response=response)

    assert_no_exchange_duplicate_submission(
        {"order_intents": [{"symbol": "BTC"}, {"symbol": "ETH"}]},
        client=FakeClient(),
        client_order_prefix="live",
    )


def test_assert_no_duplicate_submission_blocks_same_run_id(tmp_path: Path) -> None:
    log_path = tmp_path / "bithumb_live_execution_log.jsonl"
    append_execution_log(
        log_path,
        {
            "mode": "submit",
            "run_id": "1h:test",
            "submitted_orders": [{"client_order_id": "live-btc-01"}],
        },
    )
    with pytest.raises(RuntimeError, match="run_id=1h:test"):
        assert_no_duplicate_submission(
            {"run_id": "1h:test", "order_intents": [{"symbol": "BTC"}]},
            client_order_prefix="live",
            execution_log_path=log_path,
        )


def test_assert_no_duplicate_submission_blocks_same_client_order_id(tmp_path: Path) -> None:
    log_path = tmp_path / "bithumb_live_execution_log.jsonl"
    append_execution_log(
        log_path,
        {
            "mode": "submit",
            "run_id": "1h:older",
            "submitted_orders": [{"client_order_id": "live-btc-01"}],
        },
    )
    with pytest.raises(RuntimeError, match="client_order_id=live-btc-01"):
        assert_no_duplicate_submission(
            {"run_id": "1h:newer", "order_intents": [{"symbol": "BTC"}]},
            client_order_prefix="live",
            execution_log_path=log_path,
        )


def test_submit_execution_plan_uses_generated_client_order_id_for_status_lookup_when_uuid_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        submitted = False

        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

        @staticmethod
        def get_order_chance(market: str) -> dict[str, object]:
            return {"bid_account": {"currency": "KRW", "balance": "300000"}}

        @staticmethod
        def build_market_buy_order_body(order_intent: dict[str, object], *, client_order_id: str | None = None) -> dict[str, str]:
            return {
                "market": str(order_intent["market"]),
                "side": "bid",
                "order_type": "price",
                "price": "250000",
                "client_order_id": str(client_order_id),
            }

        @staticmethod
        def create_order(order_body: dict[str, str]) -> dict[str, str]:
            FakeClient.submitted = True
            return {"status": "0000"}

        @staticmethod
        def get_order(*, uuid: str | None = None, client_order_id: str | None = None) -> dict[str, str | None]:
            if uuid is None and client_order_id == "codex-btc-01" and not FakeClient.submitted:
                request = httpx.Request("GET", "https://api.bithumb.com/v1/order")
                response = httpx.Response(404, request=request)
                raise httpx.HTTPStatusError("not found", request=request, response=response)
            return {"uuid": uuid, "client_order_id": client_order_id, "state": "wait"}

    monkeypatch.setattr(execution_script, "BithumbPrivateClient", FakeClient)

    payload = submit_execution_plan(
        {
            "order_intents": [
                {
                    "symbol": "BTC",
                    "market": "KRW-BTC",
                    "quote_amount_krw": 250000.0,
                }
            ]
        },
        access_key="ak",
        secret_key="sk",
        allowed_markets=["KRW-BTC"],
        max_total_quote_krw=300000.0,
    )

    assert payload["submitted_orders"][0]["order_status"]["lookup_uuid"] is None
    assert payload["submitted_orders"][0]["order_status"]["lookup_client_order_id"] == "codex-btc-01"
    assert payload["submitted_orders"][0]["order_status"]["order"]["state"] == "wait"


def test_submit_execution_plan_polls_until_terminal_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order_states = iter(
        [
            {"uuid": "order-3", "client_order_id": "cid-3", "state": "wait"},
            {"uuid": "order-3", "client_order_id": "cid-3", "state": "done"},
        ]
    )

    class FakeClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

        @staticmethod
        def get_order_chance(market: str) -> dict[str, object]:
            return {"bid_account": {"currency": "KRW", "balance": "300000"}}

        @staticmethod
        def build_market_buy_order_body(order_intent: dict[str, object], *, client_order_id: str | None = None) -> dict[str, str]:
            return {
                "market": str(order_intent["market"]),
                "side": "bid",
                "order_type": "price",
                "price": "250000",
                "client_order_id": str(client_order_id),
            }

        @staticmethod
        def create_order(order_body: dict[str, str]) -> dict[str, str]:
            return {"order_id": "order-3", "client_order_id": "cid-3", "state": "wait"}

        @staticmethod
        def get_order(*, uuid: str | None = None, client_order_id: str | None = None) -> dict[str, str]:
            if uuid is None and client_order_id == "codex-btc-01":
                request = httpx.Request("GET", "https://api.bithumb.com/v1/order")
                response = httpx.Response(404, request=request)
                raise httpx.HTTPStatusError("not found", request=request, response=response)
            return next(order_states)

    monotonic_values = iter([0.0, 0.1, 0.2])
    monkeypatch.setattr(execution_script, "BithumbPrivateClient", FakeClient)
    monkeypatch.setattr(execution_script.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(execution_script.time, "sleep", lambda _: None)

    payload = submit_execution_plan(
        {
            "order_intents": [
                {"symbol": "BTC", "market": "KRW-BTC", "quote_amount_krw": 250000.0}
            ]
        },
        access_key="ak",
        secret_key="sk",
        allowed_markets=["KRW-BTC"],
        max_total_quote_krw=300000.0,
        status_poll_seconds=0.01,
        status_timeout_seconds=1.0,
    )

    assert payload["submitted_orders"][0]["timed_out"] is False
    assert payload["submitted_orders"][0]["order_status"]["order"]["state"] == "done"
    assert len(payload["submitted_orders"][0]["status_history"]) == 2


def test_submit_execution_plan_cancels_when_timeout_expires(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_order_calls: list[tuple[str | None, str | None]] = []

    class FakeClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

        @staticmethod
        def get_order_chance(market: str) -> dict[str, object]:
            return {"bid_account": {"currency": "KRW", "balance": "300000"}}

        @staticmethod
        def build_market_buy_order_body(order_intent: dict[str, object], *, client_order_id: str | None = None) -> dict[str, str]:
            return {
                "market": str(order_intent["market"]),
                "side": "bid",
                "order_type": "price",
                "price": "250000",
                "client_order_id": str(client_order_id),
            }

        @staticmethod
        def create_order(order_body: dict[str, str]) -> dict[str, str]:
            return {"order_id": "order-4", "client_order_id": "cid-4", "state": "wait"}

        @staticmethod
        def get_order(*, uuid: str | None = None, client_order_id: str | None = None) -> dict[str, str]:
            if uuid is None and client_order_id == "codex-btc-01":
                request = httpx.Request("GET", "https://api.bithumb.com/v1/order")
                response = httpx.Response(404, request=request)
                raise httpx.HTTPStatusError("not found", request=request, response=response)
            get_order_calls.append((uuid, client_order_id))
            return {"uuid": "order-4", "client_order_id": "cid-4", "state": "wait"}

        @staticmethod
        def cancel_order(*, order_id: str | None = None, client_order_id: str | None = None) -> dict[str, str | None]:
            return {"order_id": order_id, "client_order_id": client_order_id, "state": "cancel"}

    monotonic_values = iter([0.0, 0.2, 1.1])
    monkeypatch.setattr(execution_script, "BithumbPrivateClient", FakeClient)
    monkeypatch.setattr(execution_script.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(execution_script.time, "sleep", lambda _: None)

    payload = submit_execution_plan(
        {
            "order_intents": [
                {"symbol": "BTC", "market": "KRW-BTC", "quote_amount_krw": 250000.0}
            ]
        },
        access_key="ak",
        secret_key="sk",
        allowed_markets=["KRW-BTC"],
        max_total_quote_krw=300000.0,
        status_poll_seconds=0.01,
        status_timeout_seconds=1.0,
        cancel_on_timeout=True,
    )

    order_row = payload["submitted_orders"][0]
    assert order_row["timed_out"] is True
    assert order_row["cancel_response"]["state"] == "cancel"
    assert order_row["order_status"]["order"]["state"] == "cancel"


def test_execute_bithumb_execution_plan_script_appends_execution_log(tmp_path: Path) -> None:
    plan_path = tmp_path / "execution_plan.json"
    log_path = tmp_path / "bithumb_live_execution_log.jsonl"
    _write_execution_plan(plan_path)

    cmd = [
        sys.executable,
        str(Path("scripts/execute_bithumb_execution_plan.py")),
        "--plan-json",
        str(plan_path),
        "--access-key",
        "ak",
        "--secret-key",
        "sk",
        "--client-order-prefix",
        "nightly",
        "--format",
        "json",
        "--execution-log",
        str(log_path),
    ]
    subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=True)
    rows = log_path.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    payload = json.loads(rows[0])
    assert payload["mode"] == "preview"
    assert payload["plan_path"] == str(plan_path.resolve())
    assert payload["intent_count"] == 1


def test_execute_bithumb_execution_plan_script_blocks_duplicate_submit_from_log(tmp_path: Path) -> None:
    plan_path = tmp_path / "execution_plan.json"
    log_path = tmp_path / "bithumb_live_execution_log.jsonl"
    _write_execution_plan(plan_path)
    append_execution_log(
        log_path,
        {
            "mode": "submit",
            "run_id": "1h:test",
            "submitted_orders": [{"client_order_id": "nightly-btc-01"}],
        },
    )

    cmd = [
        sys.executable,
        str(Path("scripts/execute_bithumb_execution_plan.py")),
        "--plan-json",
        str(plan_path),
        "--access-key",
        "ak",
        "--secret-key",
        "sk",
        "--client-order-prefix",
        "nightly",
        "--submit",
        "--allowed-market",
        "KRW-BTC",
        "--max-total-quote-krw",
        "300000",
        "--execution-log",
        str(log_path),
        "--format",
        "json",
    ]
    result = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True)
    assert result.returncode != 0
    assert "duplicate live submission blocked" in result.stderr
