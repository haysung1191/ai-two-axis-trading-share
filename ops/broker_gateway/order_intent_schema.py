from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any


REQUIRED_FIELDS = [
    "intent_id",
    "candidate_id",
    "mode",
    "asset_class",
    "venue",
    "account_scope",
    "symbol",
    "side",
    "order_type",
    "quantity",
    "notional_krw",
    "created_at_utc",
    "signal_id",
    "approval_packet_id",
    "gatekeeper_permission",
    "broker_submit_scope",
]

ALLOWED_MODES = {"shadow", "local_sim_paper", "broker_paper", "limited_live"}


def utc_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def stable_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_order_intent(**kwargs: Any) -> dict[str, Any]:
    payload = dict(kwargs)
    payload.setdefault("created_at_utc", utc_now())
    payload.setdefault("order_type", "market")
    payload.setdefault("broker_submit_scope", "disabled")
    payload.setdefault("approval_packet_id", "")
    payload.setdefault("gatekeeper_permission", "")
    if not payload.get("intent_id"):
        identity = {
            "candidate_id": payload.get("candidate_id"),
            "mode": payload.get("mode"),
            "symbol": payload.get("symbol"),
            "side": payload.get("side"),
            "quantity": payload.get("quantity"),
            "notional_krw": payload.get("notional_krw"),
            "signal_id": payload.get("signal_id"),
            "created_at_utc": payload.get("created_at_utc"),
        }
        payload["intent_id"] = stable_hash(identity)
    return payload


def validate_order_intent(intent: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        value = intent.get(field)
        if value is None or value == "":
            errors.append(f"MISSING_FIELD:{field}")
    if intent.get("mode") and intent.get("mode") not in ALLOWED_MODES:
        errors.append(f"INVALID_MODE:{intent.get('mode')}")
    try:
        if float(intent.get("notional_krw") or 0.0) < 0:
            errors.append("NEGATIVE_NOTIONAL")
    except (TypeError, ValueError):
        errors.append("INVALID_NOTIONAL")
    try:
        if float(intent.get("quantity") or 0.0) < 0:
            errors.append("NEGATIVE_QUANTITY")
    except (TypeError, ValueError):
        errors.append("INVALID_QUANTITY")
    return errors
