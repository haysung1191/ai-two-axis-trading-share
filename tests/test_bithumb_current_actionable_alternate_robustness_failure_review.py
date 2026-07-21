from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_alternate_robustness_failure_review.py")
SPEC = importlib.util.spec_from_file_location(
    "build_bithumb_current_actionable_alternate_robustness_failure_review",
    MODULE_PATH,
)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class BithumbAlternateRobustnessFailureReviewTests(unittest.TestCase):
    def assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def test_ready_when_oos_alternates_have_zero_robustness_passes(self) -> None:
        report = review.build_report(
            {
                "status": "ALTERNATE_ROBUSTNESS_ITERATE",
                "evaluated_oos_pass_candidate_count": 6,
                "robustness_pass_candidate_count": 0,
                "top_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                "best_alternate_candidate_id": None,
                "candidate_results": [
                    {
                        "candidate_id": "orca_1507",
                        "market": "KRW-ORCA",
                        "status": "ROBUSTNESS_STRESS_ITERATE",
                        "pass_count": 0,
                        "cost_pass_count": 0,
                        "estimated_cagr": 1.39,
                        "estimated_mdd": -0.2,
                        "oos_pass_fold_count": 2,
                        "oos_total_trade_count": 11,
                    }
                ],
                "no_order_assertions": self.assertions(),
            }
        )

        self.assertEqual(report["status"], "BITHUMB_ALTERNATE_ROBUSTNESS_FAILURE_REVIEW_READY")
        self.assertEqual(report["recommended_action"], review.RECOMMENDED_ACTION)
        self.assertEqual(report["evaluated_oos_pass_candidate_count"], 6)
        self.assertEqual(report["robustness_pass_candidate_count"], 0)
        self.assertFalse(report["oos_alternates_count_as_gatekeeper_relief"])
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])
        self.assertEqual(report["top_candidate_results"][0]["candidate_id"], "orca_1507")

    def test_blocked_when_any_robustness_pass_exists(self) -> None:
        report = review.build_report(
            {
                "status": "ALTERNATE_ROBUSTNESS_PASS",
                "evaluated_oos_pass_candidate_count": 6,
                "robustness_pass_candidate_count": 1,
                "best_alternate_candidate_id": "child",
                "no_order_assertions": self.assertions(),
            }
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("ROBUSTNESS_PASS_ALTERNATE_EXISTS", report["blockers"])


if __name__ == "__main__":
    unittest.main()
