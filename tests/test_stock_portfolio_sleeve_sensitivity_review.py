from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_portfolio_sleeve_sensitivity_review.py")
SPEC = importlib.util.spec_from_file_location("build_stock_portfolio_sleeve_sensitivity_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class StockPortfolioSleeveSensitivityReviewTests(unittest.TestCase):
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
            "no_order_assertions": self.safe_assertions(),
            "components": [
                {
                    "candidate_id": f"stock_{i}",
                    "lane": "kis_etfs" if i < 3 else "kis_stocks",
                    "fixed_exposure_cap": 0.65 if i < 3 else 0.55,
                    "estimated_cagr": 0.45 - i * 0.005,
                    "estimated_mdd": -0.19,
                    "repair_applied": i >= 3,
                    "queue_order_paths_safe": True,
                }
                for i in range(5)
            ],
        }

    def test_builds_ready_sensitivity_review_without_order_paths(self) -> None:
        report = review.build_report(self.sleeve_packet())

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_SENSITIVITY_REVIEW_READY")
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertEqual(report["scenario_count"], 5)
        self.assertGreaterEqual(report["viable_scenario_count"], 3)
        self.assertEqual(report["best_scenario_id"], "etf_tilt_60_40")
        self.assertGreater(report["best_estimated_sleeve_cagr"], 0.0)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_unsafe_base_packet(self) -> None:
        packet = self.sleeve_packet()
        packet["no_order_assertions"]["live_allowed_by_this_report"] = True

        report = review.build_report(packet)

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_SENSITIVITY_REVIEW_BLOCKED")
        self.assertIn("BASE_PORTFOLIO_SLEEVE_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertFalse(report["ready_for_gatekeeper_review"])


if __name__ == "__main__":
    unittest.main()
