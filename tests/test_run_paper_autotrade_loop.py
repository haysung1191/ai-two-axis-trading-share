from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\run_paper_autotrade_loop.py")
SPEC = importlib.util.spec_from_file_location("run_paper_autotrade_loop", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
loop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(loop)


class RunPaperAutotradeLoopTests(unittest.TestCase):
    def test_blocked_activation_packet_is_safe_collection_state(self) -> None:
        safety = {
            "report_read": True,
            "status": "blocked",
            "real_orders": 0,
            "broker_submit_allowed": True,
            "broker_submit_scope": "paper_only",
            "private_submit_used": False,
            "global_disable_file_present": True,
            "live_enabled_flag": False,
        }

        self.assertTrue(loop.executor_safety_ok(safety))

    def test_non_activate_heartbeat_does_not_increment_promotion_cycles(self) -> None:
        self.assertEqual(loop.completed_cycle_count(252, 1, activate=False), 252)
        self.assertEqual(loop.completed_cycle_count(252, 1, activate=True), 253)

    def test_paper_approval_from_env_requires_exact_phrase(self) -> None:
        with patch.dict(os.environ, {loop.PAPER_APPROVAL_ENV: "PAPER APPROVE small_account_growth_paper"}):
            self.assertTrue(loop.paper_approval_from_env())
        with patch.dict(os.environ, {loop.PAPER_APPROVAL_ENV: "PAPER APPROVE wrong_profile"}):
            self.assertFalse(loop.paper_approval_from_env())

    def test_previous_cycles_completed_reads_existing_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop.OUT_DIR = root
            root.mkdir(parents=True, exist_ok=True)
            (root / "paper_autotrade_loop_latest.json").write_text(
                json.dumps({"cycles_completed": 252}),
                encoding="utf-8",
            )

            self.assertEqual(loop.previous_cycles_completed(), 252)


if __name__ == "__main__":
    unittest.main()
