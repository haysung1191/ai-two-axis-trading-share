from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_orca_robustness_repair_review.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_orca_robustness_repair_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
repair = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repair)


SAFE_ASSERTIONS = {
    "promotion_allowed_by_this_report": False,
    "paper_enabled_by_this_report": False,
    "live_allowed_by_this_report": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders_allowed_by_this_report": False,
}


class BithumbCurrentActionableOrcaRobustnessRepairReviewTests(unittest.TestCase):
    def source_packet(self) -> dict:
        return {
            "status": "OOS_WALKFORWARD_PASS",
            "top_oos": {
                "candidate_id": "orca_sweep1507",
                "parent_candidate_id": "orca_parent",
                "market": "KRW-ORCA",
                "timeframe": "1d",
            },
            "no_order_assertions": SAFE_ASSERTIONS,
        }

    def test_repair_review_reports_passing_child_without_order_permissions(self) -> None:
        def fake_screen_candidate(trial, candles):
            return {
                "candidate_id": trial["candidate_id"],
                "market": trial["market"],
                "timeframe": trial["timeframe"],
                "metrics": {
                    "cagr": 1.0,
                    "total_return": 0.5,
                    "mdd": -0.2,
                    "trade_count": 12,
                    "profit_factor": 2.0,
                },
            }

        def fake_oos_candidate(candidate, candle_cache):
            return {
                "candidate_id": candidate["candidate_id"],
                "parent_candidate_id": candidate["parent_candidate_id"],
                "market": candidate["market"],
                "timeframe": candidate["timeframe"],
                "status": "OOS_CANDIDATE_PASS",
                "aggregate": {
                    "fold_count": 3,
                    "pass_fold_count": 2,
                    "positive_fold_count": 2,
                    "total_trade_count": 12,
                },
            }

        with (
            patch.object(repair.sweep.backtest, "fetch_candles", return_value=[{"close": 1.0}]),
            patch.object(repair.sweep.backtest, "screen_candidate", side_effect=fake_screen_candidate),
            patch.object(repair.oos, "evaluate_candidate", side_effect=fake_oos_candidate),
            patch.object(
                repair,
                "robustness_summary",
                return_value={
                    "status": "ROBUSTNESS_STRESS_PASS",
                    "case_count": 7,
                    "pass_count": 4,
                    "cost_pass_count": 1,
                    "cases": [],
                },
            ),
        ):
            report = repair.build_report(self.source_packet())

        self.assertEqual(report["status"], "ORCA_ROBUSTNESS_REPAIR_PASS")
        self.assertEqual(report["robustness_pass_candidate_count"], repair.MAX_ROBUSTNESS_EVALS)
        self.assertFalse(report["no_order_assertions"]["paper_enabled_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_repair_review_blocks_unsafe_source_packet(self) -> None:
        source = self.source_packet()
        source["no_order_assertions"] = dict(SAFE_ASSERTIONS)
        source["no_order_assertions"]["live_allowed_by_this_report"] = True

        report = repair.build_report(source)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("SOURCE_PACKET_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertEqual(report["trial_count"], 0)

    def test_no_passing_repair_child_is_research_iteration_not_hard_block(self) -> None:
        def fake_screen_candidate(trial, candles):
            return {
                "candidate_id": trial["candidate_id"],
                "market": trial["market"],
                "timeframe": trial["timeframe"],
                "metrics": {"cagr": 0.4, "total_return": 0.2, "mdd": -0.2, "trade_count": 12, "profit_factor": 1.5},
            }

        def fake_oos_candidate(candidate, candle_cache):
            return {
                "candidate_id": candidate["candidate_id"],
                "parent_candidate_id": candidate["parent_candidate_id"],
                "market": candidate["market"],
                "timeframe": candidate["timeframe"],
                "status": "OOS_CANDIDATE_PASS",
                "aggregate": {"fold_count": 3, "pass_fold_count": 2, "positive_fold_count": 2, "total_trade_count": 12},
            }

        with (
            patch.object(repair.sweep.backtest, "fetch_candles", return_value=[{"close": 1.0}]),
            patch.object(repair.sweep.backtest, "screen_candidate", side_effect=fake_screen_candidate),
            patch.object(repair.oos, "evaluate_candidate", side_effect=fake_oos_candidate),
            patch.object(
                repair,
                "robustness_summary",
                return_value={
                    "status": "ROBUSTNESS_STRESS_ITERATE",
                    "case_count": 7,
                    "pass_count": 1,
                    "cost_pass_count": 0,
                    "cases": [],
                },
            ),
        ):
            report = repair.build_report(self.source_packet())

        self.assertEqual(report["status"], "ORCA_ROBUSTNESS_REPAIR_ITERATE")
        self.assertIn("NO_ORCA_ROBUSTNESS_REPAIR_PASS", report["blockers"])

    def test_repair_review_uses_expanded_robustness_eval_cap(self) -> None:
        self.assertEqual(repair.MAX_ROBUSTNESS_EVALS, 192)


if __name__ == "__main__":
    unittest.main()
