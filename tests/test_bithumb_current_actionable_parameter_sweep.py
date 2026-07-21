from __future__ import annotations

import importlib.util
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_parameter_sweep.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_parameter_sweep", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
sweep = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sweep)


class BithumbCurrentActionableParameterSweepTests(unittest.TestCase):
    def test_conversion_for_screen_can_pass_without_order_paths(self) -> None:
        conversion = sweep.conversion_for_screen(
            {
                "metrics": {
                    "cagr": 0.40,
                    "total_return": 0.25,
                    "mdd": -0.32,
                    "trade_count": 12,
                    "profit_factor": 1.6,
                }
            }
        )

        self.assertTrue(conversion["pass_like"])
        self.assertLessEqual(abs(conversion["estimated_mdd"]), sweep.TARGET_MDD_ABS)
        self.assertGreaterEqual(conversion["estimated_cagr"], sweep.MIN_ESTIMATED_CAGR)

    def test_sweep_candidate_is_research_only(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=UTC)
        candles = []
        price = 100.0
        for index in range(70):
            price *= 1.04 if index % 10 < 5 else 0.99
            candles.append(
                {
                    "timestamp": start + timedelta(days=index),
                    "open": price * 0.99,
                    "high": price * 1.04,
                    "low": price * 0.96,
                    "close": price,
                    "volume": 2.0 if index % 10 == 4 else 1.0,
                }
            )

        seed = {
            "candidate_id": "bithumb_current_actionable_bio_1d_long_freeze001",
            "lane": "bithumb_1d",
            "market": "KRW-BIO",
            "timeframe": "1d",
            "current_gate": "G03_BACKTEST_SCREEN",
        }
        rows = sweep.sweep_candidate(seed, candles)

        self.assertGreater(len(rows), 0)
        self.assertFalse(rows[0]["order_paths_allowed"])
        self.assertFalse(rows[0]["counts_as_paper_or_live_evidence"])

        scout = {
            "top_near_miss_candidates": [
                {
                    "candidate_id": "bithumb_current_actionable_bio_1d_long_freeze001_sweep0001",
                    "signal": {"momentum": -0.18},
                }
            ]
        }
        adaptive_rows = sweep.sweep_candidate(seed, candles, scout)
        adaptive_thresholds = {
            row["parameters"]["momentum_threshold"]
            for row in adaptive_rows
            if row["model_generation_source"] == "current_signal_near_miss_adaptive"
        }
        self.assertIn(-0.18, adaptive_thresholds)
        self.assertGreater(len(adaptive_rows), len(rows))

    def test_report_uses_failed_risk_candidates_and_keeps_order_permissions_false(self) -> None:
        original_read_json = sweep.read_json
        original_fetch = sweep.backtest.fetch_candles
        try:
            def fake_read_json(path, default):
                if str(path).endswith("bithumb_current_actionable_nonzero_signal_scout_latest.json"):
                    return {
                        "status": "NO_CURRENT_NONZERO_SIGNAL_FOUND",
                        "near_miss_gap_summary": {"candidate_count": 1},
                        "top_near_miss_candidates": [
                            {
                                "candidate_id": "bithumb_current_actionable_bio_1d_long_freeze001_sweep0001",
                                "signal": {"momentum": -0.18},
                            }
                        ],
                    }
                if str(path).endswith("bithumb_current_actionable_frozen_candidate_latest.json"):
                    return {
                        "candidates": [
                            {
                                "candidate_id": "bithumb_current_actionable_bio_1d_long_freeze001",
                                "lane": "bithumb_1d",
                                "market": "KRW-BIO",
                                "timeframe": "1d",
                                "current_gate": "G03_BACKTEST_SCREEN",
                            }
                        ],
                        "no_order_assertions": {
                            "promotion_allowed_by_this_report": False,
                            "paper_enabled_by_this_report": False,
                            "live_allowed_by_this_report": False,
                            "broker_submit_allowed_by_this_report": False,
                            "private_submit_allowed_by_this_report": False,
                            "real_orders_allowed_by_this_report": False,
                        },
                    }
                return {
                    "conversions": [
                        {
                            "candidate_id": "bithumb_current_actionable_bio_1d_long_freeze001",
                            "status": "RISK_CONVERSION_ITERATE",
                        }
                    ],
                    "no_order_assertions": {
                        "promotion_allowed_by_this_report": False,
                        "paper_enabled_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "broker_submit_allowed_by_this_report": False,
                        "private_submit_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                }

            sweep.read_json = fake_read_json
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
                for index in range(40)
            ]
            sweep.backtest.fetch_candles = lambda _market, _timeframe: candles
            report = sweep.build_report()
        finally:
            sweep.read_json = original_read_json
            sweep.backtest.fetch_candles = original_fetch

        self.assertEqual(report["candidate_count"], 1)
        self.assertGreater(report["sweep_count"], 0)
        self.assertGreater(report["adaptive_sweep_count"], 0)
        self.assertEqual(report["current_signal_scout_status"], "NO_CURRENT_NONZERO_SIGNAL_FOUND")
        self.assertEqual(report["current_signal_near_miss_gap_summary"]["candidate_count"], 1)
        self.assertFalse(report["no_order_assertions"]["promotion_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
