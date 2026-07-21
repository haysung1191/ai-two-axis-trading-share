from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_stage6_prequeue_dry_run.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_stage6_prequeue_dry_run", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
prequeue_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prequeue_mod)


class Cand022Stage6PrequeueDryRunTests(unittest.TestCase):
    def test_build_report_is_no_write_signal_ready_but_not_readiness_ready(self) -> None:
        report = prequeue_mod.build_report("2026-05-14T12:30:00+09:00")

        self.assertEqual(report["status"], "PASS_PREQUEUE_SIGNAL_READY")
        self.assertTrue(report["dry_run"])
        self.assertFalse(report["writes_files"])
        self.assertEqual(report["queue_membership"], "dry_run_not_in_queue")
        self.assertTrue(report["signal_ok"])
        self.assertEqual(report["symbol_count"], 7)
        self.assertEqual(report["latest_position_source"], "current_signal_observation")
        self.assertEqual(report["submit_mode"], "no_submit")
        self.assertFalse(report["readiness_ok"])
        self.assertEqual(report["safety"], prequeue_mod.SAFETY)
        self.assertIn("does_not_create_order_intent", report["non_goals"])


if __name__ == "__main__":
    unittest.main()
