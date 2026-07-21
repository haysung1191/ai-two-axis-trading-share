from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .mode_guard import approval_expired, limited_live_policy_allows, paper_only_policy_allows, safety_state_hash
from .order_intent_schema import validate_order_intent


@dataclass(frozen=True)
class FirewallDecision:
    decision: str
    reason: str
    broker_endpoint_allowed: bool
    safety_state_hash: str
    approval_packet_id: str | None = None
    risk_caps_hash: str | None = None

    @property
    def allowed(self) -> bool:
        return self.decision in {"ALLOW_PAPER_ONLY", "ALLOW_LIMITED_LIVE"}


DIRECT_SUBMIT_LANES = {"research", "conversion", "shadow"}
SIMULATION_MODES = {"shadow", "local_sim_paper"}


def _caps_for_asset(policy: dict[str, Any], asset_class: str) -> tuple[str | None, float | None]:
    if asset_class == "crypto":
        return "max_crypto_weight", _float_or_none(policy.get("max_crypto_weight"))
    if asset_class in {"stock", "etf"}:
        return "max_stock_weight", _float_or_none(policy.get("max_stock_weight"))
    return "max_profile_model_weight", _float_or_none(policy.get("max_profile_model_weight"))


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _reject(intent: dict[str, Any], policy: dict[str, Any], reason: str) -> FirewallDecision:
    return FirewallDecision(
        decision="REJECT",
        reason=reason,
        broker_endpoint_allowed=False,
        safety_state_hash=safety_state_hash(intent, policy),
        approval_packet_id=str(intent.get("approval_packet_id") or "") or None,
        risk_caps_hash=safety_state_hash(
            {
                "max_profile_model_weight": policy.get("max_profile_model_weight"),
                "max_crypto_weight": policy.get("max_crypto_weight"),
                "max_stock_weight": policy.get("max_stock_weight"),
            }
        ),
    )


def evaluate_order_intent(
    intent: dict[str, Any],
    policy: dict[str, Any],
    *,
    kill_switch: dict[str, Any] | None = None,
) -> FirewallDecision:
    kill_switch = kill_switch or {}
    schema_errors = validate_order_intent(intent)
    if schema_errors:
        return _reject(intent, policy, ",".join(schema_errors))

    mode = intent["mode"]
    if mode in SIMULATION_MODES:
        return FirewallDecision(
            decision="ACCEPT_SIMULATION_ONLY",
            reason="SIMULATION_MODE_NO_BROKER_ENDPOINT",
            broker_endpoint_allowed=False,
            safety_state_hash=safety_state_hash(intent, policy, kill_switch),
            approval_packet_id=str(intent.get("approval_packet_id") or "") or None,
            risk_caps_hash=safety_state_hash(policy),
        )

    if str(intent.get("evidence_source") or "").lower() == "historical_replay":
        return _reject(intent, policy, "HISTORICAL_REPLAY_REJECTED")
    if intent.get("producer_lane") in DIRECT_SUBMIT_LANES:
        return _reject(intent, policy, f"DIRECT_SUBMIT_FORBIDDEN:{intent.get('producer_lane')}")
    if mode == "limited_live":
        if kill_switch.get("live_enabled") is False:
            return _reject(intent, policy, "KILL_SWITCH_LIVE_DISABLED")
        if not limited_live_policy_allows(policy):
            return _reject(intent, policy, "LIMITED_LIVE_POLICY_NOT_APPROVED")
        if intent.get("broker_submit_scope") != "limited_live":
            return _reject(intent, policy, "BROKER_SCOPE_NOT_LIMITED_LIVE")
        if intent.get("gatekeeper_permission") != "APPROVED_TINY_LIVE":
            return _reject(intent, policy, "MISSING_TINY_LIVE_PERMISSION")
        notional = _float_or_none(intent.get("notional_krw"))
        max_order = _float_or_none(policy.get("max_order_krw"))
        if notional is None or notional <= 0:
            return _reject(intent, policy, "NON_POSITIVE_NOTIONAL")
        if max_order is None or max_order <= 0 or notional > max_order:
            return _reject(intent, policy, "MAX_ORDER_KRW_EXCEEDED")
        return FirewallDecision(
            decision="ALLOW_LIMITED_LIVE",
            reason="APPROVED_TINY_LIVE_UNDER_HARD_CAP",
            broker_endpoint_allowed=True,
            safety_state_hash=safety_state_hash(intent, policy, kill_switch),
            approval_packet_id=str(intent.get("approval_packet_id") or ""),
            risk_caps_hash=safety_state_hash(
                {
                    "max_krw": policy.get("max_krw"),
                    "max_order_krw": policy.get("max_order_krw"),
                    "max_daily_loss_krw": policy.get("max_daily_loss_krw"),
                    "max_total_loss_krw": policy.get("max_total_loss_krw"),
                    "notional_krw": notional,
                }
            ),
        )
    if mode != "broker_paper":
        return _reject(intent, policy, f"UNSUPPORTED_ORDER_MODE:{mode}")
    if kill_switch.get("live_enabled") is True:
        return _reject(intent, policy, "KILL_SWITCH_LIVE_ENABLED")
    if not paper_only_policy_allows(policy):
        return _reject(intent, policy, "PAPER_ONLY_POLICY_NOT_APPROVED")
    if approval_expired(policy):
        return _reject(intent, policy, "PAPER_APPROVAL_EXPIRED")
    if intent.get("account_scope") != policy.get("profile"):
        return _reject(intent, policy, "WRONG_ACCOUNT_SCOPE")
    if intent.get("broker_submit_scope") != "paper_only":
        return _reject(intent, policy, "BROKER_SCOPE_NOT_PAPER_ONLY")
    if intent.get("gatekeeper_permission") != "APPROVED_PAPER_ONLY":
        return _reject(intent, policy, "MISSING_GATEKEEPER_PAPER_PERMISSION")
    if intent.get("approval_packet_id") not in {policy.get("profile"), "small_account_growth_paper"}:
        return _reject(intent, policy, "MISSING_APPROVAL_PACKET")

    asset_class = str(intent.get("asset_class"))
    if asset_class == "crypto" and intent.get("symbol") != "KRW-BTC":
        return _reject(intent, policy, "WRONG_SYMBOL")

    cap_name, cap_value = _caps_for_asset(policy, asset_class)
    if cap_value is None or cap_value <= 0:
        return _reject(intent, policy, f"MISSING_CAP:{cap_name}")

    notional = _float_or_none(intent.get("notional_krw"))
    if notional is None or notional <= 0:
        return _reject(intent, policy, "NON_POSITIVE_NOTIONAL")

    return FirewallDecision(
        decision="ALLOW_PAPER_ONLY",
        reason="APPROVED_SMALL_ACCOUNT_GROWTH_PAPER_ONLY",
        broker_endpoint_allowed=True,
        safety_state_hash=safety_state_hash(intent, policy, kill_switch),
        approval_packet_id=str(intent.get("approval_packet_id") or ""),
        risk_caps_hash=safety_state_hash(
            {
                "cap_name": cap_name,
                "cap_value": cap_value,
                "notional_krw": notional,
                "asset_class": asset_class,
            }
        ),
    )
