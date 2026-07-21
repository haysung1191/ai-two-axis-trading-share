from __future__ import annotations

import importlib.util
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_backtest_screen.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_backtest_screen", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
screen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(screen)


class BtcEthIntradayBacktestScreenTests(unittest.TestCase):
    def test_screen_candidate_is_research_only_and_can_pass_to_oos_review(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=UTC)
        candles = []
        price = 100.0
        for index in range(90):
            price *= 1.003 if index % 18 < 10 else 0.999
            candles.append(
                {
                    "timestamp": start + timedelta(hours=index),
                    "open": price * 0.999,
                    "high": price * 1.002,
                    "low": price * 0.997,
                    "close": price,
                    "volume": 2.0 if index % 18 == 6 else 1.0,
                }
            )

        result = screen.screen_candidate(
            {
                "candidate_id": "btc_eth_intraday_momentum_eth_1h",
                "market": "KRW-ETH",
                "timeframe": "1h",
                "momentum_threshold": 0.0015,
            },
            candles,
        )

        self.assertEqual(result["status"], "BACKTEST_SCREEN_PASS")
        self.assertEqual(result["next_gate"], "G04_OOS_WALKFORWARD_RESEARCH_ONLY")
        self.assertGreaterEqual(result["metrics"]["trade_count"], 3)
        self.assertFalse(result["order_paths_allowed"])
        self.assertFalse(result["counts_as_paper_or_live_evidence"])

    def test_report_keeps_all_order_permissions_false(self) -> None:
        original_read_json = screen.read_json
        original_fetch = screen.fetch_candles
        try:
            screen.read_json = lambda _path, _default: {
                "candidates": [
                    {
                        "candidate_id": "btc_eth_intraday_momentum_eth_1h",
                        "lane": "btc_eth_1h4h",
                        "market": "KRW-ETH",
                        "timeframe": "1h",
                        "momentum_threshold": 0.5,
                        "next_gate": "G03_BACKTEST_SCREEN",
                    }
                ]
            }
            start = datetime(2026, 1, 1, tzinfo=UTC)
            candles = [
                {
                    "timestamp": start + timedelta(hours=index),
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "volume": 1.0,
                }
                for index in range(50)
            ]
            screen.fetch_candles = lambda _market, _timeframe: candles
            report = screen.build_report()
        finally:
            screen.read_json = original_read_json
            screen.fetch_candles = original_fetch

        self.assertEqual(report["status"], "BACKTEST_SCREEN_COMPLETE")
        self.assertEqual(report["screened_count"], 1)
        self.assertFalse(report["no_order_assertions"]["promotion_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
