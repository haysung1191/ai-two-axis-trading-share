from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_candidate_intake.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_candidate_intake", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
intake = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(intake)


class BithumbCurrentActionableCandidateIntakeTests(unittest.TestCase):
    def test_non_flat_multi_asset_signal_becomes_current_actionable_candidate(self) -> None:
        report = intake.build_report(
            {
                "multi_asset_1d_signals": [
                    {
                        "market": "KRW-BIO",
                        "timeframe": "1d",
                        "side": "long",
                        "target_weight": 0.02,
                        "lookback_return": 2.3,
                        "short_return": 0.8,
                        "volume_ok": True,
                        "volume_ratio": 1.3,
                        "non_flat_trigger_gap": 0.0,
                        "signal_id": "s1",
                    },
                    {
                        "market": "KRW-BTC",
                        "timeframe": "1d",
                        "side": "flat",
                        "target_weight": 0.0,
                        "lookback_return": 0.08,
                        "short_return": 0.03,
                        "volume_ok": False,
                        "volume_ratio": 0.1,
                        "non_flat_trigger_gap": 0.02,
                        "signal_id": "s2",
                    },
                ],
                "intraday_1h_4h_signals": [],
            }
        )

        self.assertEqual(report["status"], "CURRENT_ACTIONABLE_CANDIDATES_FOUND")
        self.assertEqual(report["current_actionable_count"], 1)
        self.assertEqual(report["top_current_actionable"][0]["market"], "KRW-BIO")
        self.assertTrue(report["top_current_actionable"][0]["current_actionable"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_flat_signals_remain_near_trigger_research_candidates(self) -> None:
        report = intake.build_report(
            {
                "multi_asset_1d_signals": [],
                "intraday_1h_4h_signals": [
                    {
                        "market": "KRW-BTC",
                        "timeframe": "1h",
                        "side": "flat",
                        "target_weight": 0.0,
                        "lookback_return": 0.001,
                        "short_return": 0.001,
                        "volume_ok": True,
                        "volume_ratio": 1.0,
                        "non_flat_trigger_gap": 0.0002,
                        "signal_id": "s3",
                    }
                ],
            }
        )

        self.assertEqual(report["status"], "NO_CURRENT_ACTIONABLE_CANDIDATES")
        self.assertEqual(report["current_actionable_count"], 0)
        self.assertEqual(report["near_trigger_count"], 1)
        self.assertEqual(report["top_near_trigger"][0]["market"], "KRW-BTC")


if __name__ == "__main__":
    unittest.main()
