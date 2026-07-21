from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_portfolio_sleeve_resilience_ladder_review.py")
SPEC = importlib.util.spec_from_file_location("build_stock_portfolio_sleeve_resilience_ladder_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class StockPortfolioSleeveResilienceLadderReviewTests(unittest.TestCase):
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
        return {
            "base": self.ready_packet(
                "PORTFOLIO_SLEEVE_REVIEW_READY",
                estimated_sleeve_cagr=0.44,
                weighted_mdd_proxy=-0.19,
            ),
            "sensitivity": self.ready_packet(
                "PORTFOLIO_SLEEVE_SENSITIVITY_REVIEW_READY",
                scenario_count=5,
                viable_scenario_count=4,
            ),
            "leave_one_out": self.ready_packet(
                "PORTFOLIO_SLEEVE_RESILIENCE_REVIEW_READY",
                scenario_count=5,
                viable_scenario_count=5,
                worst_leave_one_out_cagr=0.40,
                worst_leave_one_out_mdd_proxy=-0.20,
            ),
            "pairwise": self.ready_packet(
                "PORTFOLIO_SLEEVE_PAIRWISE_RESILIENCE_REVIEW_READY",
                scenario_count=10,
                viable_scenario_count=9,
                fragile_scenario_count=1,
                worst_pairwise_cagr=0.38,
                worst_pairwise_mdd_proxy=-0.21,
            ),
            "pairwise_repair": self.ready_packet(
                "PORTFOLIO_SLEEVE_PAIRWISE_FRAGILITY_REPAIR_REVIEW_READY",
                scenario_count=10,
                repaired_viable_scenario_count=10,
                source_fragile_scenario_count=1,
                repaired_source_fragile_scenario_count=1,
                worst_repaired_cagr=0.37,
                worst_repaired_mdd_proxy=-0.20,
            ),
            "tail_drop": self.ready_packet(
                "PORTFOLIO_SLEEVE_TAIL_DROP_RESILIENCE_REVIEW_READY",
                scenario_count=10,
                viable_scenario_count=6,
                fragile_scenario_count=4,
                worst_tail_drop_cagr=0.35,
                worst_tail_drop_mdd_proxy=-0.22,
            ),
            "tail_drop_repair": self.ready_packet(
                "PORTFOLIO_SLEEVE_TAIL_DROP_FRAGILITY_REPAIR_REVIEW_READY",
                scenario_count=10,
                repaired_viable_scenario_count=10,
                source_fragile_scenario_count=4,
                repaired_source_fragile_scenario_count=4,
                worst_repaired_cagr=0.33,
                worst_repaired_mdd_proxy=-0.19,
            ),
        }

    def test_builds_ladder_review_without_order_paths(self) -> None:
        report = review.build_report(self.packets())

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_RESILIENCE_LADDER_REVIEW_READY")
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertEqual(report["ladder_stage_count"], 7)
        self.assertEqual(report["ready_stage_count"], 7)
        self.assertEqual(report["scenario_total_count"], 50)
        self.assertEqual(report["source_fragile_scenario_total_count"], 5)
        self.assertEqual(report["repaired_source_fragile_scenario_total_count"], 5)
        self.assertTrue(report["repair_closure"]["all_source_fragility_repaired"])
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_unsafe_source_stage(self) -> None:
        packets = self.packets()
        packets["tail_drop_repair"]["no_order_assertions"]["broker_submit_allowed_by_this_report"] = True

        report = review.build_report(packets)

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_RESILIENCE_LADDER_REVIEW_BLOCKED")
        self.assertIn("TAIL_DROP_REPAIR_ORDER_OR_EVIDENCE_FLAG_UNSAFE", report["blockers"])
        self.assertFalse(report["ready_for_gatekeeper_review"])


if __name__ == "__main__":
    unittest.main()
