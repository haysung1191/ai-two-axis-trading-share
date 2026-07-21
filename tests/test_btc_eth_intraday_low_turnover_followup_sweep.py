from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_low_turnover_followup_sweep.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_low_turnover_followup_sweep", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
followup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(followup)


class BtcEthIntradayLowTurnoverFollowupSweepTests(unittest.TestCase):
    def packet(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
            "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001_volatility_filtered_momentum_sweep080",
            "parent_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "evidence_summary": {
                "market": "KRW-BTC",
                "timeframe": "4h",
                "best_target_id": "volatility_filtered_momentum",
                "best_entry_signal_family": "volatility_expansion_momentum",
                "counts_as_paper_or_live_evidence": False,
            },
            "parameters": {
                "lookback_bars": 3,
                "hold_bars": 10,
                "volume_window": 20,
                "volume_ratio_floor": 1.3,
                "momentum_threshold": 0.0037,
                "stop_loss": 0.035,
                "take_profit": 0.09,
                "round_trip_cost_rate": 0.002,
            },
            "no_order_assertions": {
                "promotion_allowed_by_this_packet": False,
                "shadow_registration_allowed_by_this_packet": False,
                "paper_enabled_by_this_packet": False,
                "live_allowed_by_this_packet": False,
                "broker_submit_allowed_by_this_packet": False,
                "private_submit_allowed_by_this_packet": False,
                "real_orders_allowed_by_this_packet": False,
            },
        }
        payload.update(overrides)
        return payload

    def test_expands_nearby_grid_and_marks_base_parameter_match(self) -> None:
        rows = followup.expand_followup_trials(self.packet())

        self.assertEqual(len(rows), 648)
        self.assertEqual(sum(1 for row in rows if row["is_base_parameter_match"]), 1)
        self.assertEqual(rows[0]["target_id"], "volatility_filtered_momentum")
        self.assertEqual(rows[0]["entry_signal_family"], "volatility_expansion_momentum")
        self.assertFalse(rows[0]["parameters"].get("broker_submit_allowed", False))

    def test_passes_when_followup_has_sibling_passes_without_order_paths(self) -> None:
        result = {
            "candidate_id": "child_followup123",
            "status": "LOW_TURNOVER_FOLLOWUP_SWEEP_PASS",
            "is_base_parameter_match": False,
            "pass_count": 6,
            "cost_pass_count": 2,
            "oos_aggregate": {"average_fold_cagr": 0.2, "worst_fold_mdd": -0.1},
            "screen_metrics": {"trade_count": 50},
        }
        with patch.object(followup.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            followup, "expand_followup_trials", return_value=[{"parameters": {}, "is_base_parameter_match": False}]
        ), patch.object(followup, "evaluate_trial", return_value=result):
            report = followup.build_sweep(self.packet())

        self.assertEqual(report["status"], "LOW_TURNOVER_FOLLOWUP_SWEEP_PASS")
        self.assertEqual(report["followup_pass_count"], 1)
        self.assertEqual(report["sibling_pass_count"], 1)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_marks_fragile_when_only_base_parameter_passes(self) -> None:
        result = {
            "candidate_id": "child_followup010",
            "status": "LOW_TURNOVER_FOLLOWUP_SWEEP_PASS",
            "is_base_parameter_match": True,
            "pass_count": 6,
            "cost_pass_count": 2,
            "oos_aggregate": {"average_fold_cagr": 0.2, "worst_fold_mdd": -0.1},
            "screen_metrics": {"trade_count": 50},
        }
        with patch.object(followup.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            followup, "expand_followup_trials", return_value=[{"parameters": {}, "is_base_parameter_match": True}]
        ), patch.object(followup, "evaluate_trial", return_value=result):
            report = followup.build_sweep(self.packet())

        self.assertEqual(report["status"], "LOW_TURNOVER_FOLLOWUP_SWEEP_FRAGILE")
        self.assertEqual(report["followup_pass_count"], 1)
        self.assertEqual(report["sibling_pass_count"], 0)

    def test_blocks_unsafe_packet(self) -> None:
        packet = self.packet(
            no_order_assertions={
                "promotion_allowed_by_this_packet": False,
                "shadow_registration_allowed_by_this_packet": False,
                "paper_enabled_by_this_packet": False,
                "live_allowed_by_this_packet": False,
                "broker_submit_allowed_by_this_packet": True,
                "private_submit_allowed_by_this_packet": False,
                "real_orders_allowed_by_this_packet": False,
            }
        )

        report = followup.build_sweep(packet)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("LOW_TURNOVER_REBUILD_PACKET_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertEqual(report["trial_count"], 0)


if __name__ == "__main__":
    unittest.main()
