from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_oos_stability_review.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_oos_stability_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class BtcEthIntradayOosStabilityReviewTests(unittest.TestCase):
    def safe_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def test_stability_review_is_no_order_and_reports_improved_candidate(self) -> None:
        sweep = {
            "status": "SWEEP_COMPLETE",
            "no_order_assertions": self.safe_assertions(),
            "sweeps": [
                {
                    "top_trials": [
                        {
                            "candidate_id": "btc_eth_intraday_momentum_btc_4h",
                            "market": "KRW-BTC",
                            "timeframe": "4h",
                            "frozen_parameters": {"lookback_bars": 3},
                            "metrics": {"cagr": 0.1, "mdd": -0.1},
                        }
                    ]
                }
            ],
        }
        oos = {
            "candidate_id": "current",
            "aggregate": {"worst_fold_mdd": -0.16, "average_fold_cagr": 0.02},
            "no_order_assertions": self.safe_assertions(),
        }
        improved = {
            "candidate_id": "trial",
            "status": "OOS_STABILITY_PASS",
            "worst_fold_mdd": -0.10,
            "average_fold_cagr": 0.03,
            "pass_fold_count": 2,
            "positive_fold_count": 2,
            "total_trade_count": 30,
        }
        with patch.object(review.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            review,
            "evaluate_trial",
            return_value=improved,
        ):
            report = review.build_report(sweep, oos)

        self.assertEqual(report["status"], "OOS_STABILITY_REPAIR_READY")
        self.assertEqual(report["evaluated_trial_count"], 1)
        self.assertTrue(report["best_improves_current"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_unsafe_inputs(self) -> None:
        report = review.build_report(
            {"status": "SWEEP_COMPLETE", "no_order_assertions": {"broker_submit_allowed_by_this_report": True}},
            {"no_order_assertions": self.safe_assertions()},
        )

        self.assertEqual(report["status"], "OOS_STABILITY_ITERATE")
        self.assertIn("INPUT_ORDER_PATH_NOT_SAFE", report["blockers"])


if __name__ == "__main__":
    unittest.main()
