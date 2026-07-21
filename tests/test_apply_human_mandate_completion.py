from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import apply_human_mandate_completion as apply_mod


class ApplyHumanMandateCompletionTests(unittest.TestCase):
    def write_mandate(self, path: Path) -> None:
        path.write_text(
            "\n".join(
                [
                    "mandate_status: CAPS_PROVIDED",
                    "mandate_incomplete_reason: >",
                    "  Remaining fields are missing.",
                    "max_order_krw: 100000",
                    "max_daily_loss_krw: 20000",
                    "max_total_loss_krw: 100000",
                    "reporting_policy: null",
                    "incident_policy_confirmed: null",
                    "safety_state_while_incomplete:",
                    "  paper_enabled: false",
                    "  live_enabled: false",
                    "  broker_submit_allowed: false",
                    "  real_orders_allowed: false",
                    "  live_order_intent_creation_allowed: false",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def test_blocks_without_exact_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "human_mandate.yaml"
            self.write_mandate(path)
            before = path.read_text(encoding="utf-8")

            report = apply_mod.apply_mandate_completion(
                "wrong instruction",
                dry_run=True,
                mandate_path=path,
                report_path=Path(tmp) / "apply_report.json",
            )

            self.assertEqual(report["status"], "BLOCK_HUMAN_MANDATE_COMPLETION_APPLY")
            self.assertIn("operator_instruction_exact_match", report["blockers"])
            self.assertFalse(report["wrote_human_mandate"])
            self.assertEqual(path.read_text(encoding="utf-8"), before)
            self.assertEqual(report["safety"], apply_mod.SAFETY)

    def test_dry_run_with_exact_instruction_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "human_mandate.yaml"
            self.write_mandate(path)
            before = path.read_text(encoding="utf-8")

            report = apply_mod.apply_mandate_completion(
                apply_mod.REQUIRED_INSTRUCTION,
                dry_run=True,
                mandate_path=path,
                report_path=Path(tmp) / "apply_report.json",
                generated_at="2026-05-14T10:00:00+09:00",
            )

            self.assertEqual(report["status"], "DRY_RUN_READY_TO_APPLY_HUMAN_MANDATE_COMPLETION")
            self.assertEqual(report["blockers"], [])
            self.assertFalse(report["wrote_human_mandate"])
            self.assertEqual(path.read_text(encoding="utf-8"), before)
            self.assertIn("build_cand022_stage6_shadow_readiness_packet.py", " ".join(report["dry_run_preview_verification_commands"]))
            self.assertEqual(report["safety"], apply_mod.SAFETY)

    def test_main_accepts_operator_instruction_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "human_mandate.yaml"
            instruction_path = Path(tmp) / "instruction.txt"
            self.write_mandate(path)
            instruction_path.write_text(apply_mod.REQUIRED_INSTRUCTION + "\n", encoding="utf-8")

            report = apply_mod.apply_mandate_completion(
                instruction_path.read_text(encoding="utf-8").strip(),
                dry_run=True,
                mandate_path=path,
                report_path=Path(tmp) / "apply_report.json",
                generated_at="2026-05-14T10:00:00+09:00",
            )

            self.assertEqual(report["status"], "DRY_RUN_READY_TO_APPLY_HUMAN_MANDATE_COMPLETION")

    def test_apply_with_exact_instruction_updates_only_mandate_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "human_mandate.yaml"
            self.write_mandate(path)

            report = apply_mod.apply_mandate_completion(
                apply_mod.REQUIRED_INSTRUCTION,
                dry_run=False,
                mandate_path=path,
                report_path=Path(tmp) / "apply_report.json",
                generated_at="2026-05-14T10:00:00+09:00",
            )
            after = path.read_text(encoding="utf-8")

            self.assertEqual(report["status"], "APPLIED_HUMAN_MANDATE_COMPLETION")
            self.assertTrue(report["wrote_human_mandate"])
            self.assertIn("mandate_status: COMPLETE", after)
            self.assertIn("reporting_policy:", after)
            self.assertIn("incident_policy_confirmed:", after)
            self.assertIn("checkpoint_email_frequency_hours: 3", after)
            self.assertIn("kill_switch_trigger_conditions_accepted: true", after)
            self.assertIn("paper_enabled: false", after)
            self.assertIn("live_enabled: false", after)
            self.assertIn("broker_submit_allowed: false", after)
            self.assertIn("live_order_intent_creation_allowed: false", after)
            self.assertNotIn("paper_enabled: true", after)
            self.assertNotIn("live_enabled: true", after)
            self.assertEqual(report["safety"], apply_mod.SAFETY)


if __name__ == "__main__":
    unittest.main()
