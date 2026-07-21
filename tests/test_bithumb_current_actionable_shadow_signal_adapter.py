from __future__ import annotations

import importlib.util
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_shadow_signal_adapter.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_shadow_signal_adapter", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


CANDIDATE_ID = "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354"


def registry() -> dict:
    return {
        "records": [
            {
                "candidate_id": CANDIDATE_ID,
                "lane": "bithumb_1d",
                "market": "KRW-POLA",
                "timeframe": "1d",
                "status": "SHADOW_REVIEW_REGISTERED",
                "recommended_exposure_cap": 0.86,
            }
        ]
    }


def oos() -> dict:
    return {
        "candidate_id": CANDIDATE_ID,
        "parameters": {
            "lookback_bars": 3,
            "hold_bars": 3,
            "volume_window": 3,
            "volume_ratio_floor": 0.8,
            "momentum_threshold": 0.02,
        },
    }


def candles(trigger: bool) -> list[dict]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    rows = []
    prices = [100.0, 101.0, 102.0, 103.0, 106.0 if trigger else 102.5]
    volumes = [100.0, 100.0, 100.0, 100.0, 130.0]
    for index, (price, volume) in enumerate(zip(prices, volumes)):
        rows.append(
            {
                "timestamp": start + timedelta(days=index),
                "open": price,
                "high": price * 1.01,
                "low": price * 0.99,
                "close": price,
                "volume": volume,
            }
        )
    return rows


class BithumbCurrentActionableShadowSignalAdapterTests(unittest.TestCase):
    def test_builds_triggered_shadow_observation_without_order_paths(self) -> None:
        report = adapter.build_report(registry(), oos(), candles(trigger=True))

        self.assertEqual(report["status"], "SHADOW_SIGNAL_READY")
        self.assertEqual(report["signal"]["shadow_action"], "SHADOW_TARGET_OBSERVATION")
        self.assertTrue(report["signal"]["triggered"])
        self.assertEqual(report["signal"]["target_shadow_weight"], 0.86)
        self.assertFalse(report["safety"]["does_start_shadow_loop"])
        self.assertFalse(report["safety"]["does_emit_order_signal"])
        self.assertFalse(report["safety"]["does_write_order_intent"])
        self.assertFalse(report["safety"]["does_enable_paper"])
        self.assertFalse(report["safety"]["does_enable_live"])
        self.assertFalse(report["safety"]["broker_submit_allowed_by_this_report"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_builds_flat_shadow_observation_when_trigger_is_absent(self) -> None:
        report = adapter.build_report(registry(), oos(), candles(trigger=False))

        self.assertEqual(report["status"], "SHADOW_SIGNAL_READY")
        self.assertEqual(report["signal"]["shadow_action"], "SHADOW_FLAT_OBSERVATION")
        self.assertFalse(report["signal"]["triggered"])
        self.assertEqual(report["signal"]["target_shadow_weight"], 0.0)

    def test_blocks_without_registered_candidate(self) -> None:
        report = adapter.build_report({"records": []}, oos(), candles(trigger=True))

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("NO_REGISTERED_BITHUMB_SHADOW_REVIEW_CANDIDATE", report["blockers"])
        self.assertFalse(report["safety"]["does_enable_live"])
        self.assertFalse(report["safety"]["does_emit_order_signal"])

    def test_uses_same_family_current_top_parameters_when_registered_candidate_rolls_out_of_latest_oos(self) -> None:
        rolled_oos = oos()
        rolled_oos["candidate_id"] = "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355"
        rolled_oos["top_oos"] = {
            "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
            "market": "KRW-POLA",
            "timeframe": "1d",
            "parameters": rolled_oos.pop("parameters"),
        }

        report = adapter.build_report(registry(), rolled_oos, candles(trigger=False))

        self.assertEqual(report["status"], "SHADOW_SIGNAL_READY")
        self.assertEqual(report["parameter_source"], "top_oos_same_family_market_timeframe_fallback")
        self.assertEqual(
            report["warnings"],
            ["OOS_PARAMETERS_FALLBACK_TO_SAME_FAMILY_CURRENT_TOP"],
        )
        self.assertFalse(report["parameter_candidate_matches_registered"])
        self.assertFalse(report["safety"]["does_emit_order_signal"])


if __name__ == "__main__":
    unittest.main()
