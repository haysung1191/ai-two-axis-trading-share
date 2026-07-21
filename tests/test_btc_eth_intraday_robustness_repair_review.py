from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_robustness_repair_review.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_robustness_repair_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class BtcEthIntradayRobustnessRepairReviewTests(unittest.TestCase):
    def safe_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def oos_packet(self) -> dict[str, object]:
        return {
            "status": "OOS_WALKFORWARD_PASS",
            "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "market": "KRW-BTC",
            "timeframe": "4h",
            "no_order_assertions": self.safe_assertions(),
        }

    def robustness_packet(self) -> dict[str, object]:
        return {
            "status": "ROBUSTNESS_STRESS_ITERATE",
            "no_order_assertions": self.safe_assertions(),
        }

    def test_reports_repair_ready_without_order_paths(self) -> None:
        repair = {
            "candidate_id": "repair",
            "status": "ROBUSTNESS_REPAIR_PASS",
            "pass_count": 5,
            "cost_pass_count": 1,
            "oos_aggregate": {"average_fold_cagr": 0.03, "worst_fold_mdd": -0.1},
        }
        with patch.object(review.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            review,
            "repair_parameter_grid",
            return_value=[{"lookback_bars": 3}],
        ), patch.object(review, "evaluate_trial", return_value=repair):
            report = review.build_report(self.oos_packet(), self.robustness_packet())

        self.assertEqual(report["status"], "ROBUSTNESS_REPAIR_READY")
        self.assertEqual(report["repair_pass_count"], 1)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_unsafe_inputs(self) -> None:
        packet = self.oos_packet()
        packet["no_order_assertions"] = {"broker_submit_allowed_by_this_report": True}

        report = review.build_report(packet, self.robustness_packet())

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("INPUT_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertEqual(report["trial_count"], 0)

    def test_surfaces_best_cost_stress_gap_for_iteration(self) -> None:
        row = {
            "candidate_id": "repair",
            "status": "ROBUSTNESS_REPAIR_ITERATE",
            "pass_count": 4,
            "cost_pass_count": 0,
            "oos_aggregate": {"average_fold_cagr": 0.03, "worst_fold_mdd": -0.1},
            "cases": [
                {
                    "case_id": "cost_30bps",
                    "status": "STRESS_ITERATE",
                    "full_window_metrics": {"total_return": -0.02, "mdd": -0.18, "trade_count": 40},
                    "fold_aggregate": {"pass_fold_count": 2, "positive_fold_count": 2},
                },
                {
                    "case_id": "cost_40bps",
                    "status": "STRESS_ITERATE",
                    "full_window_metrics": {"total_return": -0.08, "mdd": -0.21, "trade_count": 40},
                    "fold_aggregate": {"pass_fold_count": 2, "positive_fold_count": 2},
                },
            ],
        }
        with patch.object(review.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            review,
            "repair_parameter_grid",
            return_value=[{"lookback_bars": 3}],
        ), patch.object(review, "evaluate_trial", return_value=row):
            report = review.build_report(self.oos_packet(), self.robustness_packet())

        summary = report["best_cost_stress_summary"]
        self.assertEqual(report["status"], "ROBUSTNESS_REPAIR_ITERATE")
        self.assertEqual(summary["best_cost_case_id"], "cost_30bps")
        self.assertEqual(summary["best_cost_total_return"], -0.02)
        self.assertEqual(summary["cost_return_gap_to_pass"], 0.02)
        self.assertEqual(summary["cost_mdd_gap_to_pass"], 0.0)
        self.assertEqual(report["best_cost_case_id"], "cost_30bps")
        self.assertEqual(report["best_cost_total_return"], -0.02)
        self.assertEqual(report["best_cost_return_gap_to_pass"], 0.02)
        self.assertEqual(report["best_cost_mdd_gap_to_pass"], 0.0)

    def test_repair_parameter_grid_adds_focused_cost_repair_variants(self) -> None:
        rows = review.repair_parameter_grid("4h")

        self.assertGreater(len(rows), len(review.sweep.grid_for_timeframe("4h")))
        self.assertIn(
            {
                "lookback_bars": 3,
                "hold_bars": 12,
                "volume_window": 18,
                "volume_ratio_floor": 1.0,
                "momentum_threshold": 0.004,
                "stop_loss": 0.035,
                "take_profit": 0.08,
                "round_trip_cost_rate": review.backtest.ROUND_TRIP_COST_RATE,
            },
            rows,
        )


if __name__ == "__main__":
    unittest.main()
