from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


WATCHDOG_PATH = Path(r"C:\AI\codex-output-kit\watch_cai_model_factory_goal.ps1")


class CaiModelFactoryGoalWatchdogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = WATCHDOG_PATH.read_text(encoding="utf-8-sig")

    def test_watchdog_surfaces_file_backed_goal_completion_state(self) -> None:
        self.assertIn("function Get-GoalCompletionInfo", self.script)
        self.assertIn("goal_completion = $goalCompletionInfo", self.script)
        self.assertIn("goal_model_factory_completion_audit_latest.json", self.script)
        self.assertIn("goal_model_factory_requirement_checklist_latest.json", self.script)
        self.assertIn("goal_model_factory_remaining_blockers_latest.json", self.script)
        self.assertIn("goal_model_factory_unblock_verification_packet_latest.json", self.script)
        self.assertIn("paper_promotion_evidence_latest.json", self.script)
        self.assertIn("realtime_risk_guard_latest.json", self.script)

        expected_fields = [
            "completion_audit_status",
            "completion_allowed",
            "completion_audit_incomplete_count",
            "requirement_checklist_status",
            "requirement_checklist_incomplete_count",
            "remaining_blocker_status",
            "remaining_blocker_count",
            "codex_unblockable_now_count",
            "operator_input_blocker_count",
            "approval_required_count",
            "remaining_blockers",
            "goal_wait_state",
            "goal_wait_reason",
            "unblock_verification_status",
            "unblock_verification_blocker_count",
            "unblock_recheck_status",
            "unblock_ready_recheck_lanes",
            "unblock_ready_recheck_lane_count",
            "unblock_ready_recheck_lanes_text",
            "unblock_kis_recheck_ready",
            "unblock_paper_recheck_ready",
            "paper_cycles_completed",
            "paper_cycles_target",
            "paper_cycles_missing",
            "non_flat_signal_count",
            "executable_order_count",
            "risk_guard_status",
            "risk_guard_halt_count",
            "risk_guard_warn_count",
        ]
        for field in expected_fields:
            self.assertIn(field, self.script)

    def test_watchdog_prefers_combined_paper_evidence_and_keeps_order_safety_fields(self) -> None:
        self.assertIn("$paperEvidence.evidence.combined_evidence", self.script)
        self.assertIn("combined_non_flat_signal_count", self.script)
        self.assertIn("combined_executable_order_evidence_count", self.script)

        safety_fields = [
            "private_submit_used",
            "real_orders",
            "broker_submit_scope",
            "broker_paper_policy_live_enabled_not_false",
            "broker_paper_policy_private_submit_used_not_false",
            "broker_submit_scope_not_paper_only",
            "paper_loop_real_orders_nonzero",
            "paper_loop_private_submit_used_not_false",
        ]
        for field in safety_fields:
            self.assertIn(field, self.script)

        self.assertIn(
            "Goal completion is not inferred from the watchdog. It mirrors the file-backed completion audit",
            self.script,
        )

    def test_watchdog_does_not_restart_codex_when_only_operator_or_approval_blockers_remain(self) -> None:
        expected_snippets = [
            "WAITING_FOR_OPERATOR_OR_APPROVAL",
            "remaining_blockers_require_operator_input_or_explicit_approval",
            "not_started_waiting_for_operator_or_approval",
            "goal_session_present_waiting_for_operator_or_approval",
            "stale_goal_not_restarted_waiting_for_operator_or_approval",
            "$goalWaitingForOperatorOrApproval",
            "codex_unblockable_now_count",
        ]
        for snippet in expected_snippets:
            self.assertIn(snippet, self.script)

    def test_watchdog_detects_current_goal_command_and_duplicates(self) -> None:
        expected_snippets = [
            "model-development factory goal",
            "--enable goals",
            "--cd\\s+\"?C:\\\\AI\"?",
            "duplicate_goal_sessions_detected_no_restart",
            "ParentProcessId",
            "CommandLine",
        ]
        for snippet in expected_snippets:
            self.assertIn(snippet, self.script)

    def test_watchdog_powershell_syntax_parses(self) -> None:
        command = (
            "$errors=$null; "
            "[System.Management.Automation.PSParser]::Tokenize("
            "(Get-Content -Raw -LiteralPath 'C:\\AI\\codex-output-kit\\watch_cai_model_factory_goal.ps1'), "
            "[ref]$errors) | Out-Null; "
            "if ($errors -and $errors.Count -gt 0) { $errors | ConvertTo-Json -Depth 3; exit 1 }"
        )
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
