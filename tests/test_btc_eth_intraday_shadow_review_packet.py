from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_shadow_review_packet.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_shadow_review_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
packet_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_mod)


SAFE_REPORT_ASSERTIONS = {
    "promotion_allowed_by_this_report": False,
    "paper_enabled_by_this_report": False,
    "live_allowed_by_this_report": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders_allowed_by_this_report": False,
}


class BtcEthIntradayShadowReviewPacketTests(unittest.TestCase):
    def test_packet_is_review_ready_without_enabling_shadow_or_orders(self) -> None:
        candidate_id = "btc_eth_intraday_momentum_btc_4h_sweep001"
        packet = packet_mod.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "candidate_id": candidate_id,
                "market": "KRW-BTC",
                "timeframe": "4h",
                "conversion": {"recommended_exposure_cap": 0.71},
                "gate_result": "pass_mdd_cap",
                "next_gate": "G07_SHADOW_REVIEW_RESEARCH_ONLY",
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "OOS_WALKFORWARD_PASS",
                "candidate_id": candidate_id,
                "aggregate": {"pass_fold_count": 2, "positive_fold_count": 2, "total_trade_count": 74},
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "READY_FOR_OOS_RESEARCH_REVIEW",
                "candidate": {"candidate_id": candidate_id},
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "ROBUSTNESS_REPAIR_READY",
                "best_candidate_id": f"{candidate_id}_robustrepair_445",
                "best_pass_count": 7,
                "best_cost_pass_count": 2,
                "best_cost_stress_summary": {
                    "best_cost_case_id": "cost_30bps",
                    "best_cost_total_return": 0.068,
                },
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "gatekeeper_action_packet": {
                    "btc_eth_intraday_risk_conversion": {"ready_for_shadow_review": True}
                }
            },
            {
                "status": "WARN",
                "halt_count": 0,
                "warn_count": 1,
                "checks": [
                    {"name": "live_disabled", "status": "PASS"},
                    {"name": "private_submit_unused", "status": "PASS"},
                    {"name": "real_orders_zero", "status": "PASS"},
                ],
            },
        )

        self.assertEqual(packet["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertEqual(packet["blockers"], [])
        self.assertTrue(packet["readiness_checks"]["robustness_repair_ready"])
        self.assertTrue(packet["readiness_checks"]["risk_guard_review_safety_pass"])
        self.assertEqual(packet["evidence_summary"]["risk_guard_status"], "WARN")
        self.assertEqual(packet["evidence_summary"]["risk_guard_halt_count"], 0)
        self.assertEqual(
            packet["evidence_summary"]["robustness_repair_candidate_id"],
            f"{candidate_id}_robustrepair_445",
        )
        self.assertEqual(packet["evidence_summary"]["robustness_repair_cost_pass_count"], 2)
        self.assertFalse(packet["no_order_assertions"]["shadow_enabled_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["paper_enabled_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["live_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["broker_submit_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["real_orders_allowed_by_this_packet"])

    def test_packet_blocks_when_source_order_assertions_are_not_safe(self) -> None:
        unsafe = dict(SAFE_REPORT_ASSERTIONS)
        unsafe["live_allowed_by_this_report"] = True
        packet = packet_mod.build_packet(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "candidate_id": "c", "no_order_assertions": unsafe},
            {"status": "OOS_WALKFORWARD_PASS", "candidate_id": "c", "no_order_assertions": SAFE_REPORT_ASSERTIONS},
            {
                "status": "READY_FOR_OOS_RESEARCH_REVIEW",
                "candidate": {"candidate_id": "c"},
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {"status": "ROBUSTNESS_REPAIR_READY", "no_order_assertions": SAFE_REPORT_ASSERTIONS},
            {"gatekeeper_action_packet": {"btc_eth_intraday_risk_conversion": {"ready_for_shadow_review": True}}},
            {
                "status": "PASS",
                "halt_count": 0,
                "checks": [
                    {"name": "live_disabled", "status": "PASS"},
                    {"name": "private_submit_unused", "status": "PASS"},
                    {"name": "real_orders_zero", "status": "PASS"},
                ],
            },
        )

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("risk_no_order_safe", packet["blockers"])

    def test_packet_blocks_when_robustness_repair_is_not_ready(self) -> None:
        packet = packet_mod.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "candidate_id": "c",
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {"status": "OOS_WALKFORWARD_PASS", "candidate_id": "c", "no_order_assertions": SAFE_REPORT_ASSERTIONS},
            {
                "status": "READY_FOR_OOS_RESEARCH_REVIEW",
                "candidate": {"candidate_id": "c"},
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {"status": "ROBUSTNESS_REPAIR_ITERATE", "no_order_assertions": SAFE_REPORT_ASSERTIONS},
            {"gatekeeper_action_packet": {"btc_eth_intraday_risk_conversion": {"ready_for_shadow_review": True}}},
            {
                "status": "PASS",
                "halt_count": 0,
                "checks": [
                    {"name": "live_disabled", "status": "PASS"},
                    {"name": "private_submit_unused", "status": "PASS"},
                    {"name": "real_orders_zero", "status": "PASS"},
                ],
            },
        )

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("robustness_repair_ready", packet["blockers"])

    def test_packet_blocks_when_risk_guard_hard_safety_fails(self) -> None:
        packet = packet_mod.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "candidate_id": "c",
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {"status": "OOS_WALKFORWARD_PASS", "candidate_id": "c", "no_order_assertions": SAFE_REPORT_ASSERTIONS},
            {
                "status": "READY_FOR_OOS_RESEARCH_REVIEW",
                "candidate": {"candidate_id": "c"},
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {"status": "ROBUSTNESS_REPAIR_READY", "no_order_assertions": SAFE_REPORT_ASSERTIONS},
            {"gatekeeper_action_packet": {"btc_eth_intraday_risk_conversion": {"ready_for_shadow_review": True}}},
            {
                "status": "WARN",
                "halt_count": 1,
                "checks": [
                    {"name": "live_disabled", "status": "PASS"},
                    {"name": "private_submit_unused", "status": "PASS"},
                    {"name": "real_orders_zero", "status": "PASS"},
                ],
            },
        )

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("risk_guard_review_safety_pass", packet["blockers"])


if __name__ == "__main__":
    unittest.main()
