from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_gatekeeper_blocker_triage_review.py")
SPEC = importlib.util.spec_from_file_location(
    "build_bithumb_current_actionable_gatekeeper_blocker_triage_review",
    MODULE_PATH,
)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class BithumbGatekeeperBlockerTriageReviewTests(unittest.TestCase):
    def gatekeeper_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_packet": False,
            "shadow_enabled_by_this_packet": False,
            "paper_enabled_by_this_packet": False,
            "live_allowed_by_this_packet": False,
            "broker_submit_allowed_by_this_packet": False,
            "private_submit_allowed_by_this_packet": False,
            "real_orders_allowed_by_this_packet": False,
        }

    def report_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def test_ready_when_gatekeeper_packet_is_blocked_by_zero_pass_robustness(self) -> None:
        report = review.build_report(
            {
                "status": "BLOCKED",
                "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                "parent_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001",
                "blockers": ["robustness_stress_pass"],
                "readiness_checks": {"oos_walkforward_pass": True, "robustness_stress_pass": False},
                "evidence_summary": {
                    "market": "KRW-ORCA",
                    "timeframe": "1d",
                    "oos_status": "OOS_WALKFORWARD_PASS",
                    "oos_pass_fold_count": 2,
                    "estimated_cagr": 1.39,
                    "estimated_mdd": -0.2,
                },
                "no_order_assertions": self.gatekeeper_assertions(),
            },
            {
                "status": "ROBUSTNESS_STRESS_ITERATE",
                "case_count": 7,
                "pass_count": 0,
                "cost_pass_count": 0,
                "no_order_assertions": self.report_assertions(),
            },
        )

        self.assertEqual(report["status"], "BITHUMB_GATEKEEPER_BLOCKER_TRIAGE_REVIEW_READY")
        self.assertEqual(report["recommended_action"], review.RECOMMENDED_ACTION)
        self.assertEqual(report["robustness_pass_count"], 0)
        self.assertFalse(report["high_cagr_counts_as_promotion_evidence"])
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocked_when_robustness_has_pass_cases(self) -> None:
        report = review.build_report(
            {
                "status": "BLOCKED",
                "blockers": ["robustness_stress_pass"],
                "readiness_checks": {"oos_walkforward_pass": True, "robustness_stress_pass": False},
                "no_order_assertions": self.gatekeeper_assertions(),
            },
            {
                "status": "ROBUSTNESS_STRESS_ITERATE",
                "case_count": 7,
                "pass_count": 1,
                "cost_pass_count": 0,
                "no_order_assertions": self.report_assertions(),
            },
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("ROBUSTNESS_HAS_PASS_CASES", report["blockers"])


if __name__ == "__main__":
    unittest.main()
