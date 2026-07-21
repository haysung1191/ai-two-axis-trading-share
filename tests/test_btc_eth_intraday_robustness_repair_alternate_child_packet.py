from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_robustness_repair_alternate_child_packet.py")
SPEC = importlib.util.spec_from_file_location(
    "build_btc_eth_intraday_robustness_repair_alternate_child_packet",
    MODULE_PATH,
)
assert SPEC is not None
assert SPEC.loader is not None
packet_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_builder)


class BtcEthIntradayRobustnessRepairAlternateChildPacketTests(unittest.TestCase):
    def safe_report_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def source_packet(self) -> dict[str, object]:
        return {
            "status": "ROBUSTNESS_REPAIR_READY",
            "base_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "best_candidate_id": "repair_445",
            "market": "KRW-BTC",
            "timeframe": "4h",
            "trial_count": 528,
            "repair_pass_count": 3,
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": self.safe_report_assertions(),
            "candidate_results": [
                {
                    "candidate_id": "repair_445",
                    "status": "ROBUSTNESS_REPAIR_PASS",
                    "pass_count": 7,
                    "cost_pass_count": 2,
                    "screen_metrics": {"total_return": 0.11, "cagr": 0.24, "mdd": -0.18, "trade_count": 46},
                    "oos_aggregate": {"average_fold_cagr": 0.66, "worst_fold_mdd": -0.18, "total_trade_count": 45},
                    "parameters": {"lookback_bars": 3, "hold_bars": 12},
                },
                {
                    "candidate_id": "repair_441",
                    "status": "ROBUSTNESS_REPAIR_PASS",
                    "pass_count": 7,
                    "cost_pass_count": 2,
                    "screen_metrics": {"total_return": 0.16, "cagr": 0.36, "mdd": -0.15, "trade_count": 49},
                    "oos_aggregate": {"average_fold_cagr": 0.60, "worst_fold_mdd": -0.15, "total_trade_count": 48},
                    "parameters": {"lookback_bars": 3, "hold_bars": 12, "volume_window": 18},
                },
                {
                    "candidate_id": "repair_438",
                    "status": "ROBUSTNESS_REPAIR_PASS",
                    "pass_count": 6,
                    "cost_pass_count": 2,
                    "screen_metrics": {"total_return": 0.10, "cagr": 0.23, "mdd": -0.14, "trade_count": 51},
                    "oos_aggregate": {"average_fold_cagr": 0.38, "worst_fold_mdd": -0.14, "total_trade_count": 50},
                    "parameters": {"lookback_bars": 3, "hold_bars": 12},
                },
            ],
        }

    def test_builds_ready_alternate_child_packet_without_order_paths(self) -> None:
        packet = packet_builder.build_packet(self.source_packet())

        self.assertEqual(packet["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertTrue(packet["ready_for_human_review"])
        self.assertEqual(packet["alternate_pass_child_count"], 2)
        self.assertEqual(packet["top_alternate_candidate_id"], "repair_441")
        self.assertEqual(
            packet["exact_phrase_to_record"],
            "REVIEW_BTC_ETH_INTRADAY_ALTERNATE_REPAIR_CHILDREN_ONLY",
        )
        self.assertFalse(packet["counts_as_paper_or_live_evidence"])
        self.assertFalse(packet["no_order_assertions"]["live_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["broker_submit_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["real_orders_allowed_by_this_packet"])

    def test_blocks_unsafe_source_packet(self) -> None:
        source = self.source_packet()
        source["no_order_assertions"] = {"broker_submit_allowed_by_this_report": True}

        packet = packet_builder.build_packet(source)

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("SOURCE_REPAIR_PACKET_NOT_NO_ORDER_SAFE", packet["blockers"])


if __name__ == "__main__":
    unittest.main()
