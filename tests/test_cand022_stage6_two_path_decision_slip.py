from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_cand022_stage6_two_path_decision_slip.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_stage6_two_path_decision_slip", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
slip_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(slip_mod)


class Cand022Stage6TwoPathDecisionSlipTests(unittest.TestCase):
    def test_slip_surfaces_only_two_valid_stage6_paths_without_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit = root / "stage6.json"
            card = root / "card.json"
            shadow_apply = root / "shadow_apply.json"
            audit.write_text(
                json.dumps(
                    {
                        "completion_decision": "NOT_COMPLETE",
                        "stage6_reached": False,
                        "completion_percent_by_checklist": 90.5,
                        "missing_or_blocked_check_ids": [
                            "dispatch_sent_confirmation_recorded",
                            "stage6_queue_allowed_or_shadow_passed",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            card.write_text(
                json.dumps(
                    {
                        "recommended_path": {
                            "email_markdown": "email.md",
                            "email_sha256": "emailhash",
                            "attachment": "handoff.zip",
                            "attachment_sha256": "ziphash",
                            "after_send_helper_command": (
                                "python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send"
                            ),
                            "post_confirmation_watch_command": (
                                "python .\\run_cand022_provider_return_watch.py --cycles 180"
                            ),
                        },
                        "optional_shadow_only_exception": {
                            "is_approval": False,
                            "auto_apply_allowed": False,
                            "exact_instruction": "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY",
                            "apply_and_verify_dry_run_command": (
                                "python .\\run_cand022_shadow_only_exception_apply_and_verify.py "
                                "--operator-instruction \"APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY\""
                            ),
                            "apply_and_verify_execute_command": (
                                "python .\\run_cand022_shadow_only_exception_apply_and_verify.py "
                                "--operator-instruction \"APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY\" "
                                "--execute --i-confirm-apply-shadow-only-exception"
                            ),
                            "execute_command_requires_confirm_flag": "--i-confirm-apply-shadow-only-exception",
                            "meaning": "no_submit_review_only_shadow_observation",
                        },
                    }
                ),
                encoding="utf-8",
            )
            shadow_apply.write_text(
                json.dumps(
                    {
                        "status": "DRY_RUN_READY_EXACT_INSTRUCTION_BUT_NOT_EXECUTED",
                        "operator_instruction_exact_match": True,
                        "apply_report_status": "DRY_RUN_READY_TO_APPLY_SHADOW_ONLY_EXCEPTION",
                        "execute_requested": False,
                        "confirm_apply": False,
                    }
                ),
                encoding="utf-8",
            )

            with (
                patch.object(slip_mod, "STAGE6_AUDIT", audit),
                patch.object(slip_mod, "ACTION_CARD", card),
                patch.object(slip_mod, "SHADOW_APPLY_AND_VERIFY", shadow_apply),
            ):
                report = slip_mod.build_report("2026-05-14T19:05:00+09:00")

        self.assertEqual(report["status"], "WAITING_FOR_OPERATOR_STAGE6_PATH_DECISION")
        self.assertFalse(report["stage6_reached"])
        self.assertEqual(report["completion_percent"], 90.5)
        self.assertEqual(report["recommended_path"]["path_id"], "provider_dispatch_and_returned_rows")
        self.assertIn("Recommended: send provider packet", report["recommended_path"]["label"])
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", report["recommended_path"]["after_actual_send_command"])
        self.assertIn("--i-confirm-actual-send", report["recommended_path"]["after_actual_send_command"])
        self.assertIn("run_cand022_provider_return_watch.py", report["recommended_path"]["post_confirmation_watch_command"])
        self.assertEqual(
            report["recommended_path"]["refresh_allowed_only_if"],
            "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertIn(
            "kis_provider_returned_to_handoff_copy_review_latest.json",
            report["recommended_path"]["after_return_copy_review_artifact"],
        )
        self.assertEqual(report["alternate_path"]["path_id"], "no_submit_shadow_only_exception")
        self.assertIn("Alternative: explicitly apply", report["alternate_path"]["label"])
        self.assertFalse(report["alternate_path"]["is_approval"])
        self.assertFalse(report["alternate_path"]["auto_apply_allowed"])
        self.assertIn("NO_SUBMIT", report["alternate_path"]["exact_instruction_required"])
        self.assertIn("--execute", report["alternate_path"]["execute_command"])
        self.assertIn("--i-confirm-apply-shadow-only-exception", report["alternate_path"]["execute_command"])
        self.assertEqual(
            report["alternate_path"]["latest_dry_run_status"],
            "DRY_RUN_READY_EXACT_INSTRUCTION_BUT_NOT_EXECUTED",
        )
        self.assertTrue(report["alternate_path"]["latest_dry_run_exact_match"])
        self.assertFalse(report["alternate_path"]["latest_dry_run_execute_requested"])
        self.assertFalse(report["alternate_path"]["latest_dry_run_confirm_apply"])
        self.assertIn("does_not_apply_shadow_exception", report["non_goals"])
        self.assertIn("shadow_apply_and_verify", report["source_files"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        md = slip_mod.render_md(report)
        self.assertIn("Path 1 - Recommended", md)
        self.assertIn("Path 2 - Explicit Alternative", md)
        self.assertIn("READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW", md)
        self.assertIn("kis_provider_returned_to_handoff_copy_review_latest.json", md)
        self.assertIn("APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY", md)
        self.assertIn("DRY_RUN_READY_EXACT_INSTRUCTION_BUT_NOT_EXECUTED", md)
        self.assertIn("does_not", " ".join(report["non_goals"]))


if __name__ == "__main__":
    unittest.main()
