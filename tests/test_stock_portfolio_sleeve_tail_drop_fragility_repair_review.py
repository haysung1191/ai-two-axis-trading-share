from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_portfolio_sleeve_tail_drop_fragility_repair_review.py")
SPEC = importlib.util.spec_from_file_location(
    "build_stock_portfolio_sleeve_tail_drop_fragility_repair_review", MODULE_PATH
)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class StockPortfolioSleeveTailDropFragilityRepairReviewTests(unittest.TestCase):
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

    def tail_drop_packet(self) -> dict:
        return {
            "status": "PORTFOLIO_SLEEVE_TAIL_DROP_RESILIENCE_REVIEW_READY",
            "ready_for_gatekeeper_review": True,
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": self.safe_assertions(),
            "scenarios": [
                {
                    "scenario_id": "drop_three_leave_only_etfs",
                    "remaining_candidate_ids": ["candidate_0", "candidate_1"],
                    "removed_candidate_ids": ["candidate_2", "candidate_3", "candidate_4"],
                    "removed_lanes": ["kis_etfs", "kis_stocks", "kis_stocks"],
                    "fragile": True,
                    "fragility_reasons": ["SINGLE_LANE_TAIL"],
                },
                {
                    "scenario_id": "drop_three_mixed",
                    "remaining_candidate_ids": ["candidate_1", "candidate_4"],
                    "removed_candidate_ids": ["candidate_0", "candidate_2", "candidate_3"],
                    "removed_lanes": ["kis_etfs", "kis_etfs", "kis_stocks"],
                    "fragile": False,
                    "fragility_reasons": [],
                },
            ],
        }

    def test_repairs_tail_drop_single_lane_fragility_without_order_paths(self) -> None:
        report = review.build_report(self.sleeve_packet(), self.tail_drop_packet())

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_TAIL_DROP_FRAGILITY_REPAIR_REVIEW_READY")
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertEqual(report["scenario_count"], 2)
        self.assertEqual(report["source_fragile_scenario_count"], 1)
        self.assertEqual(report["repaired_source_fragile_scenario_count"], 1)
        self.assertEqual(report["repaired_viable_scenario_count"], 2)
        self.assertLessEqual(report["max_repaired_lane_weight"], 0.80)
        self.assertLessEqual(report["max_residual_cash_weight"], 0.25)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_unsafe_tail_drop_source(self) -> None:
        tail_drop = self.tail_drop_packet()
        tail_drop["no_order_assertions"]["broker_submit_allowed_by_this_report"] = True

        report = review.build_report(self.sleeve_packet(), tail_drop)

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_TAIL_DROP_FRAGILITY_REPAIR_REVIEW_BLOCKED")
        self.assertIn("SOURCE_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertFalse(report["ready_for_gatekeeper_review"])


if __name__ == "__main__":
    unittest.main()
