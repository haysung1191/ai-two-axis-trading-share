from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_oos_walkforward.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_oos_walkforward", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
oos = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oos)


class BithumbCurrentActionableOosWalkForwardTests(unittest.TestCase):
    def test_split_validation_windows_keeps_chronological_folds(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=UTC)
        candles = [{"timestamp": start + timedelta(days=index)} for index in range(10)]

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
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "top_sweep": {
                    "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep3956",
                    "parent_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "status": "PARAMETER_SWEEP_PASS",
                    "parameters": {
                        "lookback_bars": 3,
                        "hold_bars": 3,
                        "volume_window": 5,
                        "volume_ratio_floor": 0.8,
                        "momentum_threshold": 0.01,
                        "round_trip_cost_rate": 0.002,
                        "stop_loss": 0.12,
                        "take_profit": 0.35,
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
                price *= 1.012 if index % 9 < 5 else 0.996
                candles.append(
                    {
                        "timestamp": start + timedelta(days=index),
                        "open": price * 0.998,
                        "high": price * 1.006,
                        "low": price * 0.994,
                        "close": price,
                        "volume": 2.0 if index % 9 in {3, 4, 5} else 1.0,
                    }
                )
            oos.backtest.fetch_candles = lambda _market, _timeframe: candles
            report = oos.build_report()
        finally:
            oos.read_json = original_read_json
            oos.backtest.fetch_candles = original_fetch

        self.assertIn(report["status"], {"OOS_WALKFORWARD_PASS", "OOS_WALKFORWARD_ITERATE"})
        self.assertEqual(report["aggregate"]["fold_count"], 3)
        if report["aggregate"]["pass_count"]:
            self.assertEqual(report["top_oos"]["status"], "OOS_CANDIDATE_PASS")
            self.assertEqual(report["top_oos"]["candidate_id"], "bithumb_current_actionable_pola_1d_long_freeze001_sweep3956")
        self.assertNotIn("shadow", report["single_next_action"].lower())
        self.assertIn("model verification", report["single_next_action"].lower())
        self.assertFalse(report["no_order_assertions"]["promotion_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

        markdown = oos.render_md(report)
        self.assertIn("Top OOS:", markdown)

    def test_write_json_atomic_replaces_with_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "oos_atomic_test.json"
            target.write_text(json.dumps({"status": "OLD"}), encoding="utf-8")

            oos.write_json_atomic(target, {"status": "NEW", "count": 1})

            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"status": "NEW", "count": 1})
            self.assertFalse(target.with_name(f".{target.name}.tmp").exists())


if __name__ == "__main__":
    unittest.main()
