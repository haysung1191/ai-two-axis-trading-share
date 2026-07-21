from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_family_parameter_repair_review.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_family_parameter_repair_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
repair = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repair)


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


class BithumbCurrentActionableFamilyParameterRepairReviewTests(unittest.TestCase):
    def test_repairs_non_orca_family_parameters_without_order_paths(self) -> None:
        frozen = {
            **SAFE,
            "candidates": [
                {
                    "candidate_id": "virtual",
                    "parent_candidate_id": "virtual_parent",
                    "market": "KRW-VIRTUAL",
                    "timeframe": "1d",
                    "frozen_parameters": {"lookback_bars": 3},
                }
            ],
        }
        risk = {
            **SAFE,
            "conversions": [
                {
                    "candidate_id": "virtual",
                    "parent_candidate_id": "virtual_parent",
                    "market": "KRW-VIRTUAL",
                    "timeframe": "1d",
                    "status": "RISK_CONVERSION_PASS",
                }
            ],
        }
        current_oos = {**SAFE, "parent_candidate_id": "orca_parent", "market": "KRW-ORCA"}
        sweep_row = {
            "candidate_id": "virtual_sweep0001",
            "parent_candidate_id": "virtual",
            "market": "KRW-VIRTUAL",
            "timeframe": "1d",
            "status": "PARAMETER_SWEEP_PASS",
            "parameters": {"lookback_bars": 5},
            "conversion": {"estimated_cagr": 0.5, "source_profit_factor": 2.0, "source_mdd": -0.2},
        }

        with patch.object(repair.sweep.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            repair.sweep, "sweep_candidate", return_value=[sweep_row]
        ), patch.object(repair.oos, "evaluate_candidate") as evaluate_candidate, patch.object(
            repair, "robustness_summary"
        ) as robustness_summary:
            evaluate_candidate.return_value = {
                "candidate_id": "virtual_sweep0001",
                "market": "KRW-VIRTUAL",
                "status": "OOS_CANDIDATE_PASS",
                "aggregate": {
                    "fold_count": 3,
                    "pass_fold_count": 2,
                    "positive_fold_count": 2,
                    "worst_fold_mdd": -0.1,
                    "average_fold_cagr": 0.4,
                    "total_trade_count": 8,
                },
                "source_conversion": {"estimated_cagr": 0.5},
            }
            robustness_summary.return_value = {
                "status": "ROBUSTNESS_STRESS_PASS",
                "case_count": 7,
                "pass_count": 4,
                "cost_pass_count": 1,
                "cases": [],
            }
            report = repair.build_report(frozen=frozen, risk=risk, current_oos=current_oos)

        self.assertEqual(report["status"], "FAMILY_PARAMETER_REPAIR_ROBUSTNESS_PASS")
        self.assertEqual(report["seed_candidate_count"], 1)
        self.assertEqual(report["evaluated_trial_count"], 1)
        self.assertEqual(report["oos_pass_candidate_count"], 1)
        self.assertEqual(report["robustness_pass_candidate_count"], 1)
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_uses_expanded_trial_window_per_family(self) -> None:
        frozen = {
            **SAFE,
            "candidates": [
                {
                    "candidate_id": "virtual",
                    "parent_candidate_id": "virtual_parent",
                    "market": "KRW-VIRTUAL",
                    "timeframe": "1d",
                    "frozen_parameters": {"lookback_bars": 3},
                }
            ],
        }
        risk = {
            **SAFE,
            "conversions": [
                {
                    "candidate_id": "virtual",
                    "parent_candidate_id": "virtual_parent",
                    "market": "KRW-VIRTUAL",
                    "timeframe": "1d",
                    "status": "RISK_CONVERSION_PASS",
                }
            ],
        }
        current_oos = {**SAFE, "parent_candidate_id": "orca_parent", "market": "KRW-ORCA"}
        sweep_rows = [
            {
                "candidate_id": f"virtual_sweep{i:04d}",
                "parent_candidate_id": "virtual",
                "market": "KRW-VIRTUAL",
                "timeframe": "1d",
                "status": "PARAMETER_SWEEP_PASS",
                "parameters": {"lookback_bars": i},
                "conversion": {
                    "estimated_cagr": 1.0 - (i * 0.01),
                    "source_profit_factor": 2.0,
                    "source_mdd": -0.2,
                },
            }
            for i in range(20)
        ]

        with patch.object(repair.sweep.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            repair.sweep, "sweep_candidate", return_value=sweep_rows
        ), patch.object(repair.oos, "evaluate_candidate") as evaluate_candidate:
            evaluate_candidate.side_effect = [
                {
                    "candidate_id": row["candidate_id"],
                    "market": "KRW-VIRTUAL",
                    "status": "OOS_CANDIDATE_ITERATE",
                    "aggregate": {},
                }
                for row in sweep_rows[: repair.MAX_TRIALS_PER_FAMILY]
            ]
            report = repair.build_report(frozen=frozen, risk=risk, current_oos=current_oos)

        self.assertEqual(repair.MAX_TRIALS_PER_FAMILY, 12)
        self.assertEqual(report["evaluated_trial_count"], 12)
        self.assertEqual(evaluate_candidate.call_count, 12)

    def test_includes_positive_repair_potential_seed_that_is_not_full_risk_pass(self) -> None:
        frozen = {
            **SAFE,
            "candidates": [
                {
                    "candidate_id": "risk_pass",
                    "parent_candidate_id": "risk_pass_parent",
                    "market": "KRW-PASS",
                    "timeframe": "1d",
                    "frozen_parameters": {"lookback_bars": 3},
                },
                {
                    "candidate_id": "near_pass",
                    "parent_candidate_id": "near_pass_parent",
                    "market": "KRW-NEAR",
                    "timeframe": "1d",
                    "frozen_parameters": {"lookback_bars": 4},
                },
            ],
        }
        risk = {
            **SAFE,
            "conversions": [
                {
                    "candidate_id": "risk_pass",
                    "status": "RISK_CONVERSION_PASS",
                    "conversion": {
                        "estimated_cagr": 0.50,
                        "source_profit_factor": 2.0,
                        "source_trade_count": 12,
                        "recommended_exposure_cap": 0.50,
                    },
                },
                {
                    "candidate_id": "near_pass",
                    "status": "RISK_CONVERSION_ITERATE",
                    "conversion": {
                        "estimated_cagr": 0.12,
                        "source_profit_factor": 1.5,
                        "source_trade_count": 10,
                        "recommended_exposure_cap": 0.40,
                    },
                },
            ],
        }
        current_oos = {**SAFE, "parent_candidate_id": "orca_parent", "market": "KRW-ORCA"}

        seeds = repair.repair_seed_candidates(frozen, risk, current_oos)

        self.assertEqual([row["candidate_id"] for row in seeds], ["risk_pass", "near_pass"])

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

        report = repair.build_report(frozen=unsafe, risk=SAFE, current_oos=SAFE)

        self.assertEqual(report["status"], "BLOCKED_UNSAFE_SOURCE_PACKET")
        self.assertIn("SOURCE_PACKET_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertEqual(report["evaluated_trial_count"], 0)

    def test_expands_non_orca_repair_trials_per_family(self) -> None:
        frozen = {
            **SAFE,
            "candidates": [
                {
                    "candidate_id": "pola",
                    "parent_candidate_id": "pola_parent",
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                },
                {
                    "candidate_id": "bio",
                    "parent_candidate_id": "bio_parent",
                    "market": "KRW-BIO",
                    "timeframe": "1d",
                },
            ],
        }
        risk = {
            **SAFE,
            "conversions": [
                {"candidate_id": "pola", "status": "RISK_CONVERSION_PASS"},
                {"candidate_id": "bio", "status": "RISK_CONVERSION_PASS"},
            ],
        }
        current_oos = {**SAFE, "parent_candidate_id": "orca_parent", "market": "KRW-ORCA"}

        def fake_sweep(seed, candles):
            return [
                {
                    "candidate_id": f"{seed['candidate_id']}_sweep{i:04d}",
                    "parent_candidate_id": seed["candidate_id"],
                    "market": seed["market"],
                    "timeframe": "1d",
                    "status": "PARAMETER_SWEEP_PASS",
                    "conversion": {
                        "estimated_cagr": 1.0 - (i * 0.01),
                        "source_profit_factor": 2.0,
                        "source_mdd": -0.2,
                    },
                }
                for i in range(20)
            ]

        def fake_evaluate(candidate, candle_cache):
            return {
                "candidate_id": candidate["candidate_id"],
                "market": candidate["market"],
                "status": "OOS_CANDIDATE_ITERATE",
                "aggregate": {"fold_count": 3, "pass_fold_count": 1},
            }

        with patch.object(repair.sweep.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            repair.sweep, "sweep_candidate", side_effect=fake_sweep
        ), patch.object(repair.oos, "evaluate_candidate", side_effect=fake_evaluate):
            report = repair.build_report(frozen=frozen, risk=risk, current_oos=current_oos)

        self.assertEqual(repair.MAX_TRIALS_PER_FAMILY, 12)
        self.assertEqual(report["seed_candidate_count"], 2)
        self.assertEqual(report["evaluated_trial_count"], 24)


if __name__ == "__main__":
    unittest.main()
