from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any


def safety_state_hash(*payloads: dict[str, Any]) -> str:
    raw = json.dumps(payloads, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def approval_expired(policy: dict[str, Any], now: datetime | None = None) -> bool:
    expires = parse_utc(policy.get("expires_at_utc"))
    if expires is None:
        return False
    current = now or datetime.now(tz=UTC)
    return expires <= current


def paper_only_policy_allows(policy: dict[str, Any]) -> bool:
    return (
        policy.get("policy_mode") == "paper_only"
        and policy.get("paper_enabled") is True
        and policy.get("broker_submit_allowed") is True
        and policy.get("broker_submit_scope") == "paper_only"
        and policy.get("live_enabled") is False
        and policy.get("private_submit_used") is False
        and policy.get("real_orders_allowed") is False
    )


def limited_live_policy_allows(policy: dict[str, Any]) -> bool:
    try:
        max_krw = float(policy.get("max_krw") or 0)
        max_order_krw = float(policy.get("max_order_krw") or 0)
        max_daily_loss_krw = float(policy.get("max_daily_loss_krw") or 0)
        max_total_loss_krw = float(policy.get("max_total_loss_krw") or 0)
    except (TypeError, ValueError):
        return False
    expected_approval = f"LIVE APPROVE {int(max_krw)} {int(max_daily_loss_krw)} {int(max_total_loss_krw)}"
    return (
        policy.get("policy_mode") == "limited_live"
        and policy.get("live_enabled") is True
        and policy.get("broker_submit_allowed") is True
        and policy.get("broker_submit_scope") == "limited_live"
        and policy.get("private_submit_used") is False
        and policy.get("real_orders_allowed") is True
        and max_krw > 0
        and max_order_krw > 0
        and max_daily_loss_krw > 0
        and max_total_loss_krw > 0
        and str(policy.get("approval_text") or "") == expected_approval
    )
