from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_bithumb_non_orca_family_widened_repair_sweep.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_non_orca_family_widened_repair_sweep", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
sweep = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sweep)


class BithumbNonOrcaFamilyWidenedRepairSweepTests(unittest.TestCase):
    def source_spec(self) -> dict:
        return {
            "status": "READY_FOR_RESEARCH_SPEC_REVIEW",
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": dict(sweep.SAFE_ASSERTIONS),
            "repair_targets": [
                {
                    "candidate_id": "pola",
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "base_parameters": {
                        "lookback_bars": 3,
                        "hold_bars": 7,
                        "volume_window": 20,
                        "volume_ratio_floor": 1.0,
                        "momentum_threshold": 0.02,
                        "round_trip_cost_rate": 0.002,
                        "stop_loss": 0.12,
                        "take_profit": 0.35,
                    },
                    "parameter_grid": {
                        "lookback_bars": [2],
                        "volume_window": [10],
                        "volume_ratio_floor": [0.8],
                        "momentum_threshold": [0.01],
                        "hold_bars": [7],
                        "stop_loss": [0.12],
                        "take_profit": [0.35],
                    },
                }
            ],
        }

    def test_widened_sweep_reports_passing_child_without_order_permissions(self) -> None:
        with (
            patch.object(sweep.repair.sweep.backtest, "fetch_candles", return_value=[{"close": 1.0}]),
            patch.object(
                sweep.repair,
                "screen_and_oos_trial",
                return_value={
                    "candidate_id": "pola_widenedrepair_001",
                    "parent_candidate_id": "pola",
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "status": "OOS_CANDIDATE_PASS",
                    "source_conversion": {"estimated_cagr": 0.4, "estimated_mdd": -0.19},
                    "aggregate": {"fold_count": 3, "pass_fold_count": 2, "positive_fold_count": 2, "total_trade_count": 9},
                },
            ),
            patch.object(
                sweep.repair,
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
            report = sweep.build_report(self.source_spec())

        self.assertEqual(report["status"], "NON_ORCA_WIDENED_REPAIR_SWEEP_PASS")
        self.assertEqual(report["trial_count"], 1)
        self.assertEqual(report["robustness_pass_trial_count"], 1)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertEqual(report["no_order_assertions"], sweep.SAFE_ASSERTIONS)

    def test_widened_sweep_iterates_without_robustness_pass(self) -> None:
        with (
            patch.object(sweep.repair.sweep.backtest, "fetch_candles", return_value=[{"close": 1.0}]),
            patch.object(
                sweep.repair,
                "screen_and_oos_trial",
                return_value={
                    "candidate_id": "pola_widenedrepair_001",
                    "status": "OOS_CANDIDATE_PASS",
                    "source_conversion": {"estimated_cagr": 0.2, "estimated_mdd": -0.2},
                    "aggregate": {"fold_count": 3, "pass_fold_count": 2, "positive_fold_count": 2, "total_trade_count": 9},
                },
            ),
            patch.object(
                sweep.repair,
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
            report = sweep.build_report(self.source_spec())

        self.assertEqual(report["status"], "NON_ORCA_WIDENED_REPAIR_SWEEP_ITERATE")
        self.assertIn("NO_NON_ORCA_WIDENED_REPAIR_ROBUSTNESS_PASS", report["blockers"])

    def test_widened_sweep_blocks_unsafe_source_spec(self) -> None:
        source = self.source_spec()
        source["no_order_assertions"]["broker_submit_allowed_by_this_report"] = True

        report = sweep.build_report(source)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("SOURCE_SPEC_ORDER_PATH_NOT_SAFE", report["blockers"])


if __name__ == "__main__":
    unittest.main()
