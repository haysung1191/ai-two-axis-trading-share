from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\run_cand022_shadow_only_exception_apply_and_verify.py")
SPEC = importlib.util.spec_from_file_location("run_cand022_shadow_only_exception_apply_and_verify", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
runner_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner_mod)


class Cand022ShadowOnlyExceptionApplyAndVerifyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.apply_report_path = Path(self.tmpdir.name) / "shadow_apply_report.json"

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_exact_instruction_without_execute_stays_dry_run(self) -> None:
        fake_apply = {
            "status": "DRY_RUN_READY_TO_APPLY_SHADOW_ONLY_EXCEPTION",
            "wrote_acceptance": False,
            "appended_shadow_queue": False,
            "dry_run_preview_verification_commands": [
                "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120"
            ],
            "safety": runner_mod.SAFETY,
        }
        with patch.object(runner_mod.apply_mod, "apply_exception", return_value=fake_apply):
            report = runner_mod.build_report(
                operator_instruction=runner_mod.REQUIRED_INSTRUCTION,
                execute=False,
                confirm_apply=False,
                generated_at="2026-05-14T14:00:00+09:00",
                apply_report_path=self.apply_report_path,
            )

        self.assertEqual(report["status"], "DRY_RUN_READY_EXACT_INSTRUCTION_BUT_NOT_EXECUTED")
        self.assertEqual(report["apply_report_status"], "DRY_RUN_READY_TO_APPLY_SHADOW_ONLY_EXCEPTION")
        self.assertFalse(report["apply_report"]["wrote_acceptance"])
        self.assertFalse(report["apply_report"]["appended_shadow_queue"])
        self.assertEqual(report["verification_results"], [])
        self.assertIn(
            "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120",
            report["post_apply_verification_commands"],
        )
        self.assertEqual(report["safety"], runner_mod.SAFETY)

    def test_wrong_instruction_blocks_even_with_execute(self) -> None:
        report = runner_mod.build_report(
            operator_instruction="wrong",
            execute=True,
            confirm_apply=True,
            generated_at="2026-05-14T14:00:00+09:00",
            apply_report_path=self.apply_report_path,
        )

        self.assertEqual(report["status"], "BLOCKED_NOT_APPLIED")
        self.assertFalse(report["operator_instruction_exact_match"])
        self.assertEqual(report["apply_report_status"], "BLOCK_SHADOW_ONLY_EXCEPTION_APPLY")
        self.assertEqual(report["verification_results"], [])

    def test_execute_requires_confirm_flag(self) -> None:
        fake_apply = {
            "status": "DRY_RUN_READY_TO_APPLY_SHADOW_ONLY_EXCEPTION",
            "wrote_acceptance": False,
            "appended_shadow_queue": False,
            "dry_run_preview_verification_commands": [],
            "safety": runner_mod.SAFETY,
        }
        with patch.object(runner_mod.apply_mod, "apply_exception", return_value=fake_apply):
            report = runner_mod.build_report(
                operator_instruction=runner_mod.REQUIRED_INSTRUCTION,
                execute=True,
                confirm_apply=False,
                generated_at="2026-05-14T14:00:00+09:00",
                apply_report_path=self.apply_report_path,
            )

        self.assertEqual(report["status"], "DRY_RUN_READY_EXACT_INSTRUCTION_BUT_NOT_EXECUTED")
        self.assertFalse(report["apply_report"]["wrote_acceptance"])
        self.assertIn(runner_mod.CONFIRM_FLAG, report["next_safe_action"])

    def test_applied_status_runs_post_apply_verification_commands(self) -> None:
        fake_apply = {
            "status": "APPLIED_SHADOW_ONLY_EXCEPTION",
            "post_apply_verification_commands": [
                "python .\\build_cand022_stage6_shadow_readiness_packet.py",
                "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120",
            ],
            "wrote_acceptance": True,
            "appended_shadow_queue": True,
            "safety": runner_mod.SAFETY,
        }
        ran: list[str] = []

        def fake_runner(command: str) -> dict[str, object]:
            ran.append(command)
            return {"command": command, "returncode": 0, "status": "PASS"}

        with patch.object(runner_mod.apply_mod, "apply_exception", return_value=fake_apply):
            report = runner_mod.build_report(
                operator_instruction=runner_mod.REQUIRED_INSTRUCTION,
                execute=True,
                confirm_apply=True,
                generated_at="2026-05-14T14:00:00+09:00",
                runner=fake_runner,
            )

        self.assertEqual(report["status"], "APPLY_AND_VERIFY_COMPLETED")
        self.assertEqual(ran, fake_apply["post_apply_verification_commands"])
        self.assertEqual(report["post_apply_verification_commands"], fake_apply["post_apply_verification_commands"])
        self.assertFalse(report["verification_failed"])

    def test_existing_active_exception_is_success_status(self) -> None:
        fake_apply = {
            "status": "SHADOW_ONLY_EXCEPTION_ALREADY_ACTIVE",
            "post_apply_verification_commands": [],
            "dry_run_preview_verification_commands": [],
            "already_active": True,
            "safety": runner_mod.SAFETY,
        }

        with patch.object(runner_mod.apply_mod, "apply_exception", return_value=fake_apply):
            report = runner_mod.build_report(
                operator_instruction=runner_mod.REQUIRED_INSTRUCTION,
                execute=False,
                confirm_apply=False,
                generated_at="2026-05-14T14:00:00+09:00",
            )

        self.assertEqual(report["status"], "SHADOW_ONLY_EXCEPTION_ALREADY_ACTIVE")
        self.assertEqual(report["apply_report_status"], "SHADOW_ONLY_EXCEPTION_ALREADY_ACTIVE")
        self.assertEqual(report["verification_results"], [])
        self.assertIn("continue the refresh stack", report["next_safe_action"])


if __name__ == "__main__":
    unittest.main()
