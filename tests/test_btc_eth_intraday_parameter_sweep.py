from __future__ import annotations

import importlib.util
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_parameter_sweep.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_parameter_sweep", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
sweep = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sweep)


class BtcEthIntradayParameterSweepTests(unittest.TestCase):
    def test_sweep_candidate_keeps_best_parameters_research_only(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=UTC)
        candles = []
        price = 100.0
        for index in range(100):
            price *= 1.004 if index % 12 < 7 else 0.998
            candles.append(
                {
                    "timestamp": start + timedelta(hours=index),
                    "open": price * 0.999,
                    "high": price * 1.002,
                    "low": price * 0.997,
                    "close": price,
                    "volume": 2.0 if index % 12 in {3, 4, 5} else 1.0,
                }
            )

        result = sweep.sweep_candidate(
            {
                "candidate_id": "btc_eth_intraday_momentum_eth_1h",
                "market": "KRW-ETH",
                "timeframe": "1h",
                "momentum_threshold": 0.0015,
            },
            candles,
            limit=2,
        )

        self.assertGreater(result["trials_run"], 0)
        self.assertGreater(result["trials_with_min_trades"], 0)
        self.assertIn("momentum_threshold", result["best_parameters"])
        self.assertTrue(all(row["order_paths_allowed"] is False for row in result["top_trials"]))
        self.assertTrue(all(row["counts_as_paper_or_live_evidence"] is False for row in result["top_trials"]))

    def test_report_keeps_all_order_permissions_false(self) -> None:
        original_read_json = sweep.read_json
        original_fetch = sweep.backtest.fetch_candles
        try:
            sweep.read_json = lambda _path, _default: {
                "screens": [
                    {
                        "candidate_id": "btc_eth_intraday_momentum_eth_1h",
                        "market": "KRW-ETH",
                        "timeframe": "1h",
                        "status": "BACKTEST_SCREEN_ITERATE",
                        "frozen_parameters": {"momentum_threshold": 0.0015},
                    }
                ]
            }
            start = datetime(2026, 1, 1, tzinfo=UTC)
            candles = [
                {
                    "timestamp": start + timedelta(hours=index),
                    "open": 100.0 + index,
                    "high": 101.0 + index,
                    "low": 99.0 + index,
                    "close": 100.0 + index,
                    "volume": 2.0,
                }
                for index in range(80)
            ]
            sweep.backtest.fetch_candles = lambda _market, _timeframe: candles
            report = sweep.build_report()
        finally:
            sweep.read_json = original_read_json
            sweep.backtest.fetch_candles = original_fetch

        self.assertEqual(report["status"], "SWEEP_COMPLETE")
        self.assertEqual(report["sweep_count"], 1)
        self.assertFalse(report["no_order_assertions"]["promotion_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
