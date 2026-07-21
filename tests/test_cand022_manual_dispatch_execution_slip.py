from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_manual_dispatch_execution_slip.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_manual_dispatch_execution_slip", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
slip_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(slip_mod)


class Cand022ManualDispatchExecutionSlipTests(unittest.TestCase):
    def test_slip_is_ready_read_only_and_preserves_safety(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instruction = root / "instruction.json"
            router = root / "router.json"
            audit = root / "audit.json"
            send = root / "send.json"
            receipt = root / "receipt.json"
            presend = root / "presend.json"
            eml = root / "eml.json"
            confirmation_dry_run = root / "confirmation_dry_run.json"
            copy_review = root / "copy_review.json"
            instruction.write_text(
                json.dumps(
                    {
                        "status": "READY_MANUAL_DISPATCH_INSTRUCTION_PACKET",
                        "email": {
                            "subject": "CAND-022 source-backed provider response draft request",
                            "source_markdown": "frozen/email.md",
                            "source_sha256": "emailhash",
                        },
                        "attachment_to_send": {"path": "frozen/handoff.zip", "sha256": "ziphash"},
                        "confirmation_after_send": {
                            "preferred_helper_command": (
                                "python .\\write_cand022_dispatch_sent_confirmation.py --sent-at "
                                "\"<timezone-aware sent time>\" --sent-by \"<operator_or_account>\" "
                                "--recipient-or-channel \"<provider_or_channel>\" --i-confirm-actual-send"
                            ),
                            "editable_fields_only": ["sent_at", "sent_by", "recipient_or_channel"],
                            "latest": "sent.json",
                        },
                        "expected_return_files": ["a.csv", "b.csv", "c.csv"],
                        "return_staging_dir": "returned",
                        "safety": slip_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            router.write_text(
                json.dumps(
                    {
                        "recommended_next_action_id": "send_external_provider_dispatch_packet",
                        "action_router": [
                            {
                                "action_id": "send_external_provider_dispatch_packet",
                                "after_return_copy_review_required_before_refresh": True,
                                "after_return_refresh_allowed_only_if_copy_review_status": (
                                    "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW"
                                ),
                                "after_return_refresh_forbidden_if_copy_review_status": (
                                    "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW"
                                ),
                            }
                        ],
                        "safety": slip_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            audit.write_text(
                json.dumps(
                    {
                        "status": "NOT_COMPLETE_BLOCKED_BY_EXTERNAL_DISPATCH_AND_PROVIDER_ROWS",
                        "missing_or_blocked_check_ids": ["dispatch_sent_confirmation_recorded"],
                        "safety": slip_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            send.write_text(
                json.dumps(
                    {
                        "send_confirmation_valid": False,
                        "post_confirmation_watch_command": "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120",
                        "safety": slip_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            receipt.write_text(
                json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS", "safety": slip_mod.SAFETY}),
                encoding="utf-8",
            )
            presend.write_text(
                json.dumps(
                    {
                        "status": "PASS_PRESEND_ACTIVE_SEND_FILES_VERIFIED",
                        "blockers": [],
                        "active_send_files": {
                            "email_markdown": {"path": "frozen/email.md", "sha256": "emailhash"},
                            "attachment": {"path": "frozen/handoff.zip", "sha256": "ziphash"},
                        },
                        "safety": slip_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            eml.write_text(
                json.dumps(
                    {
                        "status": "READY_DISPATCH_EML_DRAFT_NO_SEND",
                        "eml_draft": "frozen/draft.eml",
                        "to_placeholder": "provider_or_channel_to_fill@example.invalid",
                        "attachment": "frozen/handoff.zip",
                        "attachment_sha256": "ziphash",
                        "blockers": [],
                        "safety": slip_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            confirmation_dry_run.write_text(
                json.dumps(
                    {
                        "status": "READY_DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML",
                        "dry_run_writer_status": "DRY_RUN_READY_TO_WRITE_DISPATCH_SENT_CONFIRMATION",
                        "confirmation_output_exists_after_dry_run": False,
                        "actual_after_send_command_template": (
                            "python .\\write_cand022_dispatch_sent_confirmation.py --sent-at \"<timezone-aware sent time>\" "
                            "--sent-by \"<operator_or_account>\" --recipient-or-channel \"<provider_or_channel>\" "
                            "--eml-report \"eml.json\" --i-confirm-actual-send"
                        ),
                        "dry_run_writer_report": {
                            "post_write_sequence_contract": {
                                "immediate_safe_commands": [],
                                "copy_review_required_before_refresh": True,
                                "copy_review_command": "python .\\build_kis_provider_returned_to_handoff_copy_review.py",
                                "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                                "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                                "refresh_command_after_allowed_copy_review": (
                                    "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120"
                                ),
                            }
                        },
                        "post_write_sequence_contract": {
                            "watch_command": (
                                "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120"
                            )
                        },
                        "blockers": [],
                        "safety": slip_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            copy_review.write_text(
                json.dumps(
                    {
                        "status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                        "blockers": ["returned_provider_csvs_missing"],
                        "manual_copy_plan": [
                            {
                                "kind": "membership",
                                "from": "returned/a.csv",
                                "to": "handoff/a.csv",
                                "allowed_only_if_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                            }
                        ],
                        "safety": slip_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = slip_mod.build_report(
                "2026-05-14T06:20:00+09:00",
                instruction_packet_path=instruction,
                router_path=router,
                active_audit_path=audit,
                send_status_path=send,
                return_receipt_path=receipt,
                presend_verifier_path=presend,
                provider_dispatch_eml_draft_path=eml,
                dispatch_confirmation_dry_run_from_eml_path=confirmation_dry_run,
                returned_to_handoff_copy_review_path=copy_review,
            )

        self.assertEqual(report["status"], "READY_MANUAL_DISPATCH_EXECUTION_SLIP")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["send_now"]["attachment"], "frozen/handoff.zip")
        self.assertEqual(report["send_now"]["attachment_sha256"], "ziphash")
        self.assertEqual(report["send_now"]["eml_draft"], "frozen/draft.eml")
        self.assertEqual(report["send_now"]["eml_draft_status"], "READY_DISPATCH_EML_DRAFT_NO_SEND")
        self.assertEqual(
            report["after_actual_send"]["confirmation_dry_run_status"],
            "READY_DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML",
        )
        self.assertTrue(report["after_actual_send"]["confirmation_dry_run_no_write"])
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", report["after_actual_send"]["preferred_helper_command"])
        self.assertIn("--i-confirm-actual-send", report["after_actual_send"]["preferred_helper_command"])
        self.assertIn("--eml-report", report["after_actual_send"]["preferred_helper_command"])
        self.assertIn("--eml-report", report["after_actual_send"]["dry_run_helper_command"])
        self.assertIn("run_cand022_provider_return_watch.py", report["after_actual_send"]["post_confirmation_watch_command"])
        self.assertEqual(
            report["after_actual_send"]["post_write_sequence_contract"]["immediate_safe_commands"],
            ["python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120"],
        )
        self.assertTrue(
            report["after_actual_send"]["post_write_sequence_contract"]["copy_review_required_before_refresh"]
        )
        self.assertIn("--dry-run", report["after_actual_send"]["dry_run_helper_command"])
        self.assertTrue(report["checks"]["presend_verified"])
        self.assertTrue(report["checks"]["send_files_match_presend_verifier"])
        self.assertTrue(report["checks"]["eml_draft_ready"])
        self.assertTrue(report["checks"]["confirmation_dry_run_ready"])
        self.assertTrue(report["checks"]["copy_review_required_before_refresh"])
        self.assertEqual(
            report["after_return"]["refresh_allowed_only_if_copy_review_status"],
            "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertEqual(report["after_return"]["copy_review_status"], "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW")
        self.assertIn("returned_provider_csvs_missing", report["after_return"]["copy_review_blockers"])
        self.assertIn("dispatch_sent_confirmation_recorded", report["current_blockers"])
        self.assertIn("does_not_send_email", report["non_goals"])
        self.assertEqual(report["safety"], slip_mod.SAFETY)

        md = slip_mod.render_md(report)
        self.assertIn("Manual dispatch slip: READY", md)
        self.assertIn("## Korean Operator Quick Steps", md)
        self.assertIn("실제 발송 후에만", md)
        self.assertIn("After return copy-review command", md)
        self.assertIn("수동 복사/검토 후 refresh command", md)
        self.assertNotIn("諛쒖넚", md)
        self.assertIn("paper/live/broker submit/order intent", md)
        self.assertIn("Pre-send verification: PASS_PRESEND_ACTIVE_SEND_FILES_VERIFIED", md)
        self.assertIn("After-send dry-run command:", md)
        self.assertIn("Local .eml draft: `frozen/draft.eml`", md)
        self.assertIn("Confirmation dry-run status: `READY_DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML`", md)
        self.assertIn("frozen/handoff.zip", md)
        self.assertIn("ziphash", md)
        self.assertIn("## Console-Safe Dispatch Fields", md)
        self.assertIn("Forbidden: do not enable paper/live/broker submit/order intent.", md)
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", md)
        self.assertIn("Start or keep the safe return watcher after confirmation", md)
        self.assertIn("Post-write sequence contract", md)
        self.assertIn("immediate_safe_commands", md)
        self.assertIn("run_cand022_provider_return_watch.py", md)
        self.assertIn("Validate fields without writing", md)
        self.assertIn("First run copy-review", md)
        self.assertIn("READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW", md)
        self.assertIn("BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW", md)
        self.assertIn("returned_provider_csvs_missing", md)
        self.assertIn('"pretrade_firewall_default_decision": "BLOCK"', md)

    def test_slip_blocks_if_instruction_packet_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instruction = root / "instruction.json"
            router = root / "router.json"
            audit = root / "audit.json"
            send = root / "send.json"
            receipt = root / "receipt.json"
            presend = root / "presend.json"
            copy_review = root / "copy_review.json"
            instruction.write_text(json.dumps({"status": "BLOCK_MANUAL_DISPATCH_INSTRUCTION_PACKET", "safety": slip_mod.SAFETY}), encoding="utf-8")
            router.write_text(json.dumps({"recommended_next_action_id": "send_external_provider_dispatch_packet", "safety": slip_mod.SAFETY}), encoding="utf-8")
            audit.write_text(json.dumps({"status": "NOT_COMPLETE", "safety": slip_mod.SAFETY}), encoding="utf-8")
            send.write_text(json.dumps({"send_confirmation_valid": False, "safety": slip_mod.SAFETY}), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS", "safety": slip_mod.SAFETY}), encoding="utf-8")
            presend.write_text(
                json.dumps(
                    {
                        "status": "PASS_PRESEND_ACTIVE_SEND_FILES_VERIFIED",
                        "blockers": [],
                        "active_send_files": {
                            "email_markdown": {"path": None, "sha256": None},
                            "attachment": {"path": None, "sha256": None},
                        },
                        "safety": slip_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            copy_review.write_text(json.dumps({"safety": slip_mod.SAFETY}), encoding="utf-8")

            report = slip_mod.build_report(
                "2026-05-14T06:20:00+09:00",
                instruction_packet_path=instruction,
                router_path=router,
                active_audit_path=audit,
                send_status_path=send,
                return_receipt_path=receipt,
                presend_verifier_path=presend,
                returned_to_handoff_copy_review_path=copy_review,
            )

        self.assertEqual(report["status"], "BLOCK_MANUAL_DISPATCH_EXECUTION_SLIP")
        self.assertIn("instruction_packet_ready", report["blockers"])

    def test_slip_blocks_if_presend_verifier_does_not_match_instruction_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instruction = root / "instruction.json"
            router = root / "router.json"
            audit = root / "audit.json"
            send = root / "send.json"
            receipt = root / "receipt.json"
            presend = root / "presend.json"
            copy_review = root / "copy_review.json"
            instruction.write_text(
                json.dumps(
                    {
                        "status": "READY_MANUAL_DISPATCH_INSTRUCTION_PACKET",
                        "email": {
                            "subject": "CAND-022 source-backed provider response draft request",
                            "source_markdown": "frozen/email.md",
                            "source_sha256": "emailhash",
                        },
                        "attachment_to_send": {"path": "frozen/handoff.zip", "sha256": "ziphash"},
                        "confirmation_after_send": {
                            "preferred_helper_command": "python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send",
                            "editable_fields_only": ["sent_at", "sent_by", "recipient_or_channel"],
                            "latest": "sent.json",
                        },
                        "expected_return_files": ["a.csv", "b.csv", "c.csv"],
                        "return_staging_dir": "returned",
                        "safety": slip_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            router.write_text(
                json.dumps(
                    {
                        "recommended_next_action_id": "send_external_provider_dispatch_packet",
                        "action_router": [
                            {
                                "action_id": "send_external_provider_dispatch_packet",
                                "after_return_copy_review_required_before_refresh": True,
                                "after_return_refresh_allowed_only_if_copy_review_status": (
                                    "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW"
                                ),
                                "after_return_refresh_forbidden_if_copy_review_status": (
                                    "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW"
                                ),
                            }
                        ],
                        "safety": slip_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            audit.write_text(json.dumps({"status": "NOT_COMPLETE", "safety": slip_mod.SAFETY}), encoding="utf-8")
            send.write_text(json.dumps({"send_confirmation_valid": False, "safety": slip_mod.SAFETY}), encoding="utf-8")
            receipt.write_text(
                json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS", "safety": slip_mod.SAFETY}),
                encoding="utf-8",
            )
            presend.write_text(
                json.dumps(
                    {
                        "status": "PASS_PRESEND_ACTIVE_SEND_FILES_VERIFIED",
                        "blockers": [],
                        "active_send_files": {
                            "email_markdown": {"path": "frozen/email.md", "sha256": "emailhash"},
                            "attachment": {"path": "frozen/handoff.zip", "sha256": "wronghash"},
                        },
                        "safety": slip_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            copy_review.write_text(json.dumps({"safety": slip_mod.SAFETY}), encoding="utf-8")

            report = slip_mod.build_report(
                "2026-05-14T06:20:00+09:00",
                instruction_packet_path=instruction,
                router_path=router,
                active_audit_path=audit,
                send_status_path=send,
                return_receipt_path=receipt,
                presend_verifier_path=presend,
                returned_to_handoff_copy_review_path=copy_review,
            )

        self.assertEqual(report["status"], "BLOCK_MANUAL_DISPATCH_EXECUTION_SLIP")
        self.assertIn("send_files_match_presend_verifier", report["blockers"])


if __name__ == "__main__":
    unittest.main()
