from __future__ import annotations

import importlib.util
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_backtest_screen.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_backtest_screen", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
screen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(screen)


class BithumbCurrentActionableBacktestScreenTests(unittest.TestCase):
    def test_current_actionable_1d_candidate_can_pass_to_oos_review(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=UTC)
        candles = []
        price = 100.0
        for index in range(80):
            price *= 1.035 if index % 12 < 7 else 0.995
            candles.append(
                {
                    "timestamp": start + timedelta(days=index),
                    "open": price * 0.99,
                    "high": price * 1.03,
                    "low": price * 0.97,
                    "close": price,
                    "volume": 2.0 if index % 12 == 5 else 1.0,
                }
            )

        result = screen.screen_candidate(
            {
                "candidate_id": "bithumb_current_actionable_bio_1d_long_freeze001",
                "parent_candidate_id": "bithumb_current_actionable_bio_1d_long",
                "lane": "bithumb_1d",
                "market": "KRW-BIO",
                "timeframe": "1d",
                "frozen_parameters": {"momentum_threshold": 0.02},
                "source_signal_id": "sig-1",
            },
            candles,
        )

        self.assertEqual(result["status"], "BACKTEST_SCREEN_PASS")
        self.assertEqual(result["next_gate"], "G04_OOS_WALKFORWARD_RESEARCH_ONLY")
        self.assertGreaterEqual(result["metrics"]["trade_count"], 3)
        self.assertFalse(result["order_paths_allowed"])
        self.assertFalse(result["counts_as_paper_or_live_evidence"])

    def test_report_uses_only_frozen_bithumb_rows_and_keeps_order_permissions_false(self) -> None:
        original_read_json = screen.read_json
        original_fetch = screen.fetch_candles
        try:
            screen.read_json = lambda _path, _default: {
                "candidates": [
                    {
                        "candidate_id": "bithumb_current_actionable_bio_1d_long_freeze001",
                        "parent_candidate_id": "bithumb_current_actionable_bio_1d_long",
                        "lane": "bithumb_1d",
                        "current_gate": "G03_BACKTEST_SCREEN",
                        "market": "KRW-BIO",
                        "timeframe": "1d",
                        "frozen_parameters": {"momentum_threshold": 0.5},
                    },
                    {
                        "candidate_id": "bithumb_current_actionable_btc_1h_flat",
                        "lane": "btc_eth_1h4h",
                        "current_gate": "G03_BACKTEST_SCREEN",
                        "market": "KRW-BTC",
                        "timeframe": "1h",
                    },
                ]
            }
            start = datetime(2026, 1, 1, tzinfo=UTC)
            candles = [
                {
                    "timestamp": start + timedelta(days=index),
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
        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(report["screened_count"], 1)
        self.assertFalse(report["no_order_assertions"]["promotion_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
