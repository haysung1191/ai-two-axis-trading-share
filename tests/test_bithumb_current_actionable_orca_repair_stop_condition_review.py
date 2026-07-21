from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_orca_repair_stop_condition_review.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_orca_repair_stop_condition_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class BithumbOrcaRepairStopConditionReviewTests(unittest.TestCase):
    def safe_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def test_builds_ready_stop_condition_review_without_order_paths(self) -> None:
        report = review.build_report(
            {
                "failure_dimension_counts": [{"dimension": "mdd_within_limit", "case_count": 10}],
                "no_order_assertions": self.safe_assertions(),
            },
            {
                "base_candidate_id": "orca_base",
                "market": "KRW-ORCA",
                "seed_count": 3,
                "evaluated_seed_count": 3,
                "oos_pass_seed_count": 3,
                "robustness_pass_seed_count": 0,
                "best_seed_id": "seed_a",
                "counts_as_paper_or_live_evidence": False,
                "no_order_assertions": self.safe_assertions(),
            },
            {
                "ranked_seed_failures": [
                    {
                        "dominant_failure_dimensions": [
                            {"dimension": "positive_total_return", "case_count": 7},
                            {"dimension": "mdd_within_limit", "case_count": 7},
                        ]
                    }
                ],
                "no_order_assertions": self.safe_assertions(),
            },
            {
                "base_candidate_id": "orca_base",
                "market": "KRW-ORCA",
                "seed_count": 3,
                "evaluated_seed_count": 3,
                "oos_pass_seed_count": 0,
                "robustness_pass_seed_count": 0,
                "best_seed_id": "seed_b",
                "counts_as_paper_or_live_evidence": False,
                "no_order_assertions": self.safe_assertions(),
            },
        )

        self.assertEqual(report["status"], "ORCA_REPAIR_STOP_CONDITION_REVIEW_READY")
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertEqual(report["recommended_branch_action"], "STOP_ORCA_REPAIR_BRANCH_AUTOMATION")
        self.assertEqual(report["total_seed_count"], 6)
        self.assertEqual(report["first_seed_oos_pass_count"], 3)
        self.assertEqual(report["followup_seed_oos_pass_count"], 0)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_when_followup_preserves_oos_viability(self) -> None:
        safe = self.safe_assertions()
        report = review.build_report(
            {"no_order_assertions": safe},
            {
                "seed_count": 3,
                "evaluated_seed_count": 3,
                "oos_pass_seed_count": 3,
                "robustness_pass_seed_count": 0,
                "no_order_assertions": safe,
            },
            {"no_order_assertions": safe},
            {
                "seed_count": 3,
                "evaluated_seed_count": 3,
                "oos_pass_seed_count": 1,
                "robustness_pass_seed_count": 0,
                "no_order_assertions": safe,
            },
        )

        self.assertEqual(report["status"], "ORCA_REPAIR_STOP_CONDITION_REVIEW_BLOCKED")
        self.assertIn("ORCA_REPAIR_STOP_CONDITION_NOT_MET", report["blockers"])
        self.assertFalse(report["ready_for_gatekeeper_review"])


if __name__ == "__main__":
    unittest.main()
