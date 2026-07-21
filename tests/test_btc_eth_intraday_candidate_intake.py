from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_candidate_intake.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_candidate_intake", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
intake = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(intake)


class BtcEthIntradayCandidateIntakeTests(unittest.TestCase):
    def test_candidate_rows_are_research_only_and_rank_nearest_intraday_target(self) -> None:
        rows = intake.intraday_candidate_rows(
            {
                "intraday_1h_4h_signals": [
                    {
                        "market": "KRW-BTC",
                        "timeframe": "1h",
                        "side": "flat",
                        "target_weight": 0.0,
                        "non_flat_trigger_gap": 0.002,
                        "lookback_return": 0.001,
                        "short_return": 0.001,
                        "volume_ratio": 1.2,
                    },
                    {
                        "market": "KRW-ETH",
                        "timeframe": "1h",
                        "side": "flat",
                        "target_weight": 0.0,
                        "non_flat_trigger_gap": 0.0004,
                        "lookback_return": 0.0014,
                        "short_return": 0.001,
                        "volume_ratio": 2.0,
                    },
                    {
                        "market": "KRW-XRP",
                        "timeframe": "1h",
                        "side": "long",
                        "non_flat_trigger_gap": 0.0,
                    },
                ]
            }
        )

        self.assertEqual([row["candidate_id"] for row in rows], ["btc_eth_intraday_momentum_eth_1h", "btc_eth_intraday_momentum_btc_1h"])
        self.assertTrue(all(row["lane"] == "btc_eth_1h4h" for row in rows))
        self.assertTrue(all(row["next_gate"] == "G03_BACKTEST_SCREEN" for row in rows))
        self.assertTrue(all(row["counts_as_paper_or_live_evidence"] is False for row in rows))
        self.assertTrue(all(row["broker_submit_allowed"] is False for row in rows))
        self.assertTrue(all(row["real_orders_allowed"] is False for row in rows))

    def test_report_keeps_all_order_permissions_false(self) -> None:
        original = intake.read_json
        try:
            intake.read_json = lambda _path, _default: {
                "intraday_1h_4h_signals": [
                    {
                        "market": "KRW-ETH",
                        "timeframe": "4h",
                        "side": "flat",
                        "target_weight": 0.0,
                        "non_flat_trigger_gap": 0.003,
                    }
                ]
            }
            report = intake.build_report()
        finally:
            intake.read_json = original

        self.assertEqual(report["status"], "READY_FOR_BACKTEST_INTAKE")
        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(report["nearest_trigger_candidate"]["candidate_id"], "btc_eth_intraday_momentum_eth_4h")
        self.assertFalse(report["no_order_assertions"]["promotion_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
