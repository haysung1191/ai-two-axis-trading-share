from __future__ import annotations

import importlib.util
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_oos_walkforward.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_oos_walkforward", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
oos = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oos)


class BtcEthIntradayOosWalkForwardTests(unittest.TestCase):
    def test_split_validation_windows_keeps_chronological_folds(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=UTC)
        candles = [{"timestamp": start + timedelta(hours=4 * index)} for index in range(9)]

        folds = oos.split_validation_windows(candles, folds=3)

        self.assertEqual(len(folds), 3)
        self.assertEqual(folds[0][0]["timestamp"], candles[0]["timestamp"])
        self.assertEqual(folds[1][0]["timestamp"], candles[3]["timestamp"])
        self.assertEqual(folds[2][-1]["timestamp"], candles[-1]["timestamp"])

    def test_report_keeps_order_permissions_false(self) -> None:
        original_read_json = oos.read_json
        original_fetch = oos.backtest.fetch_candles
        try:
            oos.read_json = lambda _path, _default: {
                "status": "READY_FOR_OOS_RESEARCH_REVIEW",
                "frozen_candidate_count": 1,
                "candidate": {
                    "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                    "market": "KRW-BTC",
                    "timeframe": "4h",
                    "frozen_parameters": {
                        "lookback_bars": 3,
                        "hold_bars": 6,
                        "volume_window": 18,
                        "volume_ratio_floor": 1.0,
                        "momentum_threshold": 0.002,
                        "round_trip_cost_rate": 0.002,
                        "stop_loss": 0.035,
                        "take_profit": 0.03,
                    },
                },
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            }
            start = datetime(2026, 1, 1, tzinfo=UTC)
            candles = []
            price = 100.0
            for index in range(120):
                price *= 1.004 if index % 12 < 7 else 0.998
                candles.append(
                    {
                        "timestamp": start + timedelta(hours=4 * index),
                        "open": price * 0.999,
                        "high": price * 1.002,
                        "low": price * 0.997,
                        "close": price,
                        "volume": 2.0 if index % 12 in {3, 4, 5} else 1.0,
                    }
                )
            oos.backtest.fetch_candles = lambda _market, _timeframe: candles
            report = oos.build_report()
        finally:
            oos.read_json = original_read_json
            oos.backtest.fetch_candles = original_fetch

        self.assertIn(report["status"], {"OOS_WALKFORWARD_PASS", "OOS_WALKFORWARD_ITERATE"})
        self.assertEqual(report["aggregate"]["fold_count"], 3)
        self.assertFalse(report["no_order_assertions"]["promotion_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
