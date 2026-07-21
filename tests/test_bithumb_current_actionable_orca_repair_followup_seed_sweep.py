from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_orca_repair_followup_seed_sweep.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_orca_repair_followup_seed_sweep", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
sweep = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sweep)


SAFE_ASSERTIONS = {
    "promotion_allowed_by_this_report": False,
    "paper_enabled_by_this_report": False,
    "live_allowed_by_this_report": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders_allowed_by_this_report": False,
}


class BithumbCurrentActionableOrcaRepairFollowupSeedSweepTests(unittest.TestCase):
    def source_packet(self) -> dict:
        return {
            "status": "ORCA_REPAIR_FOLLOWUP_SEED_PACKET_READY",
            "base_candidate_id": "orca_sweep1507",
            "parent_candidate_id": "orca_parent",
            "market": "KRW-ORCA",
            "timeframe": "1d",
            "no_order_assertions": dict(SAFE_ASSERTIONS),
            "proposed_seed_specs": [
                {
                    "seed_id": "followup_a",
                    "hypothesis": "test followup seed",
                    "parameters": {
                        "lookback_bars": 3,
                        "hold_bars": 2,
                        "volume_window": 10,
                        "volume_ratio_floor": 1.75,
                        "momentum_threshold": 0.05,
                        "stop_loss": 0.03,
                        "take_profit": 0.10,
                        "round_trip_cost_rate": 0.002,
                    },
                }
            ],
        }

    def test_followup_seed_sweep_reports_passing_child_without_order_permissions(self) -> None:
        with (
            patch.object(sweep.seed_sweep.repair.sweep.backtest, "fetch_candles", return_value=[{"close": 1.0}]),
            patch.object(
                sweep.seed_sweep,
                "evaluate_seed",
                return_value={
                    "seed_id": "followup_a",
                    "candidate_id": "orca_parent_followup_a",
                    "status": "OOS_CANDIDATE_PASS",
                    "source_conversion": {"estimated_cagr": 0.3, "estimated_mdd": -0.19},
                    "aggregate": {"fold_count": 3, "pass_fold_count": 2, "positive_fold_count": 2, "total_trade_count": 8},
                    "robustness": {
                        "status": "ROBUSTNESS_STRESS_PASS",
                        "case_count": 7,
                        "pass_count": 4,
                        "cost_pass_count": 1,
                    },
                },
            ),
        ):
            report = sweep.build_report(self.source_packet())

        self.assertEqual(report["status"], "ORCA_REPAIR_FOLLOWUP_SEED_SWEEP_PASS")
        self.assertEqual(report["robustness_pass_seed_count"], 1)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertEqual(report["no_order_assertions"], SAFE_ASSERTIONS)

    def test_followup_seed_sweep_iterates_when_no_seed_passes_robustness(self) -> None:
        with (
            patch.object(sweep.seed_sweep.repair.sweep.backtest, "fetch_candles", return_value=[{"close": 1.0}]),
            patch.object(
                sweep.seed_sweep,
                "evaluate_seed",
                return_value={
                    "seed_id": "followup_a",
                    "candidate_id": "orca_parent_followup_a",
                    "status": "OOS_CANDIDATE_PASS",
                    "source_conversion": {"estimated_cagr": -0.1, "estimated_mdd": -0.2},
                    "aggregate": {"fold_count": 3, "pass_fold_count": 2, "positive_fold_count": 2, "total_trade_count": 8},
                    "robustness": {
                        "status": "ROBUSTNESS_STRESS_ITERATE",
                        "case_count": 7,
                        "pass_count": 0,
                        "cost_pass_count": 0,
                    },
                },
            ),
        ):
            report = sweep.build_report(self.source_packet())

        self.assertEqual(report["status"], "ORCA_REPAIR_FOLLOWUP_SEED_SWEEP_ITERATE")
        self.assertIn("NO_ORCA_FOLLOWUP_REPAIR_SEED_ROBUSTNESS_PASS", report["blockers"])


if __name__ == "__main__":
    unittest.main()
