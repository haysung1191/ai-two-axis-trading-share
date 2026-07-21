from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_operator_status_brief.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_operator_status_brief", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
brief_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(brief_mod)


class Cand022OperatorStatusBriefTests(unittest.TestCase):
    def test_brief_surfaces_blocked_progress_dispatch_manifest_and_safety(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit = root / "audit.json"
            router = root / "router.json"
            closure = root / "closure.json"
            wait_packet = root / "wait_packet.json"
            progress = root / "progress.json"
            dispatch = root / "dispatch.json"
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            returned_copy = root / "returned_copy.json"
            send_status = root / "send_status.json"
            instruction = root / "instruction.json"
            slip = root / "slip.json"
            eml = root / "eml.json"
            confirmation_dry_run = root / "confirmation_dry_run.json"
            operator_decision = root / "operator_decision.json"
            watch_process = root / "watch_process.json"
            watch_continuity = root / "watch_continuity.json"
            shadow_contract = root / "shadow_contract.json"
            audit.write_text(
                json.dumps(
                    {
                        "completion_decision": "NOT_COMPLETE",
                        "failed_required_check_ids": ["provider_response_validated", "human_mandate_complete"],
                        "safety": {
                            "paper_enabled": False,
                            "live_enabled": False,
                            "broker_submit_allowed": False,
                            "order_intent_created": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            router.write_text(
                json.dumps(
                    {
                        "recommended_next_action_id": "fill_kis_pit_authoritative_intake",
                        "blocked_by_external_input": True,
                        "can_autonomously_enable_trading": False,
                        "autonomous_continuation": {
                            "decision": "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS",
                            "can_continue_local_work": False,
                            "allowed_local_actions": ["refresh_status_reports", "run_read_only_audits"],
                            "blocked_local_actions": [
                                "do_not_start_generic_model_search",
                                "do_not_create_order_intent",
                            ],
                            "why": "External dispatch/provider rows are missing.",
                        },
                        "action_router": [
                            {
                                "action_id": "send_external_provider_dispatch_packet",
                                "send_confirmation_editable_fields": ["sent_at", "sent_by", "recipient_or_channel"],
                                "send_confirmation_frozen_fields_must_match": [
                                    "freeze_dir",
                                    "frozen_email_markdown",
                                    "frozen_email_sha256",
                                    "frozen_attachment",
                                    "frozen_attachment_sha256",
                                    "expected_return_files",
                                ],
                                "send_confirmation_blockers": ["dispatch_sent_confirmation_missing"],
                            },
                            {
                                "action_id": "fill_kis_pit_authoritative_intake",
                                "primary_fill_workspace": "handoff",
                                "field_closure_checklist_csv": "closure.csv",
                            },
                            {
                                "action_id": "obtain_explicit_human_mandate_completion_instruction",
                                "status": "AWAITING_EXPLICIT_HUMAN_MANDATE_COMPLETION_INSTRUCTION",
                                "missing_fields": ["reporting_policy", "incident_policy_confirmed"],
                                "exact_instruction_file": r"C:\AI\reports\live_readiness\human_mandate_completion_instruction.latest.txt",
                                "guarded_dry_run_command": r"python .\apply_human_mandate_completion.py --operator-instruction-file C:\AI\reports\live_readiness\human_mandate_completion_instruction.latest.txt --dry-run",
                                "guarded_apply_command": r"python .\apply_human_mandate_completion.py --operator-instruction-file C:\AI\reports\live_readiness\human_mandate_completion_instruction.latest.txt",
                                "post_apply_verification_commands": ["python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120"],
                                "explicit_non_approval": "Completing human_mandate.yaml is not PAPER APPROVE and not LIVE APPROVE.",
                                "still_blocked_after_completion": ["KIS PIT/survivorship operation readiness"],
                            },
                            {
                                "action_id": "review_shadow_only_exception_contract",
                                "preflight_status": "WAIT_EXPLICIT_SHADOW_ONLY_EXCEPTION_INSTRUCTION",
                                "preflight_can_apply_now": False,
                                "preflight_blocked_checks": ["operator_instruction_exact_match"],
                                "guarded_dry_run_command": 'python .\\apply_cand022_shadow_only_exception.py --operator-instruction "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY" --dry-run',
                                "guarded_apply_command": 'python .\\apply_cand022_shadow_only_exception.py --operator-instruction "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY"',
                                "post_apply_verification_commands": [
                                    "python .\\build_cand022_stage6_shadow_readiness_packet.py",
                                    "python .\\run_stage6_shadow_loop.py --cycles 1 --dry-run",
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            closure.write_text(
                json.dumps(
                    {
                        "stage6_reached": False,
                        "stage6_readiness_decision": "BLOCK",
                        "blocker_count": 6,
                        "autonomous_continuation_decision": "WAIT_FOR_OPERATOR_OR_EXTERNAL_INPUT",
                        "guarded_shadow_exception_apply_support": {
                            "latest_apply_guard_ready": True,
                            "latest_apply_status": "DRY_RUN_READY_TO_APPLY_SHADOW_ONLY_EXCEPTION",
                        },
                        "guarded_human_mandate_apply_support": {
                            "latest_apply_guard_ready": True,
                            "latest_apply_status": "DRY_RUN_READY_TO_APPLY_HUMAN_MANDATE_COMPLETION",
                        },
                    }
                ),
                encoding="utf-8",
            )
            wait_packet.write_text(
                json.dumps(
                    {
                        "status": "WAIT_OPERATOR_OR_PROVIDER_INPUT_TO_ADVANCE_STAGE6",
                        "stage6_reached": False,
                        "recommended_next_action_id": "send_external_provider_dispatch_packet",
                        "blocked_by_operator_or_provider": True,
                        "dispatch_wait": {
                            "copy_review_before_refresh_enforced": True,
                            "return_watch_status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
                            "return_watch_refresh_result": None,
                            "after_return_copy_review": {
                                "status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                                "required_before_refresh": True,
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            progress.write_text(
                json.dumps(
                    {
                        "status": "BLOCK_HANDOFF_FILL_PROGRESS_OPEN",
                        "completed_rows": 0,
                        "total_rows": 18,
                        "open_rows": 18,
                        "completion_percent": 0.0,
                    }
                ),
                encoding="utf-8",
            )
            dispatch.write_text(
                json.dumps(
                    {
                        "status": "READY_EXTERNAL_DISPATCH_MANIFEST",
                        "email_markdown": {"path": "email.md", "sha256": "emailhash"},
                        "attachment": {"path": "handoff.zip", "sha256": "ziphash"},
                        "expected_return_files": [
                            "cand022_membership_response_draft.csv",
                            "cand022_event_or_no_event_response_draft.csv",
                            "cand022_replay_response_draft.csv",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            freeze.write_text(
                json.dumps(
                    {
                        "status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
                        "freeze_dir": "frozen",
                        "frozen_files": {
                            "email_markdown": {"path": "frozen/email.md", "sha256": "frozenemailhash"},
                            "attachment": {"path": "frozen/handoff.zip", "sha256": "frozenziphash"},
                        },
                    }
                ),
                encoding="utf-8",
            )
            receipt.write_text(
                json.dumps(
                    {
                        "status": "WAITING_FOR_RETURNED_PROVIDER_CSVS",
                        "return_staging_dir": "returned",
                        "expected_return_files": ["a.csv", "b.csv", "c.csv"],
                        "missing_files": ["a.csv", "b.csv", "c.csv"],
                    }
                ),
                encoding="utf-8",
            )
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
            send_status.write_text(
                json.dumps(
                    {
                        "status": "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION",
                        "send_confirmation_template": "template.json",
                        "send_confirmation_path": "sent.json",
                        "send_confirmation_present": False,
                        "send_confirmation_valid": False,
                    }
                ),
                encoding="utf-8",
            )
            instruction.write_text(
                json.dumps(
                    {
                        "status": "READY_MANUAL_DISPATCH_INSTRUCTION_PACKET",
                        "attachment_to_send": {"path": "frozen/handoff.zip", "sha256": "frozenziphash"},
                        "blockers": [],
                    }
                ),
                encoding="utf-8",
            )
            watch_process.write_text(
                json.dumps(
                    {
                        "status": "WATCHER_RUNNING",
                        "watch_running": True,
                        "watcher_process_ids": [4340],
                        "watcher_started": [
                            {
                                "process_id": 4340,
                                "started_at_kst": "2026-05-14T10:38:44+09:00",
                                "age_minutes": 47.4,
                                "cycles": 180,
                                "sleep_seconds": 60,
                                "expected_duration_minutes": 180.0,
                                "expected_end_at_kst": "2026-05-14T13:38:44+09:00",
                                "remaining_minutes": 132.6,
                            }
                        ],
                        "ready_for_unattended_wait": True,
                        "provider_return_watch_status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
                        "provider_return_watch_blockers": [
                            "dispatch_sent_confirmation_missing_or_invalid",
                            "returned_provider_csvs_missing",
                        ],
                        "provider_return_watch_policy": {
                            "copy_review_required_before_refresh": True,
                            "refresh_stack_invocation_policy": "manual_after_returned_to_handoff_copy_review_ready",
                            "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                            "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                        },
                        "copy_review_ready_for_manual_followup": False,
                        "recommended_command_if_not_running": (
                            "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120"
                        ),
                        "safety": {
                            "paper_enabled": False,
                            "live_enabled": False,
                            "broker_submit_allowed": False,
                            "private_submit_used": False,
                            "real_orders": 0,
                            "order_intent_created": False,
                            "pretrade_firewall_default_decision": "BLOCK",
                        },
                    }
                ),
                encoding="utf-8",
            )
            watch_continuity.write_text(
                json.dumps(
                    {
                        "status": "WATCHER_CONTINUITY_OK",
                        "needs_new_watcher": False,
                        "min_remaining_minutes": 14.7,
                        "max_remaining_minutes": 178.5,
                        "existing_watcher_process_ids": [4340, 5176],
                        "start_if_needed": False,
                        "start_command": (
                            "Start-Process -WindowStyle Hidden -FilePath python "
                            "-ArgumentList '.\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120' "
                            "-WorkingDirectory 'C:\\AI'"
                        ),
                        "safety": brief_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            slip.write_text(
                json.dumps(
                    {
                        "status": "READY_MANUAL_DISPATCH_EXECUTION_SLIP",
                        "send_now": {"attachment": "frozen/handoff.zip", "attachment_sha256": "frozenziphash"},
                        "after_actual_send": {
                            "preferred_helper_command": "python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send"
                        },
                        "blockers": [],
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
                        "subject": "CAND-022 source-backed provider response draft request",
                        "attachment_sha256": "frozenziphash",
                        "blockers": [],
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
                            "--sent-by \"<operator_or_account>\" --recipient-or-channel \"<provider_or_channel>\" --i-confirm-actual-send"
                        ),
                        "blockers": [],
                    }
                ),
                encoding="utf-8",
            )
            operator_decision.write_text(
                json.dumps(
                    {
                        "tiny_live_ready": False,
                        "do_not_auto_apply": True,
                        "decision_groups": [
                            {
                                "group_id": "kis_pit_survivorship_policy",
                                "operator_choices": [
                                    {"choice_id": "data_upgrade_required"},
                                    {"choice_id": "shadow_only_exception"},
                                ],
                                "operator_action_needed": "Choose one policy explicitly.",
                            }
                        ],
                        "forbidden_actions": ["do_not_enable_live"],
                    }
                ),
                encoding="utf-8",
            )
            shadow_contract.write_text(
                json.dumps(
                    {
                        "status": "READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT",
                        "is_approval": False,
                        "auto_apply_allowed": False,
                        "recommended_policy_choice": "shadow_only_exception",
                    }
                ),
                encoding="utf-8",
            )
            report = brief_mod.build_report(
                "2026-05-14T03:00:00+09:00",
                audit_path=audit,
                router_path=router,
                stage6_closure_plan_path=closure,
                stage6_operator_wait_packet_path=wait_packet,
                operator_decision_packet_path=operator_decision,
                provider_return_watch_process_status_path=watch_process,
                provider_watch_continuity_path=watch_continuity,
                handoff_progress_path=progress,
                dispatch_manifest_path=dispatch,
                dispatch_freeze_path=freeze,
                return_receipt_path=receipt,
                returned_to_handoff_copy_review_path=returned_copy,
                send_status_path=send_status,
                dispatch_instruction_packet_json=instruction,
                shadow_only_exception_contract_path=shadow_contract,
                manual_dispatch_execution_slip_path=slip,
                provider_dispatch_eml_draft_path=eml,
                dispatch_confirmation_dry_run_from_eml_path=confirmation_dry_run,
            )

        self.assertEqual(report["status"], "BLOCKED_NOT_COMPLETE")
        self.assertEqual(report["handoff_progress"]["open_rows"], 18)
        self.assertFalse(report["stage6_closure_plan"]["stage6_reached"])
        self.assertTrue(report["stage6_closure_plan"]["shadow_only_exception_guard_ready"])
        self.assertTrue(report["stage6_closure_plan"]["human_mandate_guard_ready"])
        self.assertEqual(
            report["stage6_operator_wait_packet"]["status"],
            "WAIT_OPERATOR_OR_PROVIDER_INPUT_TO_ADVANCE_STAGE6",
        )
        self.assertFalse(report["stage6_operator_wait_packet"]["stage6_reached"])
        self.assertTrue(report["stage6_operator_wait_packet"]["blocked_by_operator_or_provider"])
        self.assertTrue(report["stage6_operator_wait_packet"]["copy_review_before_refresh_enforced"])
        self.assertEqual(
            report["stage6_operator_wait_packet"]["return_watch_status"],
            "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
        )
        self.assertIsNone(report["stage6_operator_wait_packet"]["return_watch_refresh_result"])
        self.assertEqual(
            report["stage6_closure_plan"]["shadow_only_exception_latest_apply_status"],
            "DRY_RUN_READY_TO_APPLY_SHADOW_ONLY_EXCEPTION",
        )
        self.assertFalse(report["can_autonomously_enable_trading"])
        self.assertEqual(report["dispatch_manifest"]["status"], "READY_EXTERNAL_DISPATCH_MANIFEST")
        self.assertEqual(report["dispatch_manifest"]["attachment"], "handoff.zip")
        self.assertEqual(report["frozen_dispatch_packet"]["status"], "READY_FROZEN_EXTERNAL_DISPATCH_PACKET")
        self.assertEqual(report["frozen_dispatch_packet"]["attachment"], "frozen/handoff.zip")
        self.assertEqual(report["dispatch_file_policy"]["active_send_source"], "frozen_dispatch_packet")
        self.assertEqual(report["dispatch_file_policy"]["active_email_markdown"], "frozen/email.md")
        self.assertEqual(report["dispatch_file_policy"]["active_attachment"], "frozen/handoff.zip")
        self.assertEqual(report["dispatch_file_policy"]["mutable_latest_attachment_reference_only"], "handoff.zip")
        self.assertIn("Send only the frozen dispatch packet files", report["dispatch_file_policy"]["operator_warning"])
        self.assertEqual(report["return_receipt"]["status"], "WAITING_FOR_RETURNED_PROVIDER_CSVS")
        self.assertEqual(report["return_receipt"]["missing_files"], ["a.csv", "b.csv", "c.csv"])
        self.assertEqual(
            report["returned_to_handoff_copy_review"]["status"],
            "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertTrue(report["returned_to_handoff_copy_review"]["required_before_refresh"])
        self.assertIn(
            "membership_returned_file_missing",
            report["returned_to_handoff_copy_review"]["blockers"],
        )
        self.assertEqual(report["dispatch_send_status"]["status"], "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION")
        self.assertEqual(report["dispatch_send_status"]["send_confirmation_editable_fields"], ["sent_at", "sent_by", "recipient_or_channel"])
        self.assertEqual(report["manual_dispatch_instruction_packet"]["status"], "READY_MANUAL_DISPATCH_INSTRUCTION_PACKET")
        self.assertEqual(report["manual_dispatch_instruction_packet"]["attachment_to_send"], "frozen/handoff.zip")
        self.assertEqual(report["manual_dispatch_instruction_packet"]["attachment_sha256"], "frozenziphash")
        self.assertEqual(report["manual_dispatch_execution_slip"]["status"], "READY_MANUAL_DISPATCH_EXECUTION_SLIP")
        self.assertEqual(report["manual_dispatch_execution_slip"]["attachment_to_send"], "frozen/handoff.zip")
        self.assertEqual(report["manual_dispatch_execution_slip"]["attachment_sha256"], "frozenziphash")
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", report["manual_dispatch_execution_slip"]["helper_command"])
        self.assertEqual(report["provider_dispatch_eml_draft"]["status"], "READY_DISPATCH_EML_DRAFT_NO_SEND")
        self.assertEqual(report["provider_dispatch_eml_draft"]["eml_draft"], "frozen/draft.eml")
        self.assertEqual(
            report["dispatch_confirmation_dry_run_from_eml"]["status"],
            "READY_DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML",
        )
        self.assertEqual(
            report["dispatch_confirmation_dry_run_from_eml"]["dry_run_writer_status"],
            "DRY_RUN_READY_TO_WRITE_DISPATCH_SENT_CONFIRMATION",
        )
        self.assertFalse(report["dispatch_confirmation_dry_run_from_eml"]["confirmation_output_exists_after_dry_run"])
        self.assertEqual(report["provider_return_watch_process_status"]["status"], "WATCHER_RUNNING")
        self.assertTrue(report["provider_return_watch_process_status"]["watch_running"])
        self.assertEqual(report["provider_return_watch_process_status"]["watcher_process_ids"], [4340])
        self.assertEqual(
            report["provider_return_watch_process_status"]["watcher_started"][0]["expected_end_at_kst"],
            "2026-05-14T13:38:44+09:00",
        )
        self.assertEqual(report["provider_return_watch_process_status"]["watcher_started"][0]["remaining_minutes"], 132.6)
        self.assertIn(
            "run_cand022_provider_return_watch.py",
            report["provider_return_watch_process_status"]["recommended_command_if_not_running"],
        )
        self.assertEqual(
            report["provider_return_watch_process_status"]["provider_return_watch_policy"][
                "refresh_stack_invocation_policy"
            ],
            "manual_after_returned_to_handoff_copy_review_ready",
        )
        self.assertFalse(report["provider_return_watch_process_status"]["copy_review_ready_for_manual_followup"])
        self.assertEqual(report["provider_watch_continuity"]["status"], "WATCHER_CONTINUITY_OK")
        self.assertFalse(report["provider_watch_continuity"]["needs_new_watcher"])
        self.assertEqual(report["provider_watch_continuity"]["max_remaining_minutes"], 178.5)
        self.assertEqual(report["provider_watch_continuity"]["existing_watcher_process_ids"], [4340, 5176])
        self.assertIn("Start-Process -WindowStyle Hidden", report["provider_watch_continuity"]["start_command"])
        self.assertEqual(report["operator_decision_packet"]["status"], "READY_REVIEW_ONLY_PACKET")
        self.assertFalse(report["operator_decision_packet"]["tiny_live_ready"])
        self.assertTrue(report["operator_decision_packet"]["do_not_auto_apply"])
        self.assertFalse(report["operator_decision_packet"]["auto_apply_allowed"])
        self.assertIn("shadow_only_exception", report["operator_decision_packet"]["policy_choices"])
        self.assertEqual(
            report["operator_decision_packet"]["shadow_only_exception_contract"]["status"],
            "READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT",
        )
        self.assertFalse(report["operator_decision_packet"]["shadow_only_exception_contract"]["is_approval"])
        self.assertFalse(report["operator_decision_packet"]["shadow_only_exception_contract"]["auto_apply_allowed"])
        self.assertEqual(
            report["operator_decision_packet"]["shadow_only_exception_contract"]["preflight_status"],
            "WAIT_EXPLICIT_SHADOW_ONLY_EXCEPTION_INSTRUCTION",
        )
        self.assertFalse(report["operator_decision_packet"]["shadow_only_exception_contract"]["preflight_can_apply_now"])
        self.assertEqual(
            report["operator_decision_packet"]["shadow_only_exception_contract"]["preflight_blocked_checks"],
            ["operator_instruction_exact_match"],
        )
        self.assertIn(
            "apply_cand022_shadow_only_exception.py",
            report["operator_decision_packet"]["shadow_only_exception_contract"]["guarded_dry_run_command"],
        )
        self.assertIn(
            "build_cand022_stage6_shadow_readiness_packet.py",
            " ".join(report["operator_decision_packet"]["shadow_only_exception_contract"]["post_apply_verification_commands"]),
        )
        self.assertEqual(
            report["human_mandate_completion_packet"]["status"],
            "AWAITING_EXPLICIT_HUMAN_MANDATE_COMPLETION_INSTRUCTION",
        )
        self.assertIn("reporting_policy", report["human_mandate_completion_packet"]["missing_fields"])
        self.assertIn(
            "human_mandate_completion_instruction.latest.txt",
            report["human_mandate_completion_packet"]["exact_instruction_file"],
        )
        self.assertIn(
            "apply_human_mandate_completion.py",
            report["human_mandate_completion_packet"]["guarded_dry_run_command"],
        )
        self.assertIn("--dry-run", report["human_mandate_completion_packet"]["guarded_dry_run_command"])
        self.assertIn("--operator-instruction-file", report["human_mandate_completion_packet"]["guarded_apply_command"])
        self.assertIn(
            "run_cand022_provider_response_refresh_stack.py",
            " ".join(report["human_mandate_completion_packet"]["post_apply_verification_commands"]),
        )
        self.assertIn("not PAPER APPROVE", report["human_mandate_completion_packet"]["explicit_non_approval"])
        self.assertIn("Choose one policy explicitly", report["operator_decision_packet"]["operator_action_needed"])
        self.assertIn("expected_return_files", report["dispatch_send_status"]["send_confirmation_frozen_fields_must_match"])
        self.assertIn("dispatch_sent_confirmation_missing", report["dispatch_send_status"]["send_confirmation_blockers"])
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", report["single_next_action"])
        self.assertIn("--i-confirm-actual-send", report["single_next_action"])
        self.assertIn("kis_provider_returned_to_handoff_copy_review_latest.json", report["single_next_action"])
        self.assertIn("CAND-022_manual_dispatch_execution_slip.latest.md", report["single_next_action"])
        self.assertIn("kis_provider_external_dispatch_instruction_packet_latest.md", report["single_next_action"])
        self.assertIn("먼저", report["single_next_action"])
        self.assertIn("실제 provider 발송", report["single_next_action"])
        self.assertIn("반환 CSV가 도착하면", report["single_next_action"])
        self.assertEqual(
            report["autonomous_continuation"]["decision"],
            "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS",
        )
        self.assertFalse(report["autonomous_continuation"]["can_continue_local_work"])
        self.assertIn("do_not_start_generic_model_search", report["autonomous_continuation"]["blocked_local_actions"])
        self.assertIn("거래 안전", " ".join(report["korean_status_lines"]))
        self.assertIn("외부 입력 필요: true", " ".join(report["korean_status_lines"]))
        self.assertIn("자율 거래 활성화 가능: false", " ".join(report["korean_status_lines"]))
        self.assertIn("frozen dispatch packet READY", " ".join(report["korean_status_lines"]))
        self.assertIn("WAITING_FOR_RETURNED_PROVIDER_CSVS", " ".join(report["korean_status_lines"]))
        self.assertIn("BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW", " ".join(report["korean_status_lines"]))
        self.assertIn("copy_review_before_refresh=true", " ".join(report["korean_status_lines"]))
        self.assertIn("manual_after_returned_to_handoff_copy_review_ready", " ".join(report["korean_status_lines"]))
        self.assertIn("WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION", " ".join(report["korean_status_lines"]))
        self.assertIn("WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS", " ".join(report["korean_status_lines"]))
        self.assertIn("로컬 계속 가능: false", " ".join(report["korean_status_lines"]))
        self.assertIn("operator decision packet is review-only", " ".join(report["korean_status_lines"]))
        self.assertIn("READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT", " ".join(report["korean_status_lines"]))
        self.assertIn("READY_MANUAL_DISPATCH_EXECUTION_SLIP", " ".join(report["korean_status_lines"]))
        self.assertIn("READY_DISPATCH_EML_DRAFT_NO_SEND", " ".join(report["korean_status_lines"]))
        self.assertIn("READY_DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML", " ".join(report["korean_status_lines"]))
        self.assertIn("WATCHER_RUNNING", " ".join(report["korean_status_lines"]))
        self.assertIn("4340", " ".join(report["korean_status_lines"]))
        self.assertIn("WATCHER_CONTINUITY_OK", " ".join(report["korean_status_lines"]))
        self.assertIn("max_remaining=178.5", " ".join(report["korean_status_lines"]))
        self.assertIn("2026-05-14T13:38:44+09:00", " ".join(report["korean_status_lines"]))
        self.assertIn("shadow_guard_ready=true", " ".join(report["korean_status_lines"]))
        self.assertIn("mandate_guard_ready=true", " ".join(report["korean_status_lines"]))
        self.assertIn("does_not_mark_goal_complete", report["non_goals"])

        md = brief_mod.render_md(report)
        self.assertIn("CAND-022_manual_dispatch_execution_slip.latest.md", md)
        self.assertIn("kis_provider_external_dispatch_instruction_packet_latest.md", md)
        self.assertIn("## Active Send Files", md)
        self.assertIn("Attachment to send: `frozen/handoff.zip`", md)
        self.assertIn("Mutable latest attachment reference only: `handoff.zip`", md)
        self.assertIn("Manual dispatch instruction packet:", md)
        self.assertIn("Manual dispatch instruction status: `READY_MANUAL_DISPATCH_INSTRUCTION_PACKET`", md)
        self.assertIn("Korean manual dispatch slip status: `READY_MANUAL_DISPATCH_EXECUTION_SLIP`", md)
        self.assertIn("Korean manual dispatch slip attachment: `frozen/handoff.zip`", md)
        self.assertIn("Returned-to-handoff copy review status: `BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW`", md)
        self.assertIn("Returned-to-handoff copy review required before refresh: `true`", md)
        self.assertIn("Local .eml draft: `frozen/draft.eml`", md)
        self.assertIn("Local .eml draft status: `READY_DISPATCH_EML_DRAFT_NO_SEND`", md)
        self.assertIn("Confirmation dry-run status: `READY_DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML`", md)
        self.assertIn("Confirmation writer dry-run status: `DRY_RUN_READY_TO_WRITE_DISPATCH_SENT_CONFIRMATION`", md)
        self.assertIn("## Provider Return Watcher", md)
        self.assertIn("Status: `WATCHER_RUNNING`", md)
        self.assertIn("Watcher process ids: `4340`", md)
        self.assertIn("Watcher timing:", md)
        self.assertIn("## Provider Watch Continuity", md)
        self.assertIn("Status: `WATCHER_CONTINUITY_OK`", md)
        self.assertIn("Maximum remaining minutes: `178.5`", md)
        self.assertIn("2026-05-14T13:38:44+09:00", md)
        self.assertIn("132.6", md)
        self.assertIn("run_cand022_provider_return_watch.py", md)
        self.assertIn("## Stage 6 Closure Plan", md)
        self.assertIn("## Stage 6 Operator Wait Packet", md)
        self.assertIn("Copy-review before refresh enforced: `true`", md)
        self.assertIn("WAIT_OPERATOR_OR_PROVIDER_INPUT_TO_ADVANCE_STAGE6", md)
        self.assertIn("Shadow-only exception guard ready: `true`", md)
        self.assertIn("Human mandate guard ready: `true`", md)
        self.assertIn("DRY_RUN_READY_TO_APPLY_SHADOW_ONLY_EXCEPTION", md)
        self.assertIn("## Autonomous Continuation", md)
        self.assertIn("WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS", md)
        self.assertIn("Can continue local work: `false`", md)
        self.assertIn("do_not_start_generic_model_search", md)
        self.assertIn("## Operator Decision", md)
        self.assertIn("## Human Mandate Completion", md)
        self.assertIn("human_mandate_completion_instruction.latest.txt", md)
        self.assertIn("apply_human_mandate_completion.py", md)
        self.assertIn("Operator decision status: `READY_REVIEW_ONLY_PACKET`", md)
        self.assertIn("Operator decision tiny-live ready: `false`", md)
        self.assertIn("Operator decision auto-apply allowed: `false`", md)
        self.assertIn("shadow_only_exception", md)
        self.assertIn("Shadow-only exception contract status: `READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT`", md)
        self.assertIn("Shadow-only exception contract is approval: `false`", md)

    def test_brief_prioritizes_confirmation_when_returns_are_staged_but_dispatch_unconfirmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit = root / "audit.json"
            router = root / "router.json"
            progress = root / "progress.json"
            dispatch = root / "dispatch.json"
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            send_status = root / "send_status.json"
            instruction = root / "instruction.json"
            audit.write_text(json.dumps({"completion_decision": "NOT_COMPLETE", "failed_required_check_ids": []}), encoding="utf-8")
            router.write_text(
                json.dumps(
                    {
                        "recommended_next_action_id": "send_external_provider_dispatch_packet",
                        "blocked_by_external_input": True,
                        "can_autonomously_enable_trading": False,
                        "action_router": [
                            {
                                "action_id": "send_external_provider_dispatch_packet",
                                "send_confirmation_editable_fields": ["sent_at", "sent_by", "recipient_or_channel"],
                                "send_confirmation_frozen_fields_must_match": ["schema_version", "candidate_id", "safety"],
                                "send_confirmation_blockers": ["dispatch_sent_confirmation_missing"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            progress.write_text(json.dumps({"completed_rows": 0, "total_rows": 18, "open_rows": 18}), encoding="utf-8")
            dispatch.write_text(json.dumps({"status": "READY_EXTERNAL_DISPATCH_MANIFEST"}), encoding="utf-8")
            freeze.write_text(json.dumps({"status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET", "frozen_files": {}}), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "READY_RETURNED_PROVIDER_CSVS_FOR_REVIEW", "missing_files": []}), encoding="utf-8")
            send_status.write_text(
                json.dumps(
                    {
                        "status": "RETURNED_PROVIDER_CSVS_PRESENT_BUT_DISPATCH_UNCONFIRMED",
                        "send_confirmation_template": "template.json",
                        "send_confirmation_path": "sent.json",
                        "send_confirmation_present": False,
                        "send_confirmation_valid": False,
                    }
                ),
                encoding="utf-8",
            )
            instruction.write_text(json.dumps({"status": "READY_MANUAL_DISPATCH_INSTRUCTION_PACKET"}), encoding="utf-8")

            report = brief_mod.build_report(
                "2026-05-14T03:00:00+09:00",
                audit_path=audit,
                router_path=router,
                handoff_progress_path=progress,
                dispatch_manifest_path=dispatch,
                dispatch_freeze_path=freeze,
                return_receipt_path=receipt,
                send_status_path=send_status,
                dispatch_instruction_packet_json=instruction,
            )

        self.assertIn("실제 발송 확인이 없다", report["single_next_action"])
        self.assertIn("review-ready로 보기 전에", report["single_next_action"])
        self.assertIn("RETURNED_PROVIDER_CSVS_PRESENT_BUT_DISPATCH_UNCONFIRMED", " ".join(report["korean_status_lines"]))


if __name__ == "__main__":
    unittest.main()
