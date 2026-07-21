from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_research_hold_triage_review.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_research_hold_triage_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class BithumbResearchHoldTriageReviewTests(unittest.TestCase):
    def registry(self) -> list[dict]:
        return [
            {
                "candidate_id": "btc_1d_impulse_flag_breakout_v4",
                "asset_class": "BITHUMB_KRW_CRYPTO_MULTI",
                "strategy_family": "btc_1d_impulse_flag_breakout",
                "status": "RESEARCH_HOLD",
                "current_gate": "G03_BACKTEST_SCREEN",
                "failure_reason": "BACKTEST_BELOW_VALIDATION_INTAKE_BAR",
                "cagr": 0.19,
                "mdd": -0.08,
                "sharpe": 1.4,
                "real_orders_count": 0,
                "broker_submit_allowed": 0,
                "private_submit_used": 0,
            },
            {
                "candidate_id": "btc_1d_narrow_range_expansion_drift_v1",
                "asset_class": "BITHUMB_KRW_CRYPTO_MULTI",
                "strategy_family": "btc_1d_narrow_range_expansion_drift",
                "status": "RESEARCH_HOLD",
                "current_gate": "G03_BACKTEST_SCREEN",
                "failure_reason": "BACKTEST_BELOW_VALIDATION_INTAKE_BAR",
                "cagr": 0.18,
                "mdd": -0.15,
                "sharpe": 1.1,
                "real_orders_count": 0,
                "broker_submit_allowed": 0,
                "private_submit_used": 0,
            },
        ]

    def pull_through(self) -> dict:
        return {
            "repair_queue": [
                {"candidate_id": "btc_1d_impulse_flag_breakout_v4"},
                {"candidate_id": "btc_1d_narrow_range_expansion_drift_v1"},
            ]
        }

    def test_builds_ready_research_hold_triage_without_order_paths(self) -> None:
        report = review.build_report(self.registry(), self.pull_through())

        self.assertEqual(report["status"], "BITHUMB_RESEARCH_HOLD_TRIAGE_REVIEW_READY")
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertEqual(report["research_hold_count"], 2)
        self.assertEqual(report["triage_summary"]["recommended_action"], "ARCHIVE_OR_REQUIRE_STRONGER_FROZEN_HYPOTHESIS")
        self.assertFalse(report["triage_summary"]["mutation_allowed_by_this_report"])
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_if_registry_and_repair_queue_disagree(self) -> None:
        report = review.build_report(self.registry(), {"repair_queue": []})

        self.assertEqual(report["status"], "BITHUMB_RESEARCH_HOLD_TRIAGE_REVIEW_BLOCKED")
        self.assertIn("RESEARCH_HOLD_ROWS_NOT_VISIBLE_IN_REPAIR_QUEUE", report["blockers"])
        self.assertFalse(report["ready_for_gatekeeper_review"])

    def test_blocks_unsafe_submit_flags(self) -> None:
        rows = self.registry()
        rows[0]["broker_submit_allowed"] = 1

        report = review.build_report(rows, self.pull_through())

        self.assertEqual(report["status"], "BITHUMB_RESEARCH_HOLD_TRIAGE_REVIEW_BLOCKED")
        self.assertIn("RESEARCH_HOLD_BROKER_SUBMIT_FLAG_UNSAFE", report["blockers"])


if __name__ == "__main__":
    unittest.main()
