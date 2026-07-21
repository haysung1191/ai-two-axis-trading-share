from __future__ import annotations

from typing import Any

from .risk_firewall import FirewallDecision, evaluate_order_intent


class BrokerGateway:
    """Firewall-only gateway facade. It never calls broker endpoints."""

    def __init__(self, policy: dict[str, Any], *, kill_switch: dict[str, Any] | None = None) -> None:
        self.policy = policy
        self.kill_switch = kill_switch or {}

    def submit_order_intent(self, intent: dict[str, Any]) -> dict[str, Any]:
        decision: FirewallDecision = evaluate_order_intent(
            intent,
            self.policy,
            kill_switch=self.kill_switch,
        )
        return {
            "intent_id": intent.get("intent_id"),
            "decision": decision.decision,
            "reason": decision.reason,
            "broker_endpoint_allowed": decision.broker_endpoint_allowed,
            "broker_endpoint_called": False,
            "safety_state_hash": decision.safety_state_hash,
            "approval_packet_id": decision.approval_packet_id,
            "risk_caps_hash": decision.risk_caps_hash,
        }
