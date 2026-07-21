from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_portfolio_sleeve_tail_drop_resilience_review.py")
SPEC = importlib.util.spec_from_file_location(
    "build_stock_portfolio_sleeve_tail_drop_resilience_review", MODULE_PATH
)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class StockPortfolioSleeveTailDropResilienceReviewTests(unittest.TestCase):
    def safe_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def sleeve_packet(self) -> dict:
        return {
            "status": "PORTFOLIO_SLEEVE_REVIEW_READY",
            "ready_for_gatekeeper_review": True,
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": self.safe_assertions(),
            "components": [
                {
                    "candidate_id": f"candidate_{i}",
                    "lane": "kis_etfs" if i < 3 else "kis_stocks",
                    "fixed_exposure_cap": 0.65 if i < 3 else 0.55,
                    "estimated_cagr": 0.46 - i * 0.01,
                    "estimated_mdd": -0.19,
                    "queue_order_paths_safe": True,
                }
                for i in range(5)
            ],
        }

    def pairwise_repair_packet(self) -> dict:
        return {
            "status": "PORTFOLIO_SLEEVE_PAIRWISE_FRAGILITY_REPAIR_REVIEW_READY",
            "ready_for_gatekeeper_review": True,
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": self.safe_assertions(),
        }

    def test_builds_tail_drop_resilience_without_order_paths(self) -> None:
        report = review.build_report(self.sleeve_packet(), self.pairwise_repair_packet())

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_TAIL_DROP_RESILIENCE_REVIEW_READY")
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertEqual(report["scenario_count"], 10)
        self.assertGreater(report["viable_scenario_count"], 0)
        self.assertGreater(report["worst_tail_drop_cagr"], 0.0)
        self.assertGreaterEqual(report["worst_tail_drop_mdd_proxy"], -0.25)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])
        self.assertTrue(all(len(row["removed_candidate_ids"]) == 3 for row in report["scenarios"]))
        self.assertTrue(all(row["component_count"] == 2 for row in report["scenarios"]))

    def test_records_single_lane_tail_fragility_as_review_evidence(self) -> None:
        report = review.build_report(self.sleeve_packet(), self.pairwise_repair_packet())

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_TAIL_DROP_RESILIENCE_REVIEW_READY")
        self.assertGreater(report["fragile_scenario_count"], 0)
        self.assertEqual(
            report["recommended_followup"],
            "KEEP_TAIL_DROP_AS_REVIEW_ONLY_REQUIRE_MORE_LANE_DIVERSITY_BEFORE_LIVE",
        )
        self.assertTrue(any("SINGLE_LANE_TAIL" in row["fragility_reasons"] for row in report["scenarios"]))

    def test_blocks_unsafe_pairwise_repair_source(self) -> None:
        pairwise_repair = self.pairwise_repair_packet()
        pairwise_repair["no_order_assertions"]["broker_submit_allowed_by_this_report"] = True

        report = review.build_report(self.sleeve_packet(), pairwise_repair)

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_TAIL_DROP_RESILIENCE_REVIEW_BLOCKED")
        self.assertIn("SOURCE_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertFalse(report["ready_for_gatekeeper_review"])


if __name__ == "__main__":
    unittest.main()
