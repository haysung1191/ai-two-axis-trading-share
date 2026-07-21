from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_robustness_stress.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_robustness_stress", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
stress = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stress)


SAFE = {
    "promotion_allowed_by_this_report": False,
    "paper_enabled_by_this_report": False,
    "live_allowed_by_this_report": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders_allowed_by_this_report": False,
}


class BithumbCurrentActionableRobustnessStressTests(unittest.TestCase):
    def test_apply_stress_parameters_keeps_base_and_overrides_locally(self) -> None:
        base = {
            "hold_bars": 3,
            "momentum_threshold": 0.02,
            "volume_ratio_floor": 0.8,
            "stop_loss": 0.12,
            "round_trip_cost_rate": 0.002,
        }

        updated = stress.apply_stress_parameters(
            base,
            {
                "hold_bars_delta": -1,
                "momentum_threshold_multiplier": 1.25,
                "round_trip_cost_rate": 0.005,
            },
        )

        self.assertEqual(base["hold_bars"], 3)
        self.assertEqual(updated["hold_bars"], 2)
        self.assertAlmostEqual(updated["momentum_threshold"], 0.025)
        self.assertAlmostEqual(updated["round_trip_cost_rate"], 0.005)

    def test_report_keeps_order_permissions_false(self) -> None:
        original_read_json = stress.read_json
        original_fetch = stress.backtest.fetch_candles
        try:
            stress.read_json = lambda _path, _default: {
                "status": "OOS_WALKFORWARD_PASS",
                "generated_at": "2026-05-18T22:16:03+09:00",
                "top_oos": {
                    "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354",
                    "parent_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "parameters": {
                        "lookback_bars": 3,
                        "hold_bars": 3,
                        "volume_window": 5,
                        "volume_ratio_floor": 0.8,
                        "momentum_threshold": 0.01,
                        "round_trip_cost_rate": 0.002,
                        "stop_loss": 0.12,
                        "take_profit": 0.2,
                    },
                },
                "no_order_assertions": SAFE,
            }
            start = datetime(2026, 1, 1, tzinfo=UTC)
            candles = []
            price = 100.0
            for index in range(150):
                price *= 1.012 if index % 10 < 6 else 0.997
                candles.append(
                    {
                        "timestamp": start + timedelta(days=index),
                        "open": price * 0.998,
                        "high": price * 1.006,
                        "low": price * 0.994,
                        "close": price,
                        "volume": 2.0 if index % 10 in {3, 4, 5} else 1.0,
                    }
                )
            stress.backtest.fetch_candles = lambda _market, _timeframe: candles
            report = stress.build_report()
        finally:
            stress.read_json = original_read_json
            stress.backtest.fetch_candles = original_fetch

        self.assertIn(report["status"], {"ROBUSTNESS_STRESS_PASS", "ROBUSTNESS_STRESS_ITERATE"})
        self.assertEqual(report["source_oos"]["status"], "OOS_WALKFORWARD_PASS")
        self.assertEqual(report["source_oos"]["generated_at"], "2026-05-18T22:16:03+09:00")
        self.assertEqual(report["source_oos"]["top_candidate_id"], "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354")
        self.assertEqual(report["source_oos"]["top_market"], "KRW-POLA")
        self.assertEqual(report["case_count"], len(stress.STRESS_CASES))
        self.assertNotIn("gatekeeper", report["single_next_action"].lower())
        self.assertNotIn("shadow", report["single_next_action"].lower())
        self.assertIn("tiny-live precondition", report["single_next_action"].lower())
        self.assertFalse(report["no_order_assertions"]["promotion_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_write_json_atomic_replaces_with_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "stress_atomic_test.json"
            target.write_text(json.dumps({"status": "OLD"}), encoding="utf-8")

            stress.write_json_atomic(target, {"status": "NEW", "count": 1})

            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"status": "NEW", "count": 1})
            self.assertFalse(target.with_name(f".{target.name}.tmp").exists())

    def test_render_md_includes_source_oos_context(self) -> None:
        markdown = stress.render_md(
            {
                "status": "ROBUSTNESS_STRESS_PASS",
                "candidate_id": "robust1",
                "source_oos": {
                    "status": "OOS_WALKFORWARD_PASS",
                    "generated_at": "2026-05-18T22:16:03+09:00",
                    "top_candidate_id": "robust1",
                    "top_market": "KRW-ORCA",
                },
                "pass_count": 7,
                "case_count": 7,
                "cost_pass_count": 1,
                "single_next_action": "Keep this candidate in model verification for tiny-live precondition review.",
            }
        )

        self.assertIn("Source OOS: `OOS_WALKFORWARD_PASS` / `2026-05-18T22:16:03+09:00` / top `robust1` `KRW-ORCA`", markdown)


if __name__ == "__main__":
    unittest.main()
