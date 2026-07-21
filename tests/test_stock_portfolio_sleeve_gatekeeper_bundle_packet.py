from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_portfolio_sleeve_gatekeeper_bundle_packet.py")
SPEC = importlib.util.spec_from_file_location("build_stock_portfolio_sleeve_gatekeeper_bundle_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
packet_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_builder)


class StockPortfolioSleeveGatekeeperBundlePacketTests(unittest.TestCase):
    def safe_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def ready_packet(self, status: str, **extra: object) -> dict:
        packet = {
            "status": status,
            "ready_for_gatekeeper_review": True,
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": self.safe_assertions(),
        }
        packet.update(extra)
        return packet

    def packets(self) -> dict[str, dict]:
        packets = {
            key: self.ready_packet(status)
            for key, status in packet_builder.EXPECTED_STATUSES.items()
        }
        packets["base"].update(
            {
                "sleeve_policy": {
                    "component_count": 5,
                    "total_effective_exposure": 0.606,
                    "max_lane_weight": 0.6,
                },
                "sleeve_metrics": {
                    "estimated_sleeve_cagr": 0.44,
                    "weighted_mdd_proxy": -0.19,
                },
            }
        )
        packets["ladder"].update(
            {
                "ladder_stage_count": 7,
                "ready_stage_count": 7,
                "scenario_total_count": 50,
                "source_fragile_scenario_total_count": 5,
                "repaired_source_fragile_scenario_total_count": 5,
                "worst_ladder_cagr": 0.33,
                "worst_ladder_mdd_proxy": -0.2,
                "repair_closure": {"all_source_fragility_repaired": True},
            }
        )
        packets["constraint_envelope"].update(
            {
                "scenario_count": 21,
                "constraint_pass_scenario_count": 21,
                "constraint_fail_scenario_count": 0,
                "worst_constraint_cagr": 0.33,
                "worst_constraint_mdd_proxy": -0.194,
            }
        )
        return packets

    def test_builds_review_only_bundle(self) -> None:
        report = packet_builder.build_report(self.packets())

        self.assertEqual(report["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertEqual(report["exact_phrase_to_record"], "REVIEW_STOCK_PORTFOLIO_SLEEVE_BUNDLE_ONLY")
        self.assertEqual(report["stage_count"], 9)
        self.assertEqual(report["ready_stage_count"], 9)
        self.assertEqual(report["constraint_fail_scenario_count"], 0)
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_unsafe_source_stage(self) -> None:
        packets = self.packets()
        packets["constraint_envelope"]["no_order_assertions"]["broker_submit_allowed_by_this_report"] = True

        report = packet_builder.build_report(packets)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("CONSTRAINT_ENVELOPE_ORDER_OR_EVIDENCE_FLAG_UNSAFE", report["blockers"])
        self.assertFalse(report["ready_for_gatekeeper_review"])


if __name__ == "__main__":
    unittest.main()
