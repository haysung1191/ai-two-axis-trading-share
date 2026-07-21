from __future__ import annotations

import base64
import json

from src.data.bithumb_private_client import BithumbPrivateClient, build_query_hash, build_query_string


def _decode_segment(segment: str) -> dict:
    padded = segment + "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))


def test_build_query_string_and_hash_for_market_param() -> None:
    query = build_query_string({"market": "KRW-BTC"})
    assert query == "market=KRW-BTC"
    assert len(build_query_hash({"market": "KRW-BTC"})) == 128


def test_build_jwt_payload_without_params_omits_query_hash() -> None:
    client = BithumbPrivateClient(access_key="ak", secret_key="sk")
    payload = client.build_jwt_payload(None, nonce="nonce-1", timestamp_ms=123)
    assert payload == {"access_key": "ak", "nonce": "nonce-1", "timestamp": 123}


def test_build_jwt_payload_with_params_includes_query_hash() -> None:
    client = BithumbPrivateClient(access_key="ak", secret_key="sk")
    payload = client.build_jwt_payload({"market": "KRW-BTC"}, nonce="nonce-1", timestamp_ms=123)
    assert payload["access_key"] == "ak"
    assert payload["nonce"] == "nonce-1"
    assert payload["timestamp"] == 123
    assert payload["query_hash_alg"] == "SHA512"
    assert len(payload["query_hash"]) == 128


def test_build_jwt_token_uses_hs256_header() -> None:
    client = BithumbPrivateClient(access_key="ak", secret_key="sk")
    token = client.build_jwt_token({"market": "KRW-BTC"}, nonce="nonce-1", timestamp_ms=123)
    header_segment, payload_segment, signature_segment = token.split(".")
    header = _decode_segment(header_segment)
    payload = _decode_segment(payload_segment)
    assert header == {"alg": "HS256", "typ": "JWT"}
    assert payload["access_key"] == "ak"
    assert payload["nonce"] == "nonce-1"
    assert payload["timestamp"] == 123
    assert payload["query_hash_alg"] == "SHA512"
    assert signature_segment


def test_build_market_buy_request_uses_v2_orders_shape() -> None:
    client = BithumbPrivateClient(access_key="ak", secret_key="sk")
    request = client.build_market_buy_request(
        {
            "market": "KRW-BTC",
            "quote_amount_krw": 250000.0,
        },
        client_order_id="btc-entry-001",
        nonce="nonce-1",
        timestamp_ms=123,
    )
    assert request["method"] == "POST"
    assert request["path"] == "/v2/orders"
    assert request["json_body"] == {
        "market": "KRW-BTC",
        "side": "bid",
        "order_type": "price",
        "price": "250000",
        "client_order_id": "btc-entry-001",
    }
    assert request["headers"]["Authorization"].startswith("Bearer ")


def test_build_market_sell_request_uses_v2_orders_shape() -> None:
    client = BithumbPrivateClient(access_key="ak", secret_key="sk")
    request = client.build_market_sell_request(
        {
            "market": "KRW-BTC",
            "volume": 0.00088869,
        },
        client_order_id="btc-exit-001",
        nonce="nonce-1",
        timestamp_ms=123,
    )
    assert request["method"] == "POST"
    assert request["path"] == "/v2/orders"
    assert request["json_body"] == {
        "market": "KRW-BTC",
        "side": "ask",
        "order_type": "market",
        "volume": "0.00088869",
        "client_order_id": "btc-exit-001",
    }
    assert request["headers"]["Authorization"].startswith("Bearer ")


def test_get_order_uses_uuid_query_param() -> None:
    captured: dict[str, object] = {}

    class FakeClient(BithumbPrivateClient):
        def request(
            self,
            method: str,
            path: str,
            *,
            params: dict[str, object] | None = None,
            json_body: dict[str, object] | None = None,
        ) -> dict[str, object]:
            captured["method"] = method
            captured["path"] = path
            captured["params"] = params
            captured["json_body"] = json_body
            return {"uuid": "order-1"}

    client = FakeClient(access_key="ak", secret_key="sk")
    payload = client.get_order(uuid="order-1")
    assert payload["uuid"] == "order-1"
    assert captured == {
        "method": "GET",
        "path": "/v1/order",
        "params": {"uuid": "order-1"},
        "json_body": None,
    }


def test_get_order_requires_identifier() -> None:
    client = BithumbPrivateClient(access_key="ak", secret_key="sk")
    try:
        client.get_order()
    except ValueError as exc:
        assert "uuid or client_order_id is required" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_cancel_order_uses_delete_v2_order_with_client_order_id() -> None:
    captured: dict[str, object] = {}

    class FakeClient(BithumbPrivateClient):
        def request(
            self,
            method: str,
            path: str,
            *,
            params: dict[str, object] | None = None,
            json_body: dict[str, object] | None = None,
        ) -> dict[str, object]:
            captured["method"] = method
            captured["path"] = path
            captured["params"] = params
            captured["json_body"] = json_body
            return {"client_order_id": "cid-1", "state": "cancel"}

    client = FakeClient(access_key="ak", secret_key="sk")
    payload = client.cancel_order(client_order_id="cid-1")
    assert payload["state"] == "cancel"
    assert captured == {
        "method": "DELETE",
        "path": "/v2/order",
        "params": {"client_order_id": "cid-1"},
        "json_body": None,
    }
