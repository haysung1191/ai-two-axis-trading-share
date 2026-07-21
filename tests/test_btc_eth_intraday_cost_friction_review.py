from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_cost_friction_review.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_cost_friction_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class BtcEthIntradayCostFrictionReviewTests(unittest.TestCase):
    def safe_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def source(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": "ROBUSTNESS_STRESS_ITERATE",
            "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "market": "KRW-BTC",
            "timeframe": "4h",
            "case_count": 7,
            "pass_count": 4,
            "cost_pass_count": 0,
            "counts_as_paper_or_live_evidence": False,
            "cases": [
                {
                    "case_id": "cost_30bps",
                    "status": "STRESS_ITERATE",
                    "full_window_metrics": {
                        "total_return": -0.033,
                        "cagr": -0.066,
                        "mdd": -0.189,
                        "profit_factor": 0.98,
                        "trade_count": 78,
                    },
                    "fold_aggregate": {
                        "pass_fold_count": 2,
                        "positive_fold_count": 2,
                        "worst_fold_mdd": -0.188,
                        "average_fold_cagr": 0.098,
                    },
                }
            ],
            "no_order_assertions": self.safe_assertions(),
        }
        payload.update(overrides)
        return payload

    def test_ready_when_cost_pass_count_is_zero_but_other_stress_cases_pass(self) -> None:
        report = review.build_report(self.source())

        self.assertEqual(report["status"], "BTC_ETH_INTRADAY_COST_FRICTION_REVIEW_READY")
        self.assertEqual(report["recommended_action"], review.RECOMMENDED_ACTION)
        self.assertEqual(report["pass_count"], 4)
        self.assertEqual(report["cost_pass_count"], 0)
        self.assertEqual(report["cost_case_count"], 1)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["mutation_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocked_when_cost_case_passes(self) -> None:
        report = review.build_report(self.source(cost_pass_count=1))

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("COST_STRESS_ALREADY_HAS_PASS_CASE", report["blockers"])

    def test_blocked_when_source_order_path_is_unsafe(self) -> None:
        report = review.build_report(
            self.source(no_order_assertions={"broker_submit_allowed_by_this_report": True})
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("SOURCE_ORDER_PATH_NOT_SAFE", report["blockers"])


if __name__ == "__main__":
    unittest.main()
