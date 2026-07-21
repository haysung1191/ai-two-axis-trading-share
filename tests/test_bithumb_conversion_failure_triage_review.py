from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_conversion_failure_triage_review.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_conversion_failure_triage_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class BithumbConversionFailureTriageReviewTests(unittest.TestCase):
    def registry(self) -> list[dict]:
        return [
            {
                "candidate_id": "locked_recent_score3_hold14_top1",
                "asset_class": "BITHUMB_KRW_CRYPTO_MULTI",
                "strategy_family": "bithumb_short_horizon",
                "status": "CONVERSION_FAILED",
                "current_gate": "G06_RISK_CONVERSION_PORTFOLIO_FIT",
                "failure_reason": "CONVERSION_RETURN_RETENTION_FAILED",
                "secondary_reasons_json": '["MDD_TOO_HIGH", "INSUFFICIENT_HISTORY"]',
                "total_return": 1.32,
                "cagr": 25802722.4,
                "mdd": -0.277,
                "sharpe": 7.05,
                "trade_count": 18,
                "scope_frozen": 0,
                "real_orders_count": 0,
                "broker_submit_allowed": 0,
                "private_submit_used": 0,
            }
        ]

    def pull_through(self) -> dict:
        return {"repair_queue": [{"candidate_id": "locked_recent_score3_hold14_top1"}]}

    def test_builds_ready_conversion_failure_triage_without_order_paths(self) -> None:
        report = review.build_report(self.registry(), self.pull_through())

        self.assertEqual(report["status"], "BITHUMB_CONVERSION_FAILURE_TRIAGE_REVIEW_READY")
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertEqual(report["conversion_failure_count"], 1)
        self.assertEqual(
            report["triage_summary"]["recommended_action"],
            "KEEP_RESEARCH_ONLY_REQUIRE_LONGER_HISTORY_AND_RISK_CONVERSION_REPAIR",
        )
        self.assertFalse(report["triage_summary"]["high_cagr_counts_as_promotion_evidence"])
        self.assertFalse(report["triage_summary"]["mutation_allowed_by_this_report"])
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_if_registry_and_repair_queue_disagree(self) -> None:
        report = review.build_report(self.registry(), {"repair_queue": []})

        self.assertEqual(report["status"], "BITHUMB_CONVERSION_FAILURE_TRIAGE_REVIEW_BLOCKED")
        self.assertIn("CONVERSION_FAILURE_ROWS_NOT_VISIBLE_IN_REPAIR_QUEUE", report["blockers"])
        self.assertFalse(report["ready_for_gatekeeper_review"])

    def test_blocks_unsafe_real_order_count(self) -> None:
        rows = self.registry()
        rows[0]["real_orders_count"] = 1

        report = review.build_report(rows, self.pull_through())

        self.assertEqual(report["status"], "BITHUMB_CONVERSION_FAILURE_TRIAGE_REVIEW_BLOCKED")
        self.assertIn("CONVERSION_FAILURE_REAL_ORDER_COUNT_UNSAFE", report["blockers"])


if __name__ == "__main__":
    unittest.main()
