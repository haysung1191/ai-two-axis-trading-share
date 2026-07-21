from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


RUNNER_PATH = Path(r"C:\AI\codex-output-kit\run_cai_model_factory_goal.ps1")


class CaiModelFactoryGoalRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = RUNNER_PATH.read_text(encoding="utf-8-sig")

    def test_runner_has_file_backed_wait_preflight(self) -> None:
        expected_snippets = [
            "function Get-GoalRunnerPreflight",
            "function Get-ActiveModelFactoryGoalProcesses",
            "skip_start_existing_goal_session_present",
            "single_instance_model_factory_goal_already_running",
            "active_goal_process_count",
            "model-development factory goal",
            "goal_model_factory_remaining_blockers_latest.json",
            "skip_start_waiting_for_operator_or_approval",
            "remaining_blockers_require_operator_input_or_explicit_approval",
            "codex_unblockable_now_count",
            "operator_input_blocker_count",
            "approval_required_count",
        ]
        for snippet in expected_snippets:
            self.assertIn(snippet, self.script)

    def test_runner_print_only_surfaces_preflight_without_starting_codex(self) -> None:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(RUNNER_PATH),
                "-PrintOnly",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("Preflight:", completed.stdout)
        self.assertRegex(
            completed.stdout,
            "skip_start_waiting_for_operator_or_approval|skip_start_existing_goal_session_present",
        )
        self.assertRegex(completed.stdout, "codex_unblockable_now_count|active_goal_process_count")

    def test_runner_powershell_syntax_parses(self) -> None:
        command = (
            "$errors=$null; "
            "[System.Management.Automation.PSParser]::Tokenize("
            "(Get-Content -Raw -LiteralPath 'C:\\AI\\codex-output-kit\\run_cai_model_factory_goal.ps1'), "
            "[ref]$errors) | Out-Null; "
            "if ($errors -and $errors.Count -gt 0) { $errors | ConvertTo-Json -Depth 3; exit 1 }"
        )
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
