from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_broker_gateway_firewall_reports.py")
SPEC = importlib.util.spec_from_file_location("build_broker_gateway_firewall_reports", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
reports = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reports)

from ops.broker_gateway import BrokerGateway, evaluate_order_intent  # noqa: E402


def policy() -> dict:
    return {
        "profile": "small_account_growth_paper",
        "policy_mode": "paper_only",
        "paper_enabled": True,
        "broker_submit_allowed": True,
        "broker_submit_scope": "paper_only",
        "live_enabled": False,
        "private_submit_used": False,
        "real_orders_allowed": False,
        "max_profile_model_weight": 0.45,
        "max_crypto_weight": 0.3,
        "max_stock_weight": 0.15,
    }


def live_policy() -> dict:
    return {
        "profile": "small_account_growth_paper",
        "policy_mode": "limited_live",
        "paper_enabled": False,
        "live_enabled": True,
        "broker_submit_allowed": True,
        "broker_submit_scope": "limited_live",
        "private_submit_used": False,
        "real_orders_allowed": True,
        "max_krw": 100000,
        "max_order_krw": 10000,
        "max_daily_loss_krw": 10000,
        "max_total_loss_krw": 30000,
        "approval_text": "LIVE APPROVE 100000 10000 30000",
    }


class BrokerGatewayFirewallTests(unittest.TestCase):
    def test_broker_gateway_denies_without_approval(self) -> None:
        bad_policy = policy()
        bad_policy["broker_submit_allowed"] = False
        decision = evaluate_order_intent(reports.base_intent(), bad_policy)
        self.assertEqual(decision.decision, "REJECT")
        self.assertEqual(decision.reason, "PAPER_ONLY_POLICY_NOT_APPROVED")

    def test_research_cannot_submit_order(self) -> None:
        decision = evaluate_order_intent(reports.base_intent(producer_lane="research"), policy())
        self.assertEqual(decision.reason, "DIRECT_SUBMIT_FORBIDDEN:research")

    def test_conversion_cannot_submit_order(self) -> None:
        decision = evaluate_order_intent(reports.base_intent(producer_lane="conversion"), policy())
        self.assertEqual(decision.reason, "DIRECT_SUBMIT_FORBIDDEN:conversion")

    def test_shadow_cannot_submit_order(self) -> None:
        decision = evaluate_order_intent(reports.base_intent(producer_lane="shadow"), policy())
        self.assertEqual(decision.reason, "DIRECT_SUBMIT_FORBIDDEN:shadow")

    def test_missing_cap_blocks_order_intent(self) -> None:
        bad_policy = policy()
        bad_policy.pop("max_crypto_weight")
        decision = evaluate_order_intent(reports.base_intent(), bad_policy)
        self.assertEqual(decision.reason, "MISSING_CAP:max_crypto_weight")

    def test_expired_approval_blocks_order_intent(self) -> None:
        bad_policy = policy()
        bad_policy["expires_at_utc"] = "2026-01-01T00:00:00+00:00"
        decision = evaluate_order_intent(reports.base_intent(), bad_policy)
        self.assertEqual(decision.reason, "PAPER_APPROVAL_EXPIRED")

    def test_wrong_symbol_blocks_order_intent(self) -> None:
        decision = evaluate_order_intent(reports.base_intent(symbol="KRW-ETH"), policy())
        self.assertEqual(decision.reason, "WRONG_SYMBOL")

    def test_live_disabled_blocks_limited_live(self) -> None:
        intent = reports.base_intent(
            mode="limited_live",
            broker_submit_scope="limited_live",
            gatekeeper_permission="APPROVED_TINY_LIVE",
            notional_krw=10000,
        )
        decision = evaluate_order_intent(intent, live_policy(), kill_switch={"live_enabled": False})
        self.assertEqual(decision.reason, "KILL_SWITCH_LIVE_DISABLED")

    def test_limited_live_hard_cap_policy_can_pass(self) -> None:
        intent = reports.base_intent(
            mode="limited_live",
            broker_submit_scope="limited_live",
            gatekeeper_permission="APPROVED_TINY_LIVE",
            notional_krw=10000,
        )
        decision = evaluate_order_intent(intent, live_policy(), kill_switch={"live_enabled": True})
        self.assertEqual(decision.decision, "ALLOW_LIMITED_LIVE")
        self.assertEqual(decision.reason, "APPROVED_TINY_LIVE_UNDER_HARD_CAP")

    def test_limited_live_over_max_order_blocks(self) -> None:
        intent = reports.base_intent(
            mode="limited_live",
            broker_submit_scope="limited_live",
            gatekeeper_permission="APPROVED_TINY_LIVE",
            notional_krw=10001,
        )
        decision = evaluate_order_intent(intent, live_policy(), kill_switch={"live_enabled": True})
        self.assertEqual(decision.reason, "MAX_ORDER_KRW_EXCEEDED")

    def test_small_account_growth_paper_paper_only_can_pass(self) -> None:
        gateway = BrokerGateway(policy())
        result = gateway.submit_order_intent(reports.base_intent())
        self.assertEqual(result["decision"], "ALLOW_PAPER_ONLY")
        self.assertTrue(result["broker_endpoint_allowed"])
        self.assertFalse(result["broker_endpoint_called"])

    def test_historical_replay_intent_rejected(self) -> None:
        decision = evaluate_order_intent(
            reports.base_intent(evidence_source="historical_replay"),
            policy(),
        )
        self.assertEqual(decision.reason, "HISTORICAL_REPLAY_REJECTED")

    def test_current_tiny_live_report_uses_latest_intent_and_global_disable_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            intent_path = root / "intent.json"
            policy_path = root / "policy.json"
            disable_path = root / "DISABLE_ALL_TRADING"
            intent = reports.base_intent(
                candidate_id="bithumb_current_actionable_orca_1d_long_freeze001_sweep2154",
                mode="limited_live",
                asset_class="crypto",
                venue="bithumb",
                account_scope="tiny_live_hard_cap",
                symbol="KRW-ORCA",
                broker_submit_scope="limited_live",
                gatekeeper_permission="APPROVED_TINY_LIVE",
                approval_packet_id="LIVE APPROVE 100000 20000 100000",
                notional_krw=10000,
                producer_lane="operations",
                evidence_source="live_bithumb_public_api",
            )
            intent_path.write_text(reports.json.dumps(intent), encoding="utf-8")
            policy_path.write_text(reports.json.dumps(live_policy()), encoding="utf-8")
            disable_path.write_text("disabled", encoding="utf-8")

            with patch.object(reports, "TINY_LIVE_INTENT_JSON", intent_path), patch.object(
                reports, "LIMITED_LIVE_POLICY_JSON", policy_path
            ), patch.object(reports, "GLOBAL_DISABLE", disable_path):
                report = reports.build_current_tiny_live_report()

        self.assertEqual(report["decision"]["decision"], "ALLOW_LIMITED_LIVE")
        self.assertEqual(report["decision"]["reason"], "APPROVED_TINY_LIVE_UNDER_HARD_CAP")
        self.assertEqual(report["broker_submit_status"], "BLOCKED_BY_GLOBAL_DISABLE")
        self.assertFalse(report["decision"]["broker_endpoint_called"])
        self.assertEqual(report["submit_boundary"]["real_orders"], 0)


if __name__ == "__main__":
    unittest.main()
