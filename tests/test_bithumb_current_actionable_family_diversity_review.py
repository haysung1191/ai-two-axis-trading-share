from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_family_diversity_review.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_family_diversity_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
family = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(family)


SAFE = {
    "no_order_assertions": {
        "promotion_allowed_by_this_report": False,
        "paper_enabled_by_this_report": False,
        "live_allowed_by_this_report": False,
        "broker_submit_allowed_by_this_report": False,
        "private_submit_allowed_by_this_report": False,
        "real_orders_allowed_by_this_report": False,
    }
}


class BithumbCurrentActionableFamilyDiversityReviewTests(unittest.TestCase):
    def test_evaluates_non_orca_risk_pass_candidates_without_order_paths(self) -> None:
        frozen = {
            **SAFE,
            "candidates": [
                {
                    "candidate_id": "orca",
                    "market": "KRW-ORCA",
                    "frozen_parameters": {"lookback_bars": 3},
                },
                {
                    "candidate_id": "virtual",
                    "market": "KRW-VIRTUAL",
                    "frozen_parameters": {"lookback_bars": 3},
                },
            ],
        }
        risk = {
            **SAFE,
            "conversions": [
                {
                    "candidate_id": "orca",
                    "parent_candidate_id": "orca_parent",
                    "market": "KRW-ORCA",
                    "timeframe": "1d",
                    "status": "RISK_CONVERSION_PASS",
                    "conversion": {"estimated_cagr": 1.0, "source_profit_factor": 2.0, "source_mdd": -0.3},
                },
                {
                    "candidate_id": "virtual",
                    "parent_candidate_id": "virtual_parent",
                    "market": "KRW-VIRTUAL",
                    "timeframe": "1d",
                    "status": "RISK_CONVERSION_PASS",
                    "conversion": {"estimated_cagr": 0.8, "source_profit_factor": 1.9, "source_mdd": -0.25},
                },
            ],
        }
        current_oos = {
            **SAFE,
            "candidate_id": "orca_sweep",
            "parent_candidate_id": "orca_parent",
            "market": "KRW-ORCA",
        }

        with patch.object(family.oos, "evaluate_candidate") as evaluate_candidate, patch.object(
            family.oos.backtest, "fetch_candles", return_value=[{"close": 1.0}]
        ), patch.object(family, "robustness_summary") as robustness_summary:
            evaluate_candidate.return_value = {
                "candidate_id": "virtual",
                "market": "KRW-VIRTUAL",
                "status": "OOS_CANDIDATE_PASS",
                "aggregate": {
                    "fold_count": 3,
                    "pass_fold_count": 2,
                    "positive_fold_count": 2,
                    "worst_fold_mdd": -0.1,
                    "average_fold_cagr": 0.5,
                    "total_trade_count": 9,
                },
                "source_conversion": {"estimated_cagr": 0.8},
            }
            robustness_summary.return_value = {
                "status": "ROBUSTNESS_STRESS_PASS",
                "case_count": 7,
                "pass_count": 4,
                "cost_pass_count": 1,
                "cases": [],
            }
            report = family.build_report(frozen=frozen, risk=risk, current_oos=current_oos)

        self.assertEqual(report["status"], "FAMILY_DIVERSITY_ROBUSTNESS_PASS")
        self.assertEqual(report["evaluated_candidate_count"], 1)
        self.assertEqual(report["oos_pass_candidate_count"], 1)
        self.assertEqual(report["robustness_pass_candidate_count"], 1)
        self.assertEqual(report["best_candidate_id"], "virtual")
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_unsafe_source_packets(self) -> None:
        unsafe = {
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": True,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            }
        }

        report = family.build_report(frozen=SAFE, risk=unsafe, current_oos=SAFE)

        self.assertEqual(report["status"], "BLOCKED_UNSAFE_SOURCE_PACKET")
        self.assertIn("SOURCE_PACKET_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertEqual(report["evaluated_candidate_count"], 0)


if __name__ == "__main__":
    unittest.main()
