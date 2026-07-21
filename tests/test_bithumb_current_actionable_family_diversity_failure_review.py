from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_family_diversity_failure_review.py")
SPEC = importlib.util.spec_from_file_location(
    "build_bithumb_current_actionable_family_diversity_failure_review",
    MODULE_PATH,
)
assert SPEC is not None
assert SPEC.loader is not None
failure = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(failure)


SAFE = {
    "no_order_assertions": {
        "promotion_allowed_by_this_report": False,
        "paper_enabled_by_this_report": False,
        "live_allowed_by_this_report": False,
        "broker_submit_allowed_by_this_report": False,
        "private_submit_allowed_by_this_report": False,
        "real_orders_allowed_by_this_report": False,
    }
}


class BithumbCurrentActionableFamilyDiversityFailureReviewTests(unittest.TestCase):
    def test_builds_failure_direction_without_order_paths(self) -> None:
        report = failure.build_report(
            {
                **SAFE,
                "status": "FAMILY_DIVERSITY_ITERATE",
                "current_oos_candidate_id": "orca",
                "current_oos_market": "KRW-ORCA",
                "evaluated_candidate_count": 2,
                "oos_pass_candidate_count": 0,
                "robustness_pass_candidate_count": 0,
                "candidate_results": [
                    {
                        "candidate_id": "pola",
                        "market": "KRW-POLA",
                        "status": "OOS_CANDIDATE_ITERATE",
                        "aggregate": {
                            "fold_count": 3,
                            "pass_fold_count": 1,
                            "positive_fold_count": 1,
                            "worst_fold_mdd": -0.19,
                            "average_fold_cagr": 0.3,
                            "total_trade_count": 11,
                        },
                    },
                    {
                        "candidate_id": "bio",
                        "market": "KRW-BIO",
                        "status": "OOS_CANDIDATE_ITERATE",
                        "aggregate": {
                            "fold_count": 3,
                            "pass_fold_count": 0,
                            "positive_fold_count": 1,
                            "worst_fold_mdd": -0.28,
                            "average_fold_cagr": 0.4,
                            "total_trade_count": 14,
                        },
                    },
                ],
            }
        )

        self.assertEqual(report["status"], "FAMILY_DIVERSITY_FAILURE_REVIEW_READY")
        self.assertEqual(report["failure_candidate_count"], 2)
        self.assertEqual(report["dominant_failure_dimension"], "enough_pass_folds")
        self.assertEqual(report["recommended_research_action"], "REPAIR_NON_ORCA_PASS_FOLD_COVERAGE")
        self.assertEqual(report["failure_dimension_counts"]["enough_positive_folds"], 2)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_unsafe_source_packet(self) -> None:
        unsafe = {
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": True,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
            "candidate_results": [{"status": "OOS_CANDIDATE_ITERATE", "aggregate": {}}],
        }

        report = failure.build_report(unsafe)

        self.assertEqual(report["status"], "BLOCKED_UNSAFE_SOURCE_PACKET")
        self.assertIn("SOURCE_PACKET_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
