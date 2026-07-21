from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_robustness_stress.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_robustness_stress", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
stress = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stress)


class BtcEthIntradayRobustnessStressTests(unittest.TestCase):
    def safe_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def oos_packet(self) -> dict[str, object]:
        return {
            "status": "OOS_WALKFORWARD_PASS",
            "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "market": "KRW-BTC",
            "timeframe": "4h",
            "frozen_parameters": {"lookback_bars": 3, "hold_bars": 6},
            "no_order_assertions": self.safe_assertions(),
        }

    def test_report_passes_with_no_order_assertions_and_cost_case(self) -> None:
        pass_case = {
            "case_id": "base_recheck",
            "status": "STRESS_PASS",
            "full_window_metrics": {"total_return": 0.03, "mdd": -0.10, "trade_count": 20},
            "fold_aggregate": {"pass_fold_count": 2, "positive_fold_count": 2},
        }

        def fake_evaluate_case(candidate, candles, case):
            row = dict(pass_case)
            row["case_id"] = case["case_id"]
            return row

        with patch.object(stress.backtest, "fetch_candles", return_value=[{"close": 1.0}]), patch.object(
            stress,
            "evaluate_case",
            side_effect=fake_evaluate_case,
        ):
            report = stress.build_report(self.oos_packet())

        self.assertEqual(report["status"], "ROBUSTNESS_STRESS_PASS")
        self.assertEqual(report["case_count"], len(stress.STRESS_CASES))
        self.assertEqual(report["cost_pass_count"], 2)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_unsafe_oos_packet(self) -> None:
        packet = self.oos_packet()
        packet["no_order_assertions"] = {"broker_submit_allowed_by_this_report": True}

        report = stress.build_report(packet)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("OOS_PACKET_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertEqual(report["case_count"], 0)


if __name__ == "__main__":
    unittest.main()
