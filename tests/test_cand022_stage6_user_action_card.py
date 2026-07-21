from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_cand022_stage6_user_action_card.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_stage6_user_action_card", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
card_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(card_mod)


class Cand022Stage6UserActionCardTests(unittest.TestCase):
    def test_card_surfaces_recommended_dispatch_and_optional_exact_phrases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            slip = root / "slip.json"
            shadow = root / "shadow.json"
            shadow_apply = root / "shadow_apply.json"
            mandate = root / "mandate.json"
            brief = root / "brief.json"
            completion = root / "completion.json"
            eml = root / "eml.json"
            confirmation_dry_run = root / "confirmation_dry_run.json"
            copy_review = root / "copy_review.json"
            slip.write_text(
                json.dumps(
                    {
                        "send_now": {
                            "subject": "subject",
                            "email_markdown": "email.md",
                            "email_sha256": "emailhash",
                            "attachment": "handoff.zip",
                            "attachment_sha256": "ziphash",
                        },
                        "after_actual_send": {
                            "preferred_helper_command": "python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send",
                            "post_confirmation_watch_command": "python .\\run_cand022_provider_return_watch.py --cycles 180",
                        },
                    }
                ),
                encoding="utf-8",
            )
            shadow.write_text(
                json.dumps(
                    {
                        "status": "READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT",
                        "is_approval": False,
                        "auto_apply_allowed": False,
                        "required_explicit_operator_instruction_before_any_contract_change": (
                            "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY"
                        ),
                    }
                ),
                encoding="utf-8",
            )
            shadow_apply.write_text(
                json.dumps(
                    {
                        "post_apply_verification_commands": [
                            "python .\\build_cand022_stage6_shadow_readiness_packet.py",
                            "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120",
                        ]
                    }
                ),
                encoding="utf-8",
            )
            mandate.write_text(
                json.dumps(
                    {
                        "status": "AWAITING_EXPLICIT_HUMAN_MANDATE_COMPLETION_INSTRUCTION",
                        "exact_instruction_file": "instruction.txt",
                        "guarded_dry_run_command": "dry-run",
                        "guarded_apply_command": "apply",
                        "explicit_non_approval": "not PAPER APPROVE and not LIVE APPROVE",
                    }
                ),
                encoding="utf-8",
            )
            brief.write_text(json.dumps({"status": "BLOCKED_NOT_COMPLETE"}), encoding="utf-8")
            eml.write_text(
                json.dumps(
                    {
                        "status": "READY_DISPATCH_EML_DRAFT_NO_SEND",
                        "eml_draft": "draft.eml",
                        "to_placeholder": "provider_or_channel_to_fill@example.invalid",
                        "eml_inspection": {
                            "checks": {
                                "eml_exists": True,
                                "to_placeholder_present": True,
                                "subject_matches": True,
                                "attachment_payload_sha256_matches": True,
                            },
                            "blockers": [],
                        },
                    }
                ),
                encoding="utf-8",
            )
            confirmation_dry_run.write_text(
                json.dumps(
                    {
                        "status": "READY_DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML",
                        "eml_inspection": {
                            "checks": {
                                "eml_exists": True,
                                "to_placeholder_present": True,
                                "subject_matches": True,
                                "attachment_payload_sha256_matches": True,
                            },
                            "blockers": [],
                        },
                        "dry_run_writer_status": "DRY_RUN_READY_TO_WRITE_DISPATCH_SENT_CONFIRMATION",
                        "confirmation_output_exists_after_dry_run": False,
                        "actual_after_send_command_template": (
                            "python .\\write_cand022_dispatch_sent_confirmation.py --sent-at \"<timezone-aware sent time>\" "
                            "--sent-by \"<operator_or_account>\" --recipient-or-channel \"<provider_or_channel>\" --i-confirm-actual-send"
                        ),
                        "dry_run_writer_report": {
                            "eml_report_path": str(eml),
                            "eml_inspection_required": True,
                            "eml_inspection_ready": True,
                            "planned_after_write_commands": [
                                "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120",
                            ],
                            "post_write_sequence_contract": {
                                "immediate_safe_commands": [],
                                "copy_review_required_before_refresh": True,
                                "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                                "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                            }
                        },
                        "post_write_sequence_contract": {
                            "watch_command": (
                                "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120"
                            )
                        },
                        "blockers": [],
                    }
                ),
                encoding="utf-8",
            )
            copy_review.write_text(
                json.dumps(
                    {
                        "status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                        "blockers": ["returned_handoff_staging_verifier_not_ready"],
                        "manual_copy_plan": [
                            {
                                "kind": "membership",
                                "from": "returned.csv",
                                "to": "handoff.csv",
                                "allowed_only_if_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                            }
                        ],
                        "non_goals": ["does_not_auto_copy_returned_files"],
                    }
                ),
                encoding="utf-8",
            )
            completion.write_text(
                json.dumps(
                    {
                        "completion_decision": "NOT_COMPLETE",
                        "stage6_reached": False,
                        "completion_percent_by_checklist": 85.7,
                        "missing_or_blocked_check_ids": ["stage6_queue_allowed_or_shadow_passed"],
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(card_mod, "MANUAL_DISPATCH_SLIP", slip), patch.object(
                card_mod, "SHADOW_EXCEPTION_CONTRACT", shadow
            ), patch.object(
                card_mod, "SHADOW_EXCEPTION_APPLY_AND_VERIFY_REPORT", shadow_apply
            ), patch.object(card_mod, "HUMAN_MANDATE_PACKET", mandate), patch.object(
                card_mod, "OPERATOR_BRIEF", brief
            ), patch.object(card_mod, "STAGE6_COMPLETION_AUDIT", completion), patch.object(
                card_mod, "DISPATCH_EML_DRAFT", eml
            ), patch.object(
                card_mod, "DISPATCH_CONFIRMATION_DRY_RUN", confirmation_dry_run
            ), patch.object(
                card_mod, "RETURNED_TO_HANDOFF_COPY_REVIEW", copy_review
            ):
                report = card_mod.build_report("2026-05-14T13:40:00+09:00")

        self.assertEqual(report["status"], "READY_STAGE6_USER_ACTION_CARD")
        self.assertFalse(report["stage6_reached"])
        self.assertEqual(report["recommended_path"]["attachment_sha256"], "ziphash")
        self.assertEqual(report["recommended_path"]["eml_draft"], "draft.eml")
        self.assertEqual(report["working_directory"], str(card_mod.ROOT))
        self.assertEqual(report["recommended_path"]["eml_draft_status"], "READY_DISPATCH_EML_DRAFT_NO_SEND")
        self.assertTrue(report["recommended_path"]["eml_inspection"]["checks"]["attachment_payload_sha256_matches"])
        self.assertEqual(
            report["recommended_path"]["dispatch_confirmation_dry_run_status"],
            "READY_DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML",
        )
        self.assertTrue(
            report["recommended_path"]["dispatch_confirmation_dry_run_eml_inspection"]["checks"][
                "attachment_payload_sha256_matches"
            ]
        )
        self.assertTrue(report["recommended_path"]["dispatch_confirmation_writer_eml_inspection_required"])
        self.assertTrue(report["recommended_path"]["dispatch_confirmation_writer_eml_inspection_ready"])
        self.assertEqual(report["recommended_path"]["dispatch_confirmation_writer_eml_report_path"], str(eml))
        self.assertTrue(report["recommended_path"]["dispatch_confirmation_dry_run_no_write"])
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", report["recommended_path"]["after_send_helper_command"])
        self.assertEqual(
            report["recommended_path"]["planned_after_write_commands"],
            [
                "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120",
            ],
        )
        self.assertTrue(
            report["recommended_path"]["post_write_sequence_contract"]["copy_review_required_before_refresh"]
        )
        self.assertEqual(
            report["optional_shadow_only_exception"]["exact_instruction"],
            "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY",
        )
        self.assertIn(
            "run_cand022_shadow_only_exception_apply_and_verify.py",
            report["optional_shadow_only_exception"]["apply_and_verify_dry_run_command"],
        )
        self.assertIn(
            "--i-confirm-apply-shadow-only-exception",
            report["optional_shadow_only_exception"]["apply_and_verify_execute_command"],
        )
        self.assertIn(
            "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120",
            report["optional_shadow_only_exception"]["post_apply_verification_commands"],
        )
        self.assertIn("shadow_exception_apply_and_verify", report["source_files"])
        self.assertIn("shadow_exception_apply_and_verify_report", report["source_files"])
        self.assertIn("dispatch_eml_draft", report["source_files"])
        self.assertIn("dispatch_confirmation_dry_run", report["source_files"])
        self.assertEqual(
            report["after_return_copy_review"]["status"],
            "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertTrue(report["after_return_copy_review"]["required_before_refresh"])
        self.assertEqual(
            report["after_return_copy_review"]["refresh_allowed_only_if_status"],
            "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertEqual(
            report["after_return_copy_review"]["refresh_forbidden_if_status"],
            "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertIn(
            "build_kis_provider_returned_to_handoff_copy_review.py",
            report["after_return_copy_review"]["copy_review_command"],
        )
        self.assertIn("returned_to_handoff_copy_review", report["source_files"])
        self.assertFalse(report["optional_shadow_only_exception"]["is_approval"])
        self.assertFalse(report["safety"]["order_intent_created"])
        md = card_mod.render_md(report)
        self.assertIn("CAND-022 Stage 6", md)
        self.assertIn("provider", md)
        self.assertIn("APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY", md)
        self.assertIn("run_cand022_shadow_only_exception_apply_and_verify.py", md)
        self.assertIn("build_cand022_stage6_shadow_readiness_packet.py", md)
        self.assertIn("Shadow-only post-apply verification", md)
        self.assertIn("cd C:\\AI\npython .\\build_cand022_stage6_shadow_readiness_packet.py", md)
        self.assertIn("cd C:\\AI\npython .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120", md)
        self.assertIn("draft.eml", md)
        self.assertIn(".eml inspection", md)
        self.assertIn("```json", md)
        self.assertIn("attachment_payload_sha256_matches", md)
        self.assertIn("Confirmation dry-run EML inspection", md)
        self.assertIn("Confirmation writer EML inspection required", md)
        self.assertIn("Confirmation writer EML inspection ready", md)
        self.assertIn("READY_DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML", md)
        self.assertIn("Planned commands after confirmation write", md)
        self.assertIn("run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120", md)
        self.assertIn("kis_provider_returned_to_handoff_copy_review_latest.json", md)
        self.assertIn("First run copy-review", md)
        self.assertIn("Immediate safe commands after confirmation", md)
        self.assertIn("Copy-review required before refresh", md)
        self.assertIn("READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW", md)
        self.assertIn("BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW", md)
        self.assertIn("build_kis_provider_returned_to_handoff_copy_review.py", md)
        self.assertIn("run_cand022_provider_response_refresh_stack.py", md)
        self.assertIn("cd C:\\AI", md)
        self.assertIn("paper/live/broker/order_intent", md)


if __name__ == "__main__":
    unittest.main()
