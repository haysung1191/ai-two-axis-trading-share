from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_portfolio_sleeve_pairwise_resilience_review.py")
SPEC = importlib.util.spec_from_file_location("build_stock_portfolio_sleeve_pairwise_resilience_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class StockPortfolioSleevePairwiseResilienceReviewTests(unittest.TestCase):
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
                    "candidate_id": f"stock_{i}",
                    "lane": "kis_etfs" if i < 3 else "kis_stocks",
                    "fixed_exposure_cap": 0.65 if i < 3 else 0.55,
                    "estimated_cagr": 0.46 - i * 0.01,
                    "estimated_mdd": -0.19,
                    "queue_order_paths_safe": True,
                }
                for i in range(5)
            ],
        }

    def test_builds_pairwise_resilience_review_without_order_paths(self) -> None:
        report = review.build_report(self.sleeve_packet())

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_PAIRWISE_RESILIENCE_REVIEW_READY")
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertEqual(report["scenario_count"], 10)
        self.assertGreaterEqual(report["viable_scenario_count"], 0)
        self.assertGreater(report["worst_pairwise_cagr"], 0.0)
        self.assertGreaterEqual(report["worst_pairwise_mdd_proxy"], -0.25)
        self.assertEqual(report["counts_as_paper_or_live_evidence"], False)
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])
        self.assertIn("recommended_followup", report)
        self.assertTrue(all(len(row["removed_candidate_ids"]) == 2 for row in report["scenarios"]))

    def test_marks_lane_concentration_fragility_as_review_evidence(self) -> None:
        packet = self.sleeve_packet()
        report = review.build_report(packet)

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_PAIRWISE_RESILIENCE_REVIEW_READY")
        self.assertGreater(report["fragile_scenario_count"], 0)
        self.assertEqual(report["recommended_followup"], "ADD_LANE_DIVERSIFICATION_OR_CAP_ETF_CLUSTER_BEFORE_LIVE")
        self.assertTrue(
            any("LANE_WEIGHT_ABOVE_80PCT" in row["fragility_reasons"] for row in report["scenarios"])
        )

    def test_blocks_unsafe_base_packet(self) -> None:
        packet = self.sleeve_packet()
        packet["no_order_assertions"]["broker_submit_allowed_by_this_report"] = True

        report = review.build_report(packet)

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_PAIRWISE_RESILIENCE_REVIEW_BLOCKED")
        self.assertIn("BASE_PORTFOLIO_SLEEVE_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertFalse(report["ready_for_gatekeeper_review"])


if __name__ == "__main__":
    unittest.main()
