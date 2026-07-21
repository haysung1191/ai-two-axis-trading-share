from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_stage6_operator_wait_packet.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_stage6_operator_wait_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
packet_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_mod)


class Cand022Stage6OperatorWaitPacketTests(unittest.TestCase):
    def test_packet_freezes_operator_wait_without_marking_stage6_reached(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = root / "entry.json"
            stage6 = root / "stage6.json"
            plan = root / "plan.json"
            router = root / "router.json"
            brief = root / "brief.json"
            watch = root / "watch.json"
            mandate = root / "mandate.json"
            send = root / "send.json"
            returned_copy = root / "returned_copy.json"
            entry.write_text(
                json.dumps(
                    {
                        "stage6_reached": False,
                        "entry_path_status": "READY_WAIT_OPERATOR_OR_PROVIDER_INPUT",
                        "blockers": ["human_mandate_incomplete"],
                        "safety": packet_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            stage6.write_text(
                json.dumps(
                    {
                        "readiness_decision": "BLOCK",
                        "shadow_queue_allowed": False,
                        "shadow_passed": False,
                        "blockers": ["human_mandate_incomplete"],
                        "safety": packet_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            plan.write_text(json.dumps({"autonomous_continuation_decision": "WAIT_FOR_OPERATOR_OR_EXTERNAL_INPUT"}), encoding="utf-8")
            router.write_text(
                json.dumps(
                    {
                        "recommended_next_action_id": "send_external_provider_dispatch_packet",
                        "action_router": [
                            {
                                "action_id": "send_external_provider_dispatch_packet",
                                "status": "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION",
                                "manual_dispatch_execution_slip_md": "slip.md",
                                "frozen_email_markdown": "email.md",
                                "frozen_attachment": "handoff.zip",
                                "send_confirmation_path": "sent.json",
                                "send_confirmation_valid": False,
                                "expected_return_files": ["a.csv", "b.csv", "c.csv"],
                                "return_staging_dir": "returned",
                            },
                            {
                                "action_id": "obtain_explicit_human_mandate_completion_instruction",
                                "status": "AWAITING_EXPLICIT_HUMAN_MANDATE_COMPLETION_INSTRUCTION",
                                "missing_fields": ["reporting_policy"],
                                "exact_instruction_file": "instruction.txt",
                                "guarded_dry_run_command": "python .\\apply_human_mandate_completion.py --dry-run",
                                "guarded_apply_command": "python .\\apply_human_mandate_completion.py",
                                "explicit_non_approval": "not PAPER APPROVE",
                            },
                            {
                                "action_id": "review_shadow_only_exception_contract",
                                "status": "READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT",
                                "required_explicit_operator_instruction_before_any_contract_change": (
                                    "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY"
                                ),
                                "preferred_guarded_apply_and_verify_commands": {
                                    "dry_run": 'python .\\run_cand022_shadow_only_exception_apply_and_verify.py --operator-instruction "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY"',
                                    "apply": 'python .\\run_cand022_shadow_only_exception_apply_and_verify.py --operator-instruction "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY" --execute --i-confirm-apply-shadow-only-exception',
                                },
                                "guarded_dry_run_command": 'python .\\run_cand022_shadow_only_exception_apply_and_verify.py --operator-instruction "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY"',
                                "guarded_apply_command": 'python .\\run_cand022_shadow_only_exception_apply_and_verify.py --operator-instruction "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY" --execute --i-confirm-apply-shadow-only-exception',
                                "confirm_flag_required_for_real_apply": "--i-confirm-apply-shadow-only-exception",
                                "real_apply_requires_execute_flag": True,
                                "low_level_apply_script_is_not_operator_surface": True,
                                "forbidden_actions": ["do_not_create_order_intent"],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            brief.write_text(
                json.dumps(
                    {
                        "dispatch_file_policy": {
                            "active_email_markdown": "frozen/email.md",
                            "active_email_sha256": "emailhash",
                            "active_attachment": "frozen/handoff.zip",
                            "active_attachment_sha256": "ziphash",
                        },
                        "manual_dispatch_execution_slip": {
                            "helper_command": "python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send"
                        },
                    }
                ),
                encoding="utf-8",
            )
            watch.write_text(
                json.dumps(
                    {
                        "status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
                        "blockers": ["dispatch_sent_confirmation_missing_or_invalid", "returned_provider_csvs_missing"],
                        "expected_return_files": ["a.csv", "b.csv", "c.csv"],
                        "return_staging_dir": "returned",
                        "copy_review_result": None,
                        "refresh_result": None,
                        "non_goals": [
                            "does_not_write_dispatch_confirmation",
                            "does_not_copy_or_generate_provider_csvs",
                            "does_not_run_refresh_before_returned_to_handoff_copy_review",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            mandate.write_text(json.dumps({"status": "AWAITING_EXPLICIT_HUMAN_MANDATE_COMPLETION_INSTRUCTION"}), encoding="utf-8")
            send.write_text(json.dumps({"status": "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION"}), encoding="utf-8")
            returned_copy.write_text(
                json.dumps(
                    {
                        "status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                        "blockers": ["membership_returned_file_missing"],
                        "manual_copy_plan": [
                            {
                                "kind": "membership",
                                "allowed_only_if_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            packet = packet_mod.build_packet(
                "2026-05-14T10:30:00+09:00",
                entry_audit_path=entry,
                stage6_path=stage6,
                closure_plan_path=plan,
                router_path=router,
                operator_brief_path=brief,
                return_watch_path=watch,
                mandate_packet_path=mandate,
                dispatch_send_status_path=send,
                returned_to_handoff_copy_review_path=returned_copy,
            )

        self.assertEqual(packet["status"], "WAIT_OPERATOR_OR_PROVIDER_INPUT_TO_ADVANCE_STAGE6")
        self.assertFalse(packet["stage6_reached"])
        self.assertTrue(packet["blocked_by_operator_or_provider"])
        self.assertEqual(packet["recommended_next_action_id"], "send_external_provider_dispatch_packet")
        self.assertEqual(packet["dispatch_wait"]["active_attachment"], "frozen/handoff.zip")
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", packet["dispatch_wait"]["after_actual_send_command"])
        self.assertEqual(packet["dispatch_wait"]["expected_return_files"], ["a.csv", "b.csv", "c.csv"])
        self.assertIn("run_cand022_provider_return_watch.py", packet["dispatch_wait"]["safe_watch_command_after_dispatch"])
        self.assertIn("--cycles 180", packet["dispatch_wait"]["safe_watch_command_after_dispatch"])
        self.assertIn("--no-refresh", packet["dispatch_wait"]["safe_watch_command_report_only"])
        self.assertTrue(packet["dispatch_wait"]["copy_review_before_refresh_enforced"])
        self.assertIsNone(packet["dispatch_wait"]["return_watch_copy_review_result"])
        self.assertIsNone(packet["dispatch_wait"]["return_watch_refresh_result"])
        self.assertIn(
            "does_not_run_refresh_before_returned_to_handoff_copy_review",
            packet["dispatch_wait"]["return_watch_non_goals"],
        )
        self.assertTrue(packet["dispatch_wait"]["after_return_copy_review"]["required_before_refresh"])
        self.assertEqual(
            packet["dispatch_wait"]["after_return_copy_review"]["status"],
            "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertIn(
            "membership_returned_file_missing",
            packet["dispatch_wait"]["after_return_copy_review"]["blockers"],
        )
        self.assertIn("run_cand022_provider_response_refresh_stack.py", packet["dispatch_wait"]["after_return_command"])
        self.assertIn("apply_human_mandate_completion.py", packet["optional_human_mandate_wait"]["guarded_apply_command"])
        self.assertIn("NO_SUBMIT", packet["optional_shadow_exception_wait"]["required_exact_instruction"])
        self.assertIn(
            "run_cand022_shadow_only_exception_apply_and_verify.py",
            packet["optional_shadow_exception_wait"]["guarded_dry_run_command"],
        )
        self.assertIn("--execute", packet["optional_shadow_exception_wait"]["guarded_apply_command"])
        self.assertIn(
            "--i-confirm-apply-shadow-only-exception",
            packet["optional_shadow_exception_wait"]["guarded_apply_command"],
        )
        self.assertEqual(
            packet["optional_shadow_exception_wait"]["confirm_flag_required_for_real_apply"],
            "--i-confirm-apply-shadow-only-exception",
        )
        self.assertTrue(packet["optional_shadow_exception_wait"]["real_apply_requires_execute_flag"])
        self.assertTrue(packet["optional_shadow_exception_wait"]["low_level_apply_script_is_not_operator_surface"])
        self.assertFalse(packet["prompt_to_artifact_completion_audit"]["complete"])
        self.assertIn("stage6_shadow_queue_allowed_or_shadow_passed", packet["prompt_to_artifact_completion_audit"]["missing"])
        self.assertIn("does_not_mark_stage6_reached", packet["non_goals"])
        self.assertFalse(packet["safety"]["broker_submit_allowed"])

    def test_packet_reports_stage6_reached_only_from_actual_stage6_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = root / "entry.json"
            stage6 = root / "stage6.json"
            entry.write_text(json.dumps({"stage6_reached": True, "entry_path_status": "STAGE6_REACHED"}), encoding="utf-8")
            stage6.write_text(
                json.dumps(
                    {
                        "readiness_decision": "PASS",
                        "shadow_queue_allowed": True,
                        "shadow_passed": False,
                        "safety": packet_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            packet = packet_mod.build_packet(
                "2026-05-14T10:30:00+09:00",
                entry_audit_path=entry,
                stage6_path=stage6,
                closure_plan_path=root / "missing_plan.json",
                router_path=root / "missing_router.json",
                operator_brief_path=root / "missing_brief.json",
                return_watch_path=root / "missing_watch.json",
                mandate_packet_path=root / "missing_mandate.json",
                dispatch_send_status_path=root / "missing_send.json",
            )

        self.assertEqual(packet["status"], "STAGE6_REACHED")
        self.assertTrue(packet["stage6_reached"])
        self.assertTrue(packet["prompt_to_artifact_completion_audit"]["complete"])

    def test_packet_still_reports_wait_when_entry_audit_is_temporarily_blocked_by_refresh_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = root / "entry.json"
            stage6 = root / "stage6.json"
            router = root / "router.json"
            watch = root / "watch.json"
            send = root / "send.json"
            entry.write_text(
                json.dumps(
                    {
                        "stage6_reached": False,
                        "entry_path_status": "BLOCK_ENTRY_PATH_NOT_READY",
                        "provider_dispatch_path": {
                            "status": "BLOCK_PROVIDER_PATH",
                            "checks": {"refresh_stack_passed": False},
                        },
                    }
                ),
                encoding="utf-8",
            )
            stage6.write_text(
                json.dumps(
                    {
                        "readiness_decision": "BLOCK",
                        "shadow_queue_allowed": False,
                        "shadow_passed": False,
                        "safety": packet_mod.SAFETY,
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
                                "status": "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            watch.write_text(
                json.dumps(
                    {
                        "status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
                        "blockers": ["dispatch_sent_confirmation_missing_or_invalid"],
                        "non_goals": ["does_not_run_refresh_before_returned_to_handoff_copy_review"],
                    }
                ),
                encoding="utf-8",
            )
            send.write_text(json.dumps({"status": "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION"}), encoding="utf-8")

            packet = packet_mod.build_packet(
                "2026-05-14T10:30:00+09:00",
                entry_audit_path=entry,
                stage6_path=stage6,
                closure_plan_path=root / "missing_plan.json",
                router_path=router,
                operator_brief_path=root / "missing_brief.json",
                return_watch_path=watch,
                mandate_packet_path=root / "missing_mandate.json",
                dispatch_send_status_path=send,
                returned_to_handoff_copy_review_path=root / "missing_copy.json",
            )

        self.assertEqual(packet["status"], "WAIT_OPERATOR_OR_PROVIDER_INPUT_TO_ADVANCE_STAGE6")
        self.assertTrue(packet["blocked_by_operator_or_provider"])
        self.assertFalse(packet["stage6_reached"])


if __name__ == "__main__":
    unittest.main()
