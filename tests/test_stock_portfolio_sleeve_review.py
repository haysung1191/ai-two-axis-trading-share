from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_portfolio_sleeve_review.py")
SPEC = importlib.util.spec_from_file_location("build_stock_portfolio_sleeve_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class StockPortfolioSleeveReviewTests(unittest.TestCase):
    def safe_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def test_builds_ready_top5_sleeve_review_without_order_paths(self) -> None:
        rows = [
            {
                "candidate_id": f"stock_{i}",
                "lane": "kis_etfs" if i < 3 else "kis_stocks",
                "status": "ROBUSTNESS_STRESS_PASS",
                "overlay": "fixed_exposure_065" if i == 0 else "fixed_exposure_055",
                "pass_count": 4,
                "mdd_stress_pass_count": 1,
                "repair_applied": i >= 3,
                "queue_order_paths_safe": True,
                "cases": [
                    {
                        "case_id": "base_recheck",
                        "estimated_cagr": 0.40 + i * 0.01,
                        "estimated_mdd": -0.19,
                        "estimated_return_retention": 0.55,
                    }
                ],
            }
            for i in range(5)
        ]

        report = review.build_report(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "no_order_assertions": self.safe_assertions(),
            },
            {
                "status": "REPAIRED_ROBUSTNESS_STRESS_PASS",
                "queue_coverage": {
                    "stress_pass_candidate_count": 5,
                    "repaired_candidate_count": 2,
                    "top5_full_coverage": True,
                    "all_covered_candidates_safe": True,
                },
                "candidate_results": rows,
                "no_order_assertions": self.safe_assertions(),
            },
        )

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_REVIEW_READY")
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertEqual(report["sleeve_policy"]["component_count"], 5)
        self.assertAlmostEqual(report["sleeve_policy"]["component_weight"], 0.2)
        self.assertEqual(report["sleeve_policy"]["lane_weights"]["kis_etfs"], 0.6000000000000001)
        self.assertEqual(report["sleeve_metrics"]["stress_pass_candidate_count"], 5)
        self.assertEqual(report["sleeve_metrics"]["repaired_candidate_count"], 2)
        self.assertGreater(report["sleeve_metrics"]["estimated_sleeve_cagr"], 0.0)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_unsafe_component(self) -> None:
        report = review.build_report(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "no_order_assertions": self.safe_assertions(),
            },
            {
                "status": "REPAIRED_ROBUSTNESS_STRESS_PASS",
                "queue_coverage": {
                    "stress_pass_candidate_count": 5,
                    "top5_full_coverage": True,
                    "all_covered_candidates_safe": True,
                },
                "candidate_results": [
                    {
                        "candidate_id": f"stock_{i}",
                        "lane": "kis_etfs",
                        "status": "ROBUSTNESS_STRESS_PASS",
                        "overlay": "fixed_exposure_055",
                        "queue_order_paths_safe": i != 0,
                        "cases": [{"case_id": "base_recheck", "estimated_cagr": 0.4, "estimated_mdd": -0.19}],
                    }
                    for i in range(5)
                ],
                "no_order_assertions": self.safe_assertions(),
            },
        )

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_REVIEW_BLOCKED")
        self.assertIn("COMPONENT_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertFalse(report["ready_for_gatekeeper_review"])


if __name__ == "__main__":
    unittest.main()
