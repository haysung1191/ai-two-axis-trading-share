from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_low_turnover_rebuild_followup_sweep.py")
SPEC = importlib.util.spec_from_file_location(
    "build_btc_eth_intraday_low_turnover_rebuild_followup_sweep",
    MODULE_PATH,
)
assert SPEC is not None
assert SPEC.loader is not None
sweep = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sweep)


SAFE_PACKET_ASSERTIONS = {
    "promotion_allowed_by_this_packet": False,
    "shadow_registration_allowed_by_this_packet": False,
    "paper_enabled_by_this_packet": False,
    "live_allowed_by_this_packet": False,
    "broker_submit_allowed_by_this_packet": False,
    "private_submit_allowed_by_this_packet": False,
    "real_orders_allowed_by_this_packet": False,
}


class BtcEthIntradayLowTurnoverRebuildFollowupSweepTests(unittest.TestCase):
    def packet(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
            "candidate_id": "child080",
            "parent_candidate_id": "parent001",
            "evidence_summary": {"market": "KRW-BTC", "timeframe": "4h"},
            "parameters": {
                "lookback_bars": 3,
                "hold_bars": 10,
                "volume_window": 20,
                "volume_ratio_floor": 1.3,
                "momentum_threshold": 0.0037,
                "stop_loss": 0.035,
                "take_profit": 0.09,
            },
            "no_order_assertions": SAFE_PACKET_ASSERTIONS,
        }
        payload.update(overrides)
        return payload

    def test_followup_grid_expands_around_seed_parameters(self) -> None:
        rows = sweep.followup_grid(self.packet())

        self.assertEqual(len(rows), 972)
        self.assertIn(
            {
                "lookback_bars": 3,
                "hold_bars": 10,
                "volume_window": 20,
                "volume_ratio_floor": 1.3,
                "momentum_threshold": 0.0037,
                "stop_loss": 0.035,
                "take_profit": 0.09,
                "round_trip_cost_rate": sweep.backtest.ROUND_TRIP_COST_RATE,
            },
            rows,
        )

    def test_sweep_passes_with_followup_sibling_without_order_paths(self) -> None:
        result = {
            "candidate_id": "sibling",
            "status": "LOW_TURNOVER_FOLLOWUP_SWEEP_PASS",
            "pass_count": 6,
            "cost_pass_count": 2,
            "oos_aggregate": {"average_fold_cagr": 0.2, "worst_fold_mdd": -0.1},
            "screen_metrics": {"trade_count": 50},
        }
        with patch.object(sweep.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            sweep, "followup_grid", return_value=[{"lookback_bars": 3}]
        ), patch.object(sweep, "evaluate_trial", return_value=result):
            report = sweep.build_sweep(self.packet())

        self.assertEqual(report["status"], "LOW_TURNOVER_FOLLOWUP_SWEEP_PASS")
        self.assertEqual(report["followup_pass_count"], 1)
        self.assertEqual(report["best_cost_pass_count"], 2)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_sweep_iterates_when_no_sibling_cost_passes(self) -> None:
        result = {
            "candidate_id": "sibling",
            "status": "LOW_TURNOVER_FOLLOWUP_SWEEP_ITERATE",
            "pass_count": 4,
            "cost_pass_count": 0,
            "oos_aggregate": {"average_fold_cagr": 0.2, "worst_fold_mdd": -0.1},
            "screen_metrics": {"trade_count": 50},
        }
        with patch.object(sweep.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            sweep, "followup_grid", return_value=[{"lookback_bars": 3}]
        ), patch.object(sweep, "evaluate_trial", return_value=result):
            report = sweep.build_sweep(self.packet())

        self.assertEqual(report["status"], "LOW_TURNOVER_FOLLOWUP_SWEEP_ITERATE")
        self.assertEqual(report["followup_pass_count"], 0)
        self.assertEqual(report["best_cost_pass_count"], 0)

    def test_blocks_unsafe_packet(self) -> None:
        report = sweep.build_sweep(
            self.packet(no_order_assertions={**SAFE_PACKET_ASSERTIONS, "broker_submit_allowed_by_this_packet": True})
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("PACKET_ORDER_PATH_NOT_SAFE", report["blockers"])


if __name__ == "__main__":
    unittest.main()
