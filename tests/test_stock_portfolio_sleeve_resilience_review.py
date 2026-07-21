from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_portfolio_sleeve_resilience_review.py")
SPEC = importlib.util.spec_from_file_location("build_stock_portfolio_sleeve_resilience_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class StockPortfolioSleeveResilienceReviewTests(unittest.TestCase):
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

    def test_builds_ready_leave_one_out_resilience_without_order_paths(self) -> None:
        report = review.build_report(self.sleeve_packet())

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_RESILIENCE_REVIEW_READY")
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertEqual(report["scenario_count"], 5)
        self.assertEqual(report["viable_scenario_count"], 5)
        self.assertGreater(report["worst_leave_one_out_cagr"], 0.0)
        self.assertGreaterEqual(report["worst_leave_one_out_mdd_proxy"], -0.25)
        self.assertLessEqual(abs(report["max_cagr_drop_vs_base"]), 0.02)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_unsafe_base_packet(self) -> None:
        packet = self.sleeve_packet()
        packet["no_order_assertions"]["broker_submit_allowed_by_this_report"] = True

        report = review.build_report(packet)

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_RESILIENCE_REVIEW_BLOCKED")
        self.assertIn("BASE_PORTFOLIO_SLEEVE_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertFalse(report["ready_for_gatekeeper_review"])

    def test_blocks_unstable_leave_one_out_concentration(self) -> None:
        packet = self.sleeve_packet()
        for row in packet["components"]:
            row["lane"] = "kis_etfs"

        report = review.build_report(packet)

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_RESILIENCE_REVIEW_BLOCKED")
        self.assertIn("LEAVE_ONE_OUT_RESILIENCE_NOT_STABLE", report["blockers"])
        self.assertLess(report["viable_scenario_count"], report["scenario_count"])


if __name__ == "__main__":
    unittest.main()
