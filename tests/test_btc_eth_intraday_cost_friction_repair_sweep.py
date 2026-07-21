from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_cost_friction_repair_sweep.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_cost_friction_repair_sweep", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
sweep = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sweep)


class BtcEthIntradayCostFrictionRepairSweepTests(unittest.TestCase):
    def spec(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": "READY_FOR_RESEARCH_SPEC_REVIEW",
            "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "market": "KRW-BTC",
            "timeframe": "4h",
            "counts_as_paper_or_live_evidence": False,
            "repair_seeds": [
                {
                    "seed_id": "costrepair_turnover_001",
                    "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001_costrepair_turnover_001",
                    "market": "KRW-BTC",
                    "timeframe": "4h",
                    "repair_mode": "lower_turnover",
                    "parameter_grid": {
                        "hold_bars": [7],
                        "volume_ratio_floor": [1.0],
                        "momentum_threshold": [0.002],
                        "stop_loss": [0.035],
                        "take_profit": [0.04],
                    },
                    "acceptance_checks": {
                        "min_cost_pass_count": 2,
                        "min_positive_fold_count": 2,
                        "min_pass_fold_count": 2,
                        "max_worst_fold_mdd": -0.22,
                        "min_total_trade_count": 45,
                    },
                }
            ],
            "no_order_assertions": dict(sweep.SAFE_ASSERTIONS),
        }
        payload.update(overrides)
        return payload

    def test_sweep_passes_with_cost_stress_passing_child_without_order_paths(self) -> None:
        result = {
            "candidate_id": "child",
            "seed_id": "costrepair_turnover_001",
            "status": "COST_FRICTION_REPAIR_SWEEP_PASS",
            "pass_count": 5,
            "cost_pass_count": 2,
            "oos_aggregate": {"average_fold_cagr": 0.2, "worst_fold_mdd": -0.1},
            "screen_metrics": {"trade_count": 50},
        }
        with patch.object(sweep.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            sweep, "evaluate_trial", return_value=result
        ):
            report = sweep.build_sweep(self.spec())

        self.assertEqual(report["status"], "COST_FRICTION_REPAIR_SWEEP_PASS")
        self.assertEqual(report["repair_pass_count"], 1)
        self.assertEqual(report["best_cost_pass_count"], 2)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_sweep_iterates_when_no_child_passes_cost_stress(self) -> None:
        result = {
            "candidate_id": "child",
            "seed_id": "costrepair_turnover_001",
            "status": "COST_FRICTION_REPAIR_SWEEP_ITERATE",
            "pass_count": 4,
            "cost_pass_count": 0,
            "oos_aggregate": {"average_fold_cagr": 0.2, "worst_fold_mdd": -0.1},
            "screen_metrics": {"trade_count": 50},
        }
        with patch.object(sweep.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            sweep, "evaluate_trial", return_value=result
        ):
            report = sweep.build_sweep(self.spec())

        self.assertEqual(report["status"], "COST_FRICTION_REPAIR_SWEEP_ITERATE")
        self.assertEqual(report["repair_pass_count"], 0)
        self.assertEqual(report["best_cost_pass_count"], 0)

    def test_blocks_unsafe_spec(self) -> None:
        report = sweep.build_sweep(self.spec(no_order_assertions={"broker_submit_allowed_by_this_report": True}))

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("SPEC_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertEqual(report["trial_count"], 0)


if __name__ == "__main__":
    unittest.main()
