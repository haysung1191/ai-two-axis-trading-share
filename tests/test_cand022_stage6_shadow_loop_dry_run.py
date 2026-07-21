from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_stage6_shadow_loop_dry_run.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_stage6_shadow_loop_dry_run", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
dry_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dry_mod)


class Cand022Stage6ShadowLoopDryRunTests(unittest.TestCase):
    def test_build_report_proves_cand022_no_write_shadow_loop_surface(self) -> None:
        report = dry_mod.build_report("2026-05-14T15:20:00+09:00")

        self.assertEqual(report["status"], "PASS_STAGE6_LOOP_CAND022_DRY_RUN_READY")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["candidate_id"], "CAND-022")
        self.assertFalse(report["dry_run_report"]["writes_files"])
        self.assertEqual(report["dry_run_report"]["shadow_queue_candidates"], ["CAND-022"])
        self.assertEqual(report["dry_run_report"]["safety"], dry_mod.loop_mod.SAFETY)

        candidate = report["candidate_report"]
        self.assertEqual(candidate["candidate_id"], "CAND-022")
        self.assertIn(candidate["queue_membership"], {"dry_run_not_in_queue", "present"})
        self.assertTrue(candidate["signal_ok"])
        self.assertEqual(candidate["symbol_count"], 7)
        self.assertEqual(candidate["submit_mode"], "no_submit")
        self.assertEqual(candidate["latest_position_source"], "current_signal_observation")
        self.assertIn("does_not_write_shadow_signal_log", report["non_goals"])
        self.assertIn("does_not_mark_stage6_reached", report["non_goals"])
        self.assertFalse(report["safety"]["order_intent_created"])


if __name__ == "__main__":
    unittest.main()
