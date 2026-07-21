import unittest

import build_bithumb_current_actionable_orca_oos_family_review as builder


def candidate(candidate_id: str, take_profit: float, estimated_cagr: float = 1.2) -> dict:
    return {
        "candidate_id": candidate_id,
        "parent_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001",
        "market": "KRW-ORCA",
        "timeframe": "1d",
        "status": "OOS_CANDIDATE_PASS",
        "parameters": {
            "lookback_bars": 3,
            "hold_bars": 3,
            "volume_window": 10,
            "volume_ratio_floor": 1.0,
            "momentum_threshold": 0.03,
            "stop_loss": 0.12,
            "take_profit": take_profit,
        },
        "source_conversion": {
            "estimated_cagr": estimated_cagr,
            "estimated_mdd": -0.2,
            "recommended_exposure_cap": 0.68,
            "source_trade_count": 14,
            "source_profit_factor": 3.0,
        },
        "aggregate": {
            "fold_count": 3,
            "pass_fold_count": 2,
            "positive_fold_count": 2,
            "worst_fold_mdd": -0.19,
            "average_fold_cagr": 3.0,
            "total_trade_count": 11,
        },
    }


class BithumbCurrentActionableOrcaOosFamilyReviewTest(unittest.TestCase):
    def test_ready_when_multiple_orca_oos_pass_children_are_safe(self) -> None:
        report = builder.build_review(
            {
                "status": "OOS_WALKFORWARD_PASS",
                "evaluations": [candidate("orca1507", 0.2, 1.39), candidate("orca1508", 0.35, 1.31)],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            }
        )

        self.assertEqual(report["status"], "ORCA_OOS_FAMILY_REVIEW_READY")
        self.assertEqual(report["oos_pass_candidate_count"], 2)
        self.assertEqual(report["distinct_parameter_count"], 2)
        self.assertTrue(report["review_value"]["reduces_single_registered_candidate_dependency"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_when_source_order_permissions_are_not_safe(self) -> None:
        report = builder.build_review(
            {
                "status": "OOS_WALKFORWARD_PASS",
                "evaluations": [candidate("orca1507", 0.2), candidate("orca1508", 0.35)],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": True,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            }
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("source_has_no_order_permissions", report["blockers"])


if __name__ == "__main__":
    unittest.main()
