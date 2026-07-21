from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ops.broker_gateway import BrokerGateway, build_order_intent, evaluate_order_intent


ROOT = Path(r"C:\AI")
REPORT_JSON = ROOT / "reports" / "operations" / "broker_gateway_firewall_report_latest.json"
TINY_LIVE_INTENT_JSON = ROOT / "ops" / "orders" / "intents" / "tiny_live_order_intent_latest.json"
LIMITED_LIVE_POLICY_JSON = ROOT / "ops" / "runstate" / "limited_live_policy.json"
GLOBAL_DISABLE = ROOT / "ops" / "runstate" / "DISABLE_ALL_TRADING"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def base_intent(**overrides: Any) -> dict[str, Any]:
    payload = build_order_intent(
        intent_id="",
        candidate_id="bridge_28_relief",
        mode="broker_paper",
        asset_class="crypto",
        venue="bithumb",
        account_scope="small_account_growth_paper",
        symbol="KRW-BTC",
        side="BUY",
        order_type="market",
        quantity=0,
        notional_krw=10000,
        created_at_utc="2026-05-16T00:00:00Z",
        signal_id="test-signal",
        approval_packet_id="small_account_growth_paper",
        gatekeeper_permission="APPROVED_PAPER_ONLY",
        broker_submit_scope="paper_only",
        producer_lane="operations",
        evidence_source="live_signal",
    )
    payload.update(overrides)
    return payload


def build_report(policy: dict[str, Any]) -> dict[str, Any]:
    intent = base_intent()
    decision = evaluate_order_intent(intent, policy)
    return {
        "schema_version": "1.0.0",
        "intent": intent,
        "decision": {
            "decision": decision.decision,
            "reason": decision.reason,
            "broker_endpoint_allowed": decision.broker_endpoint_allowed,
            "safety_state_hash": decision.safety_state_hash,
        },
    }


def build_current_tiny_live_report() -> dict[str, Any]:
    intent = read_json(TINY_LIVE_INTENT_JSON)
    policy = read_json(LIMITED_LIVE_POLICY_JSON)
    global_disable_present = GLOBAL_DISABLE.exists()
    gateway = BrokerGateway(policy, kill_switch={"live_enabled": True})
    submit_result = gateway.submit_order_intent(intent)
    broker_submit_status = (
        "BLOCKED_BY_GLOBAL_DISABLE"
        if global_disable_present
        else "READY_FOR_MANUAL_BROKER_SUBMIT_CALL"
    )
    return {
        "schema_version": "1.0.0",
        "mode": "current_tiny_live_pre_submit_firewall",
        "source_intent_path": str(TINY_LIVE_INTENT_JSON),
        "source_policy_path": str(LIMITED_LIVE_POLICY_JSON),
        "global_disable_present": global_disable_present,
        "broker_submit_status": broker_submit_status,
        "intent": {
            "intent_id": intent.get("intent_id"),
            "candidate_id": intent.get("candidate_id"),
            "mode": intent.get("mode"),
            "venue": intent.get("venue"),
            "symbol": intent.get("symbol"),
            "side": intent.get("side"),
            "order_type": intent.get("order_type"),
            "notional_krw": intent.get("notional_krw"),
            "approval_packet_id": intent.get("approval_packet_id"),
            "gatekeeper_permission": intent.get("gatekeeper_permission"),
            "broker_submit_scope": intent.get("broker_submit_scope"),
        },
        "policy": {
            "profile": policy.get("profile"),
            "policy_mode": policy.get("policy_mode"),
            "live_enabled": policy.get("live_enabled"),
            "broker_submit_allowed": policy.get("broker_submit_allowed"),
            "broker_submit_scope": policy.get("broker_submit_scope"),
            "real_orders_allowed": policy.get("real_orders_allowed"),
            "max_krw": policy.get("max_krw"),
            "max_order_krw": policy.get("max_order_krw"),
            "max_daily_loss_krw": policy.get("max_daily_loss_krw"),
            "max_total_loss_krw": policy.get("max_total_loss_krw"),
            "approval_text": policy.get("approval_text"),
        },
        "decision": {
            "decision": submit_result["decision"],
            "reason": submit_result["reason"],
            "broker_endpoint_allowed_by_firewall": submit_result["broker_endpoint_allowed"],
            "broker_endpoint_called": False,
            "safety_state_hash": submit_result["safety_state_hash"],
            "approval_packet_id": submit_result["approval_packet_id"],
            "risk_caps_hash": submit_result["risk_caps_hash"],
        },
        "submit_boundary": {
            "automatic_submit_performed": False,
            "real_orders": 0,
            "private_submit_used": False,
            "next_required_action": (
                "Review and remove DISABLE_ALL_TRADING only if the operator intentionally wants to arm the broker submit boundary."
                if global_disable_present
                else "Run the separate broker submit command only after final operator review."
            ),
        },
    }


def main() -> int:
    report = build_current_tiny_live_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": report["decision"]["decision"],
                "reason": report["decision"]["reason"],
                "broker_submit_status": report["broker_submit_status"],
                "latest_json": str(REPORT_JSON),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
