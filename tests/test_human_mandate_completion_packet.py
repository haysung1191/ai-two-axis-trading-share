from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_human_mandate_completion_packet.py")
SPEC = importlib.util.spec_from_file_location("build_human_mandate_completion_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
packet_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_mod)


class HumanMandateCompletionPacketTests(unittest.TestCase):
    def test_packet_identifies_missing_policy_fields_without_applying(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "human_mandate.yaml"
            path.write_text(
                "\n".join(
                    [
                        "mandate_status: CAPS_PROVIDED",
                        "max_order_krw: 100000",
                        "max_daily_loss_krw: 20000",
                        "max_total_loss_krw: 100000",
                        "reporting_policy: null",
                        "incident_policy_confirmed: null",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            packet = packet_mod.build_packet("2026-05-14T00:00:00+09:00", path)

        self.assertEqual(packet["status"], "AWAITING_EXPLICIT_HUMAN_MANDATE_COMPLETION_INSTRUCTION")
        self.assertTrue(packet["caps_present"])
        self.assertTrue(packet["do_not_auto_apply"])
        self.assertIn("reporting_policy", packet["missing_fields"])
        self.assertIn("incident_policy_confirmed", packet["missing_fields"])
        self.assertIn("UPDATE HUMAN_MANDATE REPORTING_POLICY", packet["exact_instruction_to_apply_recommended_values"])
        self.assertTrue(packet["exact_instruction_file"].endswith("human_mandate_completion_instruction.latest.txt"))
        self.assertIn("apply_human_mandate_completion.py", packet["guarded_dry_run_command"])
        self.assertIn("--dry-run", packet["guarded_dry_run_command"])
        self.assertIn("--operator-instruction-file", packet["guarded_dry_run_command"])
        self.assertIn("apply_human_mandate_completion.py", packet["guarded_apply_command"])
        self.assertNotIn("--dry-run", packet["guarded_apply_command"])
        self.assertIn("--operator-instruction-file", packet["guarded_apply_command"])
        self.assertTrue(
            any(
                "run_cand022_provider_response_refresh_stack.py --timeout-seconds 120" in command
                for command in packet["post_apply_verification_commands"]
            )
        )
        self.assertFalse(packet["safety"]["order_intent_created"])

    def test_packet_does_not_claim_completion_when_caps_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "human_mandate.yaml"
            path.write_text(
                "mandate_status: CAPS_PROVIDED\n"
                "max_order_krw: null\n"
                "max_daily_loss_krw: 20000\n"
                "max_total_loss_krw: 100000\n"
                "reporting_policy: null\n"
                "incident_policy_confirmed: null\n",
                encoding="utf-8",
            )
            packet = packet_mod.build_packet("2026-05-14T00:00:00+09:00", path)

        self.assertFalse(packet["caps_present"])
        self.assertFalse(packet["can_complete_after_explicit_instruction"])
        self.assertFalse(packet["safety"]["broker_submit_allowed"])


if __name__ == "__main__":
    unittest.main()
