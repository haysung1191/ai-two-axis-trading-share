from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\run_bithumb_current_actionable_shadow_observation_loop.py")
SPEC = importlib.util.spec_from_file_location("run_bithumb_current_actionable_shadow_observation_loop", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
loop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(loop)


def ready_report() -> dict:
    return {
        "status": "SHADOW_SIGNAL_READY",
        "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354",
        "blockers": [],
        "signal": {
            "signal_id": "sig",
            "market": "KRW-POLA",
            "timeframe": "1d",
            "bar_close_ts_utc": "2026-05-02T15:00:00+00:00",
            "shadow_action": "SHADOW_FLAT_OBSERVATION",
            "triggered": False,
            "target_shadow_weight": 0.0,
            "features": {
                "momentum_return": 0.01,
                "volume_ratio": 0.7,
            },
        },
    }


class BithumbCurrentActionableShadowObservationLoopTests(unittest.TestCase):
    def test_run_cycle_records_observation_without_order_paths(self) -> None:
        ok = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            original_log_dir = loop.LOG_DIR
            try:
                loop.LOG_DIR = Path(tmp)
                with (
                    patch.object(loop, "run_adapter_once", return_value=ok),
                    patch.object(loop, "read_json", return_value=ready_report()),
                ):
                    result = loop.run_cycle("test_run", 1)
            finally:
                loop.LOG_DIR = original_log_dir

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["observation"]["market"], "KRW-POLA")
        self.assertEqual(result["observation"]["shadow_action"], "SHADOW_FLAT_OBSERVATION")
        self.assertTrue(result["safety"]["does_run_observation_loop"])
        self.assertFalse(result["safety"]["does_start_order_shadow_loop"])
        self.assertFalse(result["safety"]["does_start_shadow_loop"])
        self.assertFalse(result["safety"]["does_emit_order_signal"])
        self.assertFalse(result["safety"]["does_write_order_intent"])
        self.assertFalse(result["safety"]["does_enable_paper"])
        self.assertFalse(result["safety"]["does_enable_live"])
        self.assertFalse(result["safety"]["broker_submit_allowed"])
        self.assertFalse(result["safety"]["private_submit_used"])
        self.assertEqual(result["safety"]["real_orders"], 0)

    def test_run_cycle_fails_when_adapter_report_is_blocked(self) -> None:
        ok = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")
        blocked = {"status": "BLOCKED", "blockers": ["NO_REGISTERED_BITHUMB_SHADOW_REVIEW_CANDIDATE"]}

        with tempfile.TemporaryDirectory() as tmp:
            original_log_dir = loop.LOG_DIR
            try:
                loop.LOG_DIR = Path(tmp)
                with (
                    patch.object(loop, "run_adapter_once", return_value=ok),
                    patch.object(loop, "read_json", return_value=blocked),
                ):
                    result = loop.run_cycle("test_run", 1)
            finally:
                loop.LOG_DIR = original_log_dir

        self.assertEqual(result["status"], "fail")
        self.assertIn("NO_REGISTERED_BITHUMB_SHADOW_REVIEW_CANDIDATE", result["observation"]["blockers"])
        self.assertFalse(result["safety"]["broker_submit_allowed"])


if __name__ == "__main__":
    unittest.main()
