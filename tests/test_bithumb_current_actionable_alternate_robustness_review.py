from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_alternate_robustness_review.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_alternate_robustness_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
alternate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(alternate)


class BithumbCurrentActionableAlternateRobustnessReviewTests(unittest.TestCase):
    def test_alternate_oos_candidates_are_review_only_and_no_order(self) -> None:
        source = {
            "status": "OOS_WALKFORWARD_PASS",
            "candidate_id": "top",
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
            "evaluations": [
                {
                    "candidate_id": "alt1",
                    "parent_candidate_id": "parent",
                    "market": "KRW-ORCA",
                    "timeframe": "1d",
                    "status": "OOS_CANDIDATE_PASS",
                    "aggregate": {"pass_fold_count": 2, "positive_fold_count": 2, "total_trade_count": 10},
                    "source_conversion": {"estimated_cagr": 1.0, "estimated_mdd": -0.2},
                }
            ],
        }

        with patch.object(alternate.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            alternate,
            "candidate_pass_summary",
            return_value={
                "candidate_id": "alt1",
                "market": "KRW-ORCA",
                "status": "ROBUSTNESS_STRESS_PASS",
                "case_count": 7,
                "pass_count": 4,
                "cost_pass_count": 1,
            },
        ):
            report = alternate.build_report(source)

        self.assertEqual(report["status"], "ALTERNATE_ROBUSTNESS_PASS")
        self.assertEqual(report["evaluated_oos_pass_candidate_count"], 1)
        self.assertEqual(report["robustness_pass_candidate_count"], 1)
        self.assertEqual(report["best_alternate_candidate_id"], "alt1")
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_unsafe_oos_packet(self) -> None:
        report = alternate.build_report(
            {
                "status": "OOS_WALKFORWARD_PASS",
                "no_order_assertions": {"broker_submit_allowed_by_this_report": True},
                "evaluations": [{"candidate_id": "alt1", "status": "OOS_CANDIDATE_PASS"}],
            }
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("OOS_PACKET_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertEqual(report["evaluated_oos_pass_candidate_count"], 0)


if __name__ == "__main__":
    unittest.main()
