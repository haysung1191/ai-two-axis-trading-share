from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_low_turnover_signal_rebuild_sweep.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_low_turnover_signal_rebuild_sweep", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
sweep = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sweep)


class BtcEthIntradayLowTurnoverSignalRebuildSweepTests(unittest.TestCase):
    def spec(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": "READY_FOR_RESEARCH_SPEC_REVIEW",
            "base_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "market": "KRW-BTC",
            "timeframe": "4h",
            "counts_as_paper_or_live_evidence": False,
            "rebuild_targets": [
                {
                    "target_id": "low_turnover_trend_confirmation",
                    "signal_grid": {
                        "entry_signal_family": ["trend_confirmation_breakout"],
                        "confirmation_window": [3],
                        "min_trend_slope": [0.0025],
                        "cooldown_bars_after_exit": [2],
                    },
                }
            ],
            "acceptance_checks": {
                "min_cost_pass_count": 2,
                "min_positive_fold_count": 2,
                "min_pass_fold_count": 2,
                "max_worst_fold_mdd": -0.22,
                "min_total_trade_count": 45,
            },
            "no_order_assertions": dict(sweep.SAFE_ASSERTIONS),
        }
        payload.update(overrides)
        return payload

    def test_expands_low_turnover_target_into_existing_backtest_parameters(self) -> None:
        target = self.spec()["rebuild_targets"][0]  # type: ignore[index]

        rows = sweep.expand_target(target)  # type: ignore[arg-type]

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["target_id"], "low_turnover_trend_confirmation")
        self.assertEqual(rows[0]["entry_signal_family"], "trend_confirmation_breakout")
        self.assertEqual(rows[0]["backtest_parameters"]["lookback_bars"], 3)
        self.assertEqual(rows[0]["backtest_parameters"]["hold_bars"], 8)
        self.assertEqual(rows[0]["backtest_parameters"]["momentum_threshold"], 0.0025)
        self.assertFalse(rows[0]["backtest_parameters"].get("broker_submit_allowed", False))

    def test_sweep_passes_with_cost_stress_passing_child_without_order_paths(self) -> None:
        result = {
            "candidate_id": "child",
            "target_id": "low_turnover_trend_confirmation",
            "entry_signal_family": "trend_confirmation_breakout",
            "status": "LOW_TURNOVER_SIGNAL_REBUILD_SWEEP_PASS",
            "pass_count": 5,
            "cost_pass_count": 2,
            "oos_aggregate": {"average_fold_cagr": 0.2, "worst_fold_mdd": -0.1},
            "screen_metrics": {"trade_count": 50},
        }
        with patch.object(sweep.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            sweep, "evaluate_trial", return_value=result
        ):
            report = sweep.build_sweep(self.spec())

        self.assertEqual(report["status"], "LOW_TURNOVER_SIGNAL_REBUILD_SWEEP_PASS")
        self.assertEqual(report["rebuild_pass_count"], 1)
        self.assertEqual(report["best_cost_pass_count"], 2)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["private_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_sweep_iterates_when_no_child_passes_cost_stress(self) -> None:
        result = {
            "candidate_id": "child",
            "target_id": "low_turnover_trend_confirmation",
            "entry_signal_family": "trend_confirmation_breakout",
            "status": "LOW_TURNOVER_SIGNAL_REBUILD_SWEEP_ITERATE",
            "pass_count": 4,
            "cost_pass_count": 0,
            "oos_aggregate": {"average_fold_cagr": 0.2, "worst_fold_mdd": -0.1},
            "screen_metrics": {"trade_count": 50},
        }
        with patch.object(sweep.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            sweep, "evaluate_trial", return_value=result
        ):
            report = sweep.build_sweep(self.spec())

        self.assertEqual(report["status"], "LOW_TURNOVER_SIGNAL_REBUILD_SWEEP_ITERATE")
        self.assertEqual(report["rebuild_pass_count"], 0)
        self.assertEqual(report["best_cost_pass_count"], 0)

    def test_blocks_unsafe_spec(self) -> None:
        report = sweep.build_sweep(self.spec(no_order_assertions={"broker_submit_allowed_by_this_report": True}))

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("SPEC_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertEqual(report["trial_count"], 1)
        self.assertEqual(report["evaluated_oos_pass_trial_count"], 0)


if __name__ == "__main__":
    unittest.main()
