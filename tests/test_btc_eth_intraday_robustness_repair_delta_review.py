from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_robustness_repair_delta_review.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_robustness_repair_delta_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class BtcEthIntradayRobustnessRepairDeltaReviewTests(unittest.TestCase):
    def safe_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def test_builds_lineage_delta_review_without_order_paths(self) -> None:
        risk_packet = {
            "status": "READY_FOR_GATEKEEPER_REVIEW",
            "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "market": "KRW-BTC",
            "timeframe": "4h",
            "conversion": {
                "target_mdd_abs": 0.12,
                "recommended_exposure_cap": 0.75,
                "estimated_average_fold_cagr": 0.06,
                "estimated_worst_fold_mdd": -0.12,
                "total_trade_count": 75,
            },
            "no_order_assertions": self.safe_assertions(),
        }
        repair_packet = {
            "status": "ROBUSTNESS_REPAIR_READY",
            "base_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "best_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001_robustrepair_445",
            "repair_pass_count": 42,
            "best_pass_count": 7,
            "best_cost_pass_count": 2,
            "best_cost_case_id": "cost_30bps",
            "best_cost_total_return": 0.063,
            "best_cost_mdd": -0.196,
            "candidate_results": [
                {
                    "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001_robustrepair_445",
                    "screen_metrics": {"cagr": 0.24, "mdd": -0.18, "trade_count": 46},
                    "oos_aggregate": {
                        "average_fold_cagr": 0.24,
                        "worst_fold_mdd": -0.18,
                        "total_trade_count": 45,
                        "pass_fold_count": 2,
                        "positive_fold_count": 2,
                    },
                }
            ],
            "no_order_assertions": self.safe_assertions(),
        }

        report = review.build_report(risk_packet, repair_packet)

        self.assertEqual(report["status"], "ROBUSTNESS_REPAIR_DELTA_REVIEW_READY")
        self.assertTrue(report["lineage_match"])
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertEqual(report["child_candidate_id"], "btc_eth_intraday_momentum_btc_4h_sweep001_robustrepair_445")
        self.assertAlmostEqual(report["child_conversion"]["recommended_exposure_cap"], 2 / 3)
        self.assertGreater(report["delta"]["estimated_average_fold_cagr_delta"], 0)
        self.assertEqual(report["delta"]["trade_count_delta"], -30)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_lineage_mismatch(self) -> None:
        risk_packet = {
            "status": "READY_FOR_GATEKEEPER_REVIEW",
            "candidate_id": "base_a",
            "conversion": {"target_mdd_abs": 0.12},
            "no_order_assertions": self.safe_assertions(),
        }
        repair_packet = {
            "status": "ROBUSTNESS_REPAIR_READY",
            "base_candidate_id": "base_b",
            "best_candidate_id": "base_b_robustrepair_001",
            "candidate_results": [{"candidate_id": "base_b_robustrepair_001", "oos_aggregate": {}}],
            "no_order_assertions": self.safe_assertions(),
        }

        report = review.build_report(risk_packet, repair_packet)

        self.assertEqual(report["status"], "ROBUSTNESS_REPAIR_DELTA_REVIEW_BLOCKED")
        self.assertIn("BASE_REPAIR_LINEAGE_MISMATCH", report["blockers"])
        self.assertFalse(report["ready_for_gatekeeper_review"])


if __name__ == "__main__":
    unittest.main()
