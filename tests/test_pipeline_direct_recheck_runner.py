from __future__ import annotations

import unittest
from pathlib import Path


SCRIPT = Path(r"C:\AI\run_pipeline_direct_recheck.ps1")


class PipelineDirectRecheckRunnerTests(unittest.TestCase):
    def test_runner_refreshes_only_direct_blocker_surfaces(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")

        self.assertIn("build_stage13_completion_audit.py", text)
        self.assertIn("build_pipeline_direct_blocker_packet.py", text)
        self.assertIn("build_pipeline_direct_next_command.py", text)
        self.assertIn("build_start_here_after_reboot_validator.py", text)
        self.assertIn("build_pipeline_blocked_stop_state.py", text)
        self.assertIn("build_pipeline_blocked_runtime_safety_snapshot.py", text)
        self.assertIn("PYTHONDONTWRITEBYTECODE", text)
        self.assertIn("pipeline_direct_recheck_latest.json", text)
        self.assertNotIn("run_dual_repo_overnight_research.py", text)
        self.assertNotIn("register_bithumb_current_actionable_shadow_candidate.py --write", text)
        self.assertIn("does_not_enable_live", text)
        self.assertIn("does_not_submit_orders", text)


if __name__ == "__main__":
    unittest.main()
