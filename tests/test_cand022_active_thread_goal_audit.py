from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_cand022_active_thread_goal_audit.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_active_thread_goal_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_mod)


class Cand022ActiveThreadGoalAuditTests(unittest.TestCase):
    EXPECTED_RETURN_FILES = [
        "cand022_membership_response_draft.csv",
        "cand022_event_or_no_event_response_draft.csv",
        "cand022_replay_response_draft.csv",
    ]

    def test_read_json_optional_returns_empty_dict_for_transient_empty_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.json"
            empty.write_text("", encoding="utf-8")

            result = audit_mod.read_json_optional(empty)

        self.assertEqual(result, {})

    def test_read_json_optional_reads_valid_dict_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            valid = Path(tmp) / "valid.json"
            valid.write_text(json.dumps({"ok": True}), encoding="utf-8")

            result = audit_mod.read_json_optional(valid)

        self.assertEqual(result, {"ok": True})

    def test_write_json_replaces_atomically_without_tmp_residue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "audit.latest.json"

            audit_mod.write_json(target, {"ok": True})

            result = json.loads(target.read_text(encoding="utf-8"))
            tmp_files = list(Path(tmp).glob("*.tmp"))

        self.assertEqual(result, {"ok": True})
        self.assertEqual(tmp_files, [])

    def test_audit_reports_not_complete_until_dispatch_confirmation_returns_and_tiny_live_complete(self) -> None:
        return_dir = Path(tempfile.mkdtemp())
        template_path = return_dir / "template.json"
        template_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "candidate_id": "CAND-022",
                    "sent_at": "YYYY-MM-DDTHH:MM:SS+09:00",
                    "expected_return_files": self.EXPECTED_RETURN_FILES,
                    "safety": audit_mod.SAFETY,
                }
            ),
            encoding="utf-8",
        )
        instruction_md = return_dir / "instruction.md"
        instruction_md.write_text(
            "\n".join(
                [
                    "Email markdown: `C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md`",
                    "Email sha256: `emailhash`",
                    "Attachment: `C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip`",
                    "Attachment sha256: `ziphash`",
                ]
            ),
            encoding="utf-8",
        )
        operator_checklist_md = return_dir / "operator_checklist.md"
        operator_checklist_md.write_text(
            "\n".join(
                [
                    "Email markdown: `C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md`",
                    "Email sha256: `emailhash`",
                    "Attachment: `C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip`",
                    "Attachment sha256: `ziphash`",
                    "Do not use mutable latest zip paths.",
                    "Post-confirmation watcher: `python .\\run_cand022_provider_return_watch.py --cycles 180`",
                    "First run copy-review: `python .\\build_kis_provider_returned_to_handoff_copy_review.py`",
                    "Refresh forbidden while copy-review status is `BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW`.",
                    "Refresh allowed only after copy-review status is `READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW`.",
                ]
            ),
            encoding="utf-8",
        )
        manual_dispatch_slip_md = return_dir / "manual_dispatch_slip.md"
        eml_draft = return_dir / "CAND-022_provider_dispatch_draft.eml"
        eml_draft.write_bytes(b"Subject: CAND-022 source-backed provider response draft request\r\n\r\nbody")
        operator_brief_md = return_dir / "operator_brief.md"
        operator_brief_md.write_text(
            "\n".join(
                [
                    "Email markdown to send: `C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md`",
                    "Email sha256: `emailhash`",
                    "Attachment to send: `C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip`",
                    "Attachment sha256: `ziphash`",
                    "The mutable latest email/zip paths are reference-only.",
                    "Policy review: operator decision packet is review-only; shadow_only_exception requires explicit operator choice",
                    "## Operator Decision",
                    "Operator decision status: `READY_REVIEW_ONLY_PACKET`",
                    "Operator decision tiny-live ready: `false`",
                    "Operator decision auto-apply allowed: `false`",
                    str(manual_dispatch_slip_md),
                    "Korean manual dispatch slip status: `READY_MANUAL_DISPATCH_EXECUTION_SLIP`",
                    "Korean manual dispatch slip attachment: `C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip`",
                    "Korean manual dispatch slip attachment sha256: `ziphash`",
                ]
            ),
            encoding="utf-8",
        )
        operator_decision_md = return_dir / "operator_decision.md"
        operator_decision_md.write_text(
            "\n".join(
                [
                    "This packet is approval: `false`",
                    "Auto-apply allowed: `false`",
                    "shadow_only_exception",
                    "still block paper/live/order intents",
                    "do_not_create_order_intent_from_this_packet",
                    "do_not_enable_paper",
                    "do_not_enable_live",
                    "do_not_enable_broker_submit",
                    '"pretrade_firewall_default_decision": "BLOCK"',
                ]
            ),
            encoding="utf-8",
        )
        shadow_exception_contract_md = return_dir / "shadow_exception_contract.md"
        shadow_exception_contract_md.write_text(
            "\n".join(
                [
                    "This file is approval: `false`",
                    "Auto-apply allowed: `false`",
                    "Contract changes allowed by this file: `false`",
                    "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY",
                    "do_not_create_order_intent",
                    "do_not_enable_paper",
                    "do_not_enable_live",
                    "do_not_enable_broker_submit",
                    '"pretrade_firewall_default_decision": "BLOCK"',
                ]
            ),
            encoding="utf-8",
        )
        manual_dispatch_slip_md = return_dir / "manual_dispatch_slip.md"
        manual_dispatch_slip_md.write_text(
            "\n".join(
                [
                    "Manual dispatch slip: READY",
                    "Pre-send verification: PASS_PRESEND_ACTIVE_SEND_FILES_VERIFIED",
                    "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                    "ziphash",
                    "write_cand022_dispatch_sent_confirmation.py",
                    "Post-write sequence contract",
                    "immediate_safe_commands",
                    "copy_review_required_before_refresh",
                    '"pretrade_firewall_default_decision": "BLOCK"',
                ]
            ),
            encoding="utf-8",
        )
        guard_path = return_dir / "DISABLE_DUAL_REPO_RESEARCH_LOOP"
        guard_path.write_text("disabled_by_test\n", encoding="utf-8")
        fixtures = {
            str(audit_mod.TINY_LIVE_AUDIT): {
                "completion_decision": "NOT_COMPLETE",
                "failed_required_check_ids": ["provider_response_validated"],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.NEXT_ACTION_ROUTER): {
                "recommended_next_action_id": "send_external_provider_dispatch_packet",
                "can_autonomously_enable_trading": False,
                "blocked_by_external_input": True,
                "autonomous_continuation": {
                    "decision": "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS",
                    "can_continue_local_work": False,
                    "allowed_local_actions": ["refresh_status_reports", "run_read_only_audits"],
                    "blocked_local_actions": [
                        "do_not_start_generic_model_search",
                        "do_not_create_order_intent",
                    ],
                },
                "action_router": [
                    {
                        "action_id": "send_external_provider_dispatch_packet",
                        "frozen_email_markdown": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md",
                        "frozen_email_sha256": "emailhash",
                        "frozen_attachment": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                        "frozen_attachment_sha256": "ziphash",
                        "manual_dispatch_instruction_packet_md": "C:\\AI\\reports\\operations\\kis_provider_external_dispatch_instruction_packet_latest.md",
                        "after_return_copy_review_required_before_refresh": True,
                        "after_return_refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                        "after_return_refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                        "action_safety": audit_mod.SAFETY,
                    },
                    {
                        "action_id": "review_shadow_only_exception_contract",
                        "status": "READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT",
                        "is_approval": False,
                        "auto_apply_allowed": False,
                        "forbidden_actions": ["do_not_create_order_intent", "do_not_enable_live"],
                    }
                ],
            },
            str(audit_mod.OPERATOR_BRIEF): {
                "single_next_action": "use C:\\AI\\reports\\operations\\kis_provider_external_dispatch_instruction_packet_latest.md",
                "safety": audit_mod.SAFETY,
                "dispatch_file_policy": {
                    "active_email_markdown": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md",
                    "active_email_sha256": "emailhash",
                    "active_attachment": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                    "active_attachment_sha256": "ziphash",
                },
                "operator_decision_packet": {
                    "status": "READY_REVIEW_ONLY_PACKET",
                    "tiny_live_ready": False,
                    "auto_apply_allowed": False,
                    "policy_choices": ["data_upgrade_required", "shadow_only_exception"],
                },
            },
            str(audit_mod.REFRESH_STACK): {
                "status": "PASS_REFRESH_STACK_COMPLETED",
                "script_step_count": 47,
                "unique_script_count": 46,
                "failed_scripts": [],
                "safety": audit_mod.SAFETY,
                "scripts": [
                    "build_kis_provider_returned_handoff_staging_verifier.py",
                    "build_kis_provider_external_return_receipt_status.py",
                    "build_kis_provider_external_dispatch_send_status.py",
                    "build_cand022_active_thread_goal_audit.py",
                ],
            },
            str(audit_mod.PROVIDER_RETURN_WATCH): {
                "status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
                "blockers": [
                    "dispatch_sent_confirmation_missing_or_invalid",
                    "returned_provider_csvs_missing",
                ],
                "run_refresh_when_ready": False,
                "copy_review_required_before_refresh": True,
                "refresh_stack_invocation_policy": "manual_after_returned_to_handoff_copy_review_ready",
                "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                "non_goals": [
                    "does_not_send_email",
                    "does_not_write_dispatch_confirmation",
                    "does_not_copy_or_generate_provider_csvs",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.PROVIDER_RETURN_WATCH_PROCESS_STATUS): {
                "generated_at": "2026-05-14T04:59:00+09:00",
                "status": "WATCHER_RUNNING",
                "watch_running": True,
                "watcher_process_ids": [4340],
                "ready_for_unattended_wait": True,
                "provider_return_watch_status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
                "provider_return_watch_policy": {
                    "copy_review_required_before_refresh": True,
                    "refresh_stack_invocation_policy": "manual_after_returned_to_handoff_copy_review_ready",
                    "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                    "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                },
                "copy_review_ready_for_manual_followup": False,
                "non_goals": [
                    "does_not_start_watcher",
                    "does_not_stop_processes",
                    "does_not_send_email",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.PROVIDER_WATCH_CONTINUITY): {
                "status": "WATCHER_CONTINUITY_OK",
                "needs_new_watcher": False,
                "min_remaining_minutes": 12.0,
                "max_remaining_minutes": 179.0,
                "existing_watcher_process_ids": [4340, 5176],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.HUMAN_MANDATE_COMPLETION_PACKET): {
                "status": "AWAITING_EXPLICIT_HUMAN_MANDATE_COMPLETION_INSTRUCTION",
                "do_not_auto_apply": True,
                "caps_present": True,
                "can_complete_after_explicit_instruction": True,
                "missing_fields": ["reporting_policy", "incident_policy_confirmed", "mandate_status_complete"],
                "exact_instruction_to_apply_recommended_values": "UPDATE HUMAN_MANDATE REPORTING_POLICY checkpoint_email_frequency_hours=3",
                "exact_instruction_file": "C:\\AI\\reports\\live_readiness\\human_mandate_completion_instruction.latest.txt",
                "guarded_dry_run_command": "python .\\apply_human_mandate_completion.py --operator-instruction-file C:\\AI\\reports\\live_readiness\\human_mandate_completion_instruction.latest.txt --dry-run",
                "guarded_apply_command": "python .\\apply_human_mandate_completion.py --operator-instruction-file C:\\AI\\reports\\live_readiness\\human_mandate_completion_instruction.latest.txt",
                "post_apply_verification_commands": ["python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120"],
                "explicit_non_approval": "Completing human_mandate.yaml is not PAPER APPROVE and not LIVE APPROVE.",
                "forbidden_actions": ["do_not_modify_human_mandate_without_explicit_user_instruction", "do_not_create_order_intent"],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.BLOCKED_WAIT_STATE): {
                "status": "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS",
                "can_continue_local_work": False,
                "blockers": [],
                "blocked_local_actions": [
                    "do_not_start_generic_model_search",
                    "do_not_create_order_intent",
                ],
                "non_goals": [
                    "does_not_send_email",
                    "does_not_create_dispatch_confirmation",
                    "does_not_fill_source_rows",
                    "does_not_enable_paper_live_broker_submit_or_order_intent",
                    "does_not_mark_goal_complete",
                ],
                "missing_or_blocked_check_ids": [
                    "dispatch_sent_confirmation_recorded",
                    "returned_provider_csvs_received",
                    "source_backed_rows_complete",
                    "tiny_live_preconditions_complete",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.STAGE6_WAIT_PACKET): {
                "status": "WAIT_OPERATOR_OR_PROVIDER_INPUT_TO_ADVANCE_STAGE6",
                "stage6_reached": False,
                "blocked_by_operator_or_provider": True,
                "dispatch_wait": {
                    "safe_watch_command_after_dispatch": (
                        "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60"
                    ),
                    "safe_watch_command_report_only": (
                        "python .\\run_cand022_provider_return_watch.py --cycles 1 --sleep-seconds 0 --no-refresh"
                    ),
                },
                "prompt_to_artifact_completion_audit": {
                    "complete": False,
                    "missing": ["stage6_shadow_queue_allowed_or_shadow_passed"],
                },
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.STAGE6_BLOCKER_CLOSURE_PLAN): {
                "objective": "Reach Stage 6 Shadow Operation without enabling paper/live/broker submit/order intent.",
                "stage6_reached": False,
                "stage6_readiness_decision": "BLOCK",
                "shadow_queue_allowed": False,
                "shadow_passed": False,
                "blocker_count": 6,
                "blockers": [
                    "fresh_non_stale_signal_observation_missing",
                    "gatekeeper_stage5_to_stage6_transition_blocked",
                    "human_mandate_incomplete",
                    "kis_data_operation_ready_not_verified",
                    "point_in_time_universe_not_verified",
                    "survivorship_free_status_not_verified",
                ],
                "guarded_shadow_exception_apply_support": {
                    "latest_apply_guard_ready": True,
                    "latest_apply_dry_run": True,
                    "latest_apply_wrote_acceptance": False,
                    "latest_apply_appended_shadow_queue": False,
                },
                "guarded_human_mandate_apply_support": {
                    "latest_apply_guard_ready": True,
                    "latest_apply_dry_run": True,
                    "latest_apply_wrote_human_mandate": False,
                },
                "non_goals": ["does_not_mark_stage6_reached"],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.STAGE6_OPERATING_STATUS): {
                "status": "STAGE6_RUNNING_CAND022_NOT_COMPLETE",
                "broader_stage6_operation": {
                    "running": True,
                    "shadow_queue_candidates": ["CAND-001"],
                    "cycles_completed": 5,
                    "cycles_requested": 288,
                },
                "cand022_stage6": {
                    "stage6_reached": False,
                    "completion_decision": "NOT_COMPLETE",
                    "completion_percent": 90.5,
                },
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.MANUAL_DISPATCH_EXECUTION_SLIP): {
                "status": "READY_MANUAL_DISPATCH_EXECUTION_SLIP",
                "blockers": [],
                "send_now": {
                    "subject": "CAND-022 source-backed provider response draft request",
                    "email_markdown": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md",
                    "email_sha256": "emailhash",
                    "attachment": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                    "attachment_sha256": "ziphash",
                },
                "after_actual_send": {
                    "preferred_helper_command": "python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send",
                    "post_write_sequence_contract": {
                        "immediate_safe_commands": [
                            "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120"
                        ],
                        "copy_review_required_before_refresh": True,
                        "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                        "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                    },
                },
                "checks": {
                    "presend_verified": True,
                    "send_files_match_presend_verifier": True,
                },
                "non_goals": [
                    "does_not_send_email",
                    "does_not_enable_paper_live_broker_submit_or_order_intent",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.STAGE6_USER_ACTION_CARD): {
                "status": "READY_STAGE6_USER_ACTION_CARD",
                "stage6_reached": False,
                "stage6_completion_decision": "NOT_COMPLETE",
                "stage6_completion_percent": 85.7,
                "recommended_path": {
                    "action_id": "send_external_provider_dispatch_packet",
                    "eml_draft": str(eml_draft),
                    "eml_draft_status": "READY_DISPATCH_EML_DRAFT_NO_SEND",
                    "after_send_helper_command": (
                        "python .\\write_cand022_dispatch_sent_confirmation.py --sent-at \"<timezone-aware sent time>\" "
                        "--sent-by \"<operator_or_account>\" --recipient-or-channel \"<provider_or_channel>\" --i-confirm-actual-send"
                    ),
                    "post_confirmation_watch_command": (
                        "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120"
                    ),
                    "post_write_sequence_contract": {
                        "immediate_safe_commands": [
                            "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120"
                        ],
                        "copy_review_required_before_refresh": True,
                        "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                        "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                    },
                },
                "optional_shadow_only_exception": {
                    "is_approval": False,
                    "auto_apply_allowed": False,
                    "exact_instruction": "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY",
                },
                "non_goals": [
                    "does_not_send_email",
                    "does_not_write_dispatch_confirmation",
                    "does_not_copy_or_generate_provider_csvs",
                    "does_not_enable_paper_live_broker_submit_or_order_intent",
                    "does_not_mark_stage6_reached",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.PROVIDER_DISPATCH_EML_DRAFT): {
                "status": "READY_DISPATCH_EML_DRAFT_NO_SEND",
                "eml_draft": str(eml_draft),
                "to_placeholder": "provider_or_channel_to_fill@example.invalid",
                "subject": "CAND-022 source-backed provider response draft request",
                "email_markdown": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md",
                "email_sha256": "emailhash",
                "attachment": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                "attachment_sha256": "ziphash",
                "blockers": [],
                "non_goals": [
                    "does_not_send_email",
                    "does_not_write_dispatch_confirmation",
                    "does_not_copy_or_generate_provider_csvs",
                    "does_not_enable_paper_live_broker_submit_or_order_intent",
                    "does_not_mark_stage6_reached",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML): {
                "status": "READY_DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML",
                "dry_run_writer_status": "DRY_RUN_READY_TO_WRITE_DISPATCH_SENT_CONFIRMATION",
                "confirmation_output_path": str(return_dir / "sent.json"),
                "confirmation_output_exists_after_dry_run": False,
                "actual_after_send_command_template": (
                    'python .\\write_cand022_dispatch_sent_confirmation.py --sent-at "<timezone-aware sent time>" '
                    '--sent-by "<operator_or_account>" --recipient-or-channel "<provider_or_channel>" --i-confirm-actual-send'
                ),
                "dry_run_writer_report": {
                    "planned_after_write_commands": [
                        "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120",
                    ],
                },
                "blockers": [],
                "non_goals": [
                    "does_not_send_email",
                    "does_not_write_dispatch_confirmation",
                    "does_not_copy_or_generate_provider_csvs",
                    "does_not_enable_paper_live_broker_submit_or_order_intent",
                    "does_not_mark_stage6_reached",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML): {
                "status": "READY_DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML",
                "dry_run_writer_status": "DRY_RUN_READY_TO_WRITE_DISPATCH_SENT_CONFIRMATION",
                "confirmation_output_path": str(return_dir / "sent.json"),
                "confirmation_output_exists_after_dry_run": False,
                "actual_after_send_command_template": (
                    'python .\\write_cand022_dispatch_sent_confirmation.py --sent-at "<timezone-aware sent time>" '
                    '--sent-by "<operator_or_account>" --recipient-or-channel "<provider_or_channel>" --i-confirm-actual-send'
                ),
                "dry_run_writer_report": {
                    "planned_after_write_commands": [
                        "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120",
                    ],
                },
                "blockers": [],
                "non_goals": [
                    "does_not_send_email",
                    "does_not_write_dispatch_confirmation",
                    "does_not_copy_or_generate_provider_csvs",
                    "does_not_enable_paper_live_broker_submit_or_order_intent",
                    "does_not_mark_stage6_reached",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.OPERATOR_DECISION_PACKET): {
                "tiny_live_ready": False,
                "do_not_auto_apply": True,
                "decision_groups": [
                    {
                        "group_id": "kis_pit_survivorship_policy",
                        "operator_choices": [
                            {
                                "choice_id": "shadow_only_exception",
                                "effect": "Allow no-submit shadow observation with explicit caveats; still block paper/live/order intents.",
                            }
                        ],
                    }
                ],
                "forbidden_actions": [
                    "do_not_create_order_intent_from_this_packet",
                    "do_not_enable_paper",
                    "do_not_enable_live",
                    "do_not_enable_broker_submit",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.SHADOW_ONLY_EXCEPTION_CONTRACT): {
                "status": "READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT",
                "is_approval": False,
                "auto_apply_allowed": False,
                "contract_changes_allowed_by_this_file": False,
                "recommended_policy_choice": "shadow_only_exception",
                "forbidden_actions": [
                    "do_not_create_order_intent",
                    "do_not_enable_paper",
                    "do_not_enable_live",
                    "do_not_enable_broker_submit",
                    "do_not_submit_orders",
                    "do_not_treat_this_contract_as_approval",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.INSTRUCTION_PACKET): {
                "status": "READY_MANUAL_DISPATCH_INSTRUCTION_PACKET",
                "attachment_to_send": {
                    "path": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                    "sha256": "ziphash",
                },
                "email": {
                    "source_markdown": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md",
                    "source_sha256": "emailhash",
                },
                "expected_return_files": self.EXPECTED_RETURN_FILES,
                "return_staging_dir": str(return_dir),
                "safety": audit_mod.SAFETY,
                "confirmation_after_send": {
                    "preferred_helper_command": (
                        "python .\\write_cand022_dispatch_sent_confirmation.py --sent-at \"<timezone-aware sent time>\" "
                        "--sent-by \"<operator_or_account>\" --recipient-or-channel \"<provider_or_channel>\" --i-confirm-actual-send"
                    )
                },
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.OPERATOR_CHECKLIST): {
                "status": "READY_OPERATOR_SEND_CONFIRMATION_CHECKLIST",
                "send_confirmation": {
                    "helper": "C:\\AI\\write_cand022_dispatch_sent_confirmation.py",
                    "preferred_helper_command": (
                        "python .\\write_cand022_dispatch_sent_confirmation.py --sent-at \"<timezone-aware sent time>\" "
                        "--sent-by \"<operator_or_account>\" --recipient-or-channel \"<provider_or_channel>\" --i-confirm-actual-send"
                    ),
                    "post_confirmation_watch_command": "python .\\run_cand022_provider_return_watch.py --cycles 180",
                },
                "operator_steps": ["Do not hand-edit frozen metadata. The helper preserves safety."],
                "after_return": {
                    "copy_review_command": "python .\\build_kis_provider_returned_to_handoff_copy_review.py",
                    "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                    "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                },
                "send_files": {
                    "email_markdown": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md",
                    "email_sha256": "emailhash",
                    "attachment": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                    "attachment_sha256": "ziphash",
                },
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.GUIDANCE_CONSISTENCY): {
                "status": "PASS_DISPATCH_GUIDANCE_HELPER_FIRST",
                "blockers": [],
                "watch_token": "run_cand022_provider_return_watch.py",
                "watch_required_targets": [
                    "operator_status_brief_md",
                    "manual_dispatch_execution_slip_json",
                    "manual_dispatch_execution_slip_md",
                ],
                "inspections": [
                    {
                        "name": "codex_handover_md",
                        "passed": True,
                        "has_helper_token": True,
                        "has_confirm_flag": True,
                        "stale_phrase_hits": [],
                    },
                    {
                        "name": "blocked_handoff_md",
                        "passed": True,
                        "has_helper_token": True,
                        "has_confirm_flag": True,
                        "stale_phrase_hits": [],
                    },
                    {
                        "name": "operator_status_brief_md",
                        "passed": True,
                        "has_helper_token": True,
                        "has_confirm_flag": True,
                        "has_watch_token": True,
                        "stale_phrase_hits": [],
                    },
                    {
                        "name": "manual_dispatch_execution_slip_json",
                        "passed": True,
                        "has_helper_token": True,
                        "has_confirm_flag": True,
                        "has_watch_token": True,
                        "stale_phrase_hits": [],
                    },
                    {
                        "name": "manual_dispatch_execution_slip_md",
                        "passed": True,
                        "has_helper_token": True,
                        "has_confirm_flag": True,
                        "has_watch_token": True,
                        "stale_phrase_hits": [],
                    },
                ],
            },
            str(audit_mod.PRESEND_VERIFIER): {
                "status": "PASS_PRESEND_ACTIVE_SEND_FILES_VERIFIED",
                "blockers": [],
                "checks": {
                    "operator_brief_uses_frozen_source": True,
                    "active_email_path_matches_frozen": True,
                    "active_attachment_path_matches_frozen": True,
                    "active_email_sha256_matches_frozen": True,
                    "active_attachment_sha256_matches_frozen": True,
                },
                "active_send_files": {
                    "email_markdown": {
                        "path": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md",
                        "sha256": "emailhash",
                    },
                    "attachment": {
                        "path": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                        "sha256": "ziphash",
                    },
                },
                "expected_frozen_hashes": {"email_sha256": "emailhash", "attachment_sha256": "ziphash"},
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.SEND_STATUS): {
                "status": "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION",
                "send_confirmation_template": str(template_path),
                "send_confirmation_present": False,
                "send_confirmation_valid": False,
                "send_confirmation_blockers": ["dispatch_sent_confirmation_missing"],
            },
            str(audit_mod.RETURN_RECEIPT): {
                "status": "WAITING_FOR_RETURNED_PROVIDER_CSVS",
                "send_confirmation_path": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\send_confirmations\\CAND-022_dispatch_sent_latest.json",
                "send_confirmation_valid": False,
                "send_confirmation_blockers": ["dispatch_sent_confirmation_missing"],
                "return_staging_dir": str(return_dir),
                "expected_return_files": self.EXPECTED_RETURN_FILES,
                "missing_files": self.EXPECTED_RETURN_FILES,
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.HANDOFF_FILL_PROGRESS): {
                "status": "BLOCK_HANDOFF_FILL_PROGRESS_OPEN",
                "completed_rows": 0,
                "total_rows": 18,
                "open_rows": 18,
            },
        }

        def fake_read(path: Path) -> dict:
            if str(path) in fixtures:
                return fixtures[str(path)]
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8-sig"))
            return {}

        with patch.object(audit_mod, "read_json_optional", side_effect=fake_read), patch.object(
            audit_mod, "INSTRUCTION_PACKET_MD", instruction_md
        ), patch.object(
            audit_mod, "OPERATOR_DECISION_PACKET_MD", operator_decision_md
        ), patch.object(
            audit_mod, "SHADOW_ONLY_EXCEPTION_CONTRACT_MD", shadow_exception_contract_md
        ), patch.object(
            audit_mod, "MANUAL_DISPATCH_EXECUTION_SLIP_MD", manual_dispatch_slip_md
        ), patch.object(
            audit_mod, "OPERATOR_BRIEF_MD", operator_brief_md
        ), patch.object(
            audit_mod, "OPERATOR_CHECKLIST_MD", operator_checklist_md
        ), patch.object(
            audit_mod, "DUAL_REPO_RESEARCH_LOOP_GUARD", guard_path
        ):
            report = audit_mod.build_report("2026-05-14T05:00:00+09:00")

        self.assertEqual(report["status"], "NOT_COMPLETE_BLOCKED_BY_EXTERNAL_DISPATCH_AND_PROVIDER_ROWS")
        self.assertTrue(report["do_not_mark_goal_complete"])
        self.assertIn("dispatch_sent_confirmation_recorded", report["missing_or_blocked_check_ids"])
        self.assertIn("CAND-022_manual_dispatch_execution_slip.latest.md", report["single_next_action"])
        self.assertIn("kis_provider_external_dispatch_instruction_packet_latest.md", report["single_next_action"])
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", report["single_next_action"])
        self.assertIn("--i-confirm-actual-send", report["single_next_action"])
        self.assertIn("run_cand022_provider_return_watch.py", report["single_next_action"])
        self.assertIn("--cycles 180", report["single_next_action"])
        self.assertIn("--timeout-seconds 120", report["single_next_action"])
        self.assertIn("kis_provider_returned_to_handoff_copy_review_latest.json", report["single_next_action"])
        self.assertIn("run_cand022_provider_response_refresh_stack.py", report["single_next_action"])
        self.assertIn("returned_provider_csvs_received", report["missing_or_blocked_check_ids"])
        self.assertIn("source_backed_rows_complete", report["missing_or_blocked_check_ids"])
        self.assertIn("tiny_live_preconditions_complete", report["missing_or_blocked_check_ids"])
        self.assertNotIn("safety_invariant_across_dispatch_surfaces", report["missing_or_blocked_check_ids"])
        self.assertNotIn("dual_repo_research_loop_guard_preserved", report["missing_or_blocked_check_ids"])
        self.assertNotIn("provider_return_watch_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("provider_return_watch_process_status_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("provider_watch_continuity_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("human_mandate_completion_packet_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("manual_dispatch_packet_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("instruction_packet_matches_frozen_active_send_files", report["missing_or_blocked_check_ids"])
        self.assertNotIn("next_action_router_dispatch_matches_frozen_active_send_files", report["missing_or_blocked_check_ids"])
        self.assertNotIn("next_action_router_dispatch_action_safety_locked", report["missing_or_blocked_check_ids"])
        self.assertNotIn("manual_dispatch_execution_slip_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("manual_dispatch_execution_slip_markdown_surfaces_safe_flow", report["missing_or_blocked_check_ids"])
        self.assertNotIn("provider_dispatch_eml_draft_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("dispatch_confirmation_dry_run_from_eml_ready", report["missing_or_blocked_check_ids"])
        dry_run_row = next(row for row in report["checklist"] if row["id"] == "dispatch_confirmation_dry_run_from_eml_ready")
        self.assertIn("run_cand022_provider_return_watch.py", str(dry_run_row["observed"]["planned_after_write_commands"]))
        self.assertNotIn("stage6_user_action_card_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("operator_status_brief_surfaces_manual_dispatch_slip", report["missing_or_blocked_check_ids"])
        self.assertNotIn("instruction_packet_markdown_surfaces_frozen_hashes", report["missing_or_blocked_check_ids"])
        self.assertNotIn("instruction_return_contract_matches_receipt", report["missing_or_blocked_check_ids"])
        self.assertNotIn("refresh_stack_dependency_order_locked", report["missing_or_blocked_check_ids"])
        self.assertNotIn("frozen_active_send_files_verified", report["missing_or_blocked_check_ids"])
        self.assertNotIn("operator_status_brief_markdown_surfaces_active_send_hashes", report["missing_or_blocked_check_ids"])
        self.assertNotIn("operator_status_brief_surfaces_operator_decision_policy", report["missing_or_blocked_check_ids"])
        self.assertNotIn("operator_status_brief_json_surfaces_operator_decision_policy", report["missing_or_blocked_check_ids"])
        self.assertNotIn("guarded_dispatch_confirmation_helper_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("dispatch_confirmation_helper_post_write_refresh_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("dispatch_confirmation_helper_regression_tests_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("operator_checklist_helper_first_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("operator_checklist_markdown_surfaces_frozen_hashes", report["missing_or_blocked_check_ids"])
        self.assertNotIn("operator_checklist_copy_review_gate_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("dispatch_guidance_consistency_passed", report["missing_or_blocked_check_ids"])
        self.assertNotIn("dispatch_stale_freeze_surface_audit_passed", report["missing_or_blocked_check_ids"])
        self.assertNotIn("operator_decision_packet_review_only", report["missing_or_blocked_check_ids"])
        self.assertNotIn("operator_decision_packet_markdown_review_only", report["missing_or_blocked_check_ids"])
        self.assertNotIn("shadow_only_exception_contract_review_only", report["missing_or_blocked_check_ids"])
        self.assertNotIn("shadow_only_exception_contract_markdown_review_only", report["missing_or_blocked_check_ids"])
        self.assertNotIn("next_action_router_surfaces_shadow_exception_review_only", report["missing_or_blocked_check_ids"])
        self.assertNotIn("next_action_router_waits_for_external_dispatch_or_provider_rows", report["missing_or_blocked_check_ids"])
        self.assertNotIn("blocked_wait_state_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("stage6_operator_wait_packet_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("stage6_blocker_closure_plan_surfaces_stage_contract", report["missing_or_blocked_check_ids"])
        self.assertNotIn("stage6_operating_status_current", report["missing_or_blocked_check_ids"])
        self.assertNotIn("dispatch_confirmation_template_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("dispatch_confirmation_template_schema_locked", report["missing_or_blocked_check_ids"])
        self.assertNotIn("dispatch_confirmation_schema_validator_guard_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("dispatch_send_status_isolated_guard_tests_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("return_staging_ready", report["missing_or_blocked_check_ids"])
        self.assertNotIn("return_staging_readme_current", report["missing_or_blocked_check_ids"])
        readme_row = next(row for row in report["checklist"] if row["id"] == "return_staging_readme_current")
        self.assertTrue(readme_row["observed"]["contains_copy_review_requirement"])
        self.assertNotIn("return_receipt_dispatch_confirmation_guard_ready", report["missing_or_blocked_check_ids"])
        self.assertIn("instruction_packet", report["source_files"])
        self.assertIn("instruction_packet_md", report["source_files"])
        self.assertIn("operator_checklist", report["source_files"])
        self.assertIn("operator_checklist_md", report["source_files"])
        self.assertIn("operator_decision_packet", report["source_files"])
        self.assertIn("operator_decision_packet_md", report["source_files"])
        self.assertIn("shadow_only_exception_contract", report["source_files"])
        self.assertIn("shadow_only_exception_contract_md", report["source_files"])
        self.assertIn("next_action_router", report["source_files"])
        self.assertIn("blocked_wait_state", report["source_files"])
        self.assertIn("stage6_operator_wait_packet", report["source_files"])
        self.assertIn("stage6_blocker_closure_plan", report["source_files"])
        self.assertIn("stage6_operating_status", report["source_files"])
        self.assertIn("manual_dispatch_execution_slip", report["source_files"])
        self.assertIn("manual_dispatch_execution_slip_md", report["source_files"])
        self.assertIn("provider_dispatch_eml_draft", report["source_files"])
        self.assertIn("dispatch_confirmation_dry_run_from_eml", report["source_files"])
        self.assertIn("stage6_user_action_card", report["source_files"])
        self.assertIn("stage6_user_action_card_md", report["source_files"])
        self.assertIn("dispatch_guidance_consistency", report["source_files"])
        self.assertIn("dispatch_stale_freeze_surface_audit", report["source_files"])
        self.assertIn("dispatch_confirmation_helper", report["source_files"])
        self.assertIn("dispatch_confirmation_helper_test", report["source_files"])
        self.assertIn("dispatch_send_status_builder", report["source_files"])
        self.assertIn("dispatch_send_status_test", report["source_files"])
        self.assertIn("return_receipt_builder", report["source_files"])
        self.assertIn("refresh_stack_test", report["source_files"])
        self.assertIn("provider_return_watch", report["source_files"])
        self.assertIn("provider_return_watch_process_status", report["source_files"])
        self.assertIn("provider_watch_continuity", report["source_files"])
        self.assertIn("human_mandate_completion_packet", report["source_files"])
        self.assertIn("return_staging_readme", report["source_files"])
        self.assertIn("dual_repo_research_loop_guard", report["source_files"])
        self.assertEqual(report["stage_pipeline_context"]["stage6_name"], "Shadow Operation")
        self.assertEqual(report["stage_pipeline_context"]["stage7_name"], "Local Simulated Paper")
        self.assertFalse(report["stage6_current_state"]["stage6_reached"])
        self.assertEqual(report["stage6_current_state"]["stage6_readiness_decision"], "BLOCK")
        self.assertEqual(report["stage6_current_state"]["blocker_count"], 6)
        self.assertTrue(report["stage6_current_state"]["guarded_shadow_exception_apply_ready"])
        self.assertFalse(report["stage6_current_state"]["guarded_shadow_exception_applied"])
        self.assertTrue(report["stage6_current_state"]["guarded_human_mandate_apply_ready"])
        self.assertFalse(report["stage6_current_state"]["guarded_human_mandate_applied"])

        md = audit_mod.render_md(report)
        self.assertIn("Do not mark goal complete: `true`", md)
        self.assertIn("dispatch_sent_confirmation_recorded", md)

    def test_audit_can_report_complete_when_all_artifacts_pass(self) -> None:
        return_dir = Path(tempfile.mkdtemp())
        template_path = return_dir / "template.json"
        template_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "candidate_id": "CAND-022",
                    "sent_at": "YYYY-MM-DDTHH:MM:SS+09:00",
                    "expected_return_files": self.EXPECTED_RETURN_FILES,
                    "safety": audit_mod.SAFETY,
                }
            ),
            encoding="utf-8",
        )
        instruction_md = return_dir / "instruction.md"
        instruction_md.write_text(
            "\n".join(
                [
                    "Email markdown: `C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md`",
                    "Email sha256: `emailhash`",
                    "Attachment: `C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip`",
                    "Attachment sha256: `hash`",
                ]
            ),
            encoding="utf-8",
        )
        operator_checklist_md = return_dir / "operator_checklist.md"
        operator_checklist_md.write_text(
            "\n".join(
                [
                    "Email markdown: `C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md`",
                    "Email sha256: `emailhash`",
                    "Attachment: `C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip`",
                    "Attachment sha256: `hash`",
                    "Do not use mutable latest zip paths.",
                    "Post-confirmation watcher: `python .\\run_cand022_provider_return_watch.py --cycles 180`",
                    "First run copy-review: `python .\\build_kis_provider_returned_to_handoff_copy_review.py`",
                    "Refresh forbidden while copy-review status is `BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW`.",
                    "Refresh allowed only after copy-review status is `READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW`.",
                ]
            ),
            encoding="utf-8",
        )
        manual_dispatch_slip_md = return_dir / "manual_dispatch_slip.md"
        eml_draft = return_dir / "CAND-022_provider_dispatch_draft.eml"
        eml_draft.write_bytes(b"Subject: CAND-022 source-backed provider response draft request\r\n\r\nbody")
        operator_brief_md = return_dir / "operator_brief.md"
        operator_brief_md.write_text(
            "\n".join(
                [
                    "Email markdown to send: `C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md`",
                    "Email sha256: `emailhash`",
                    "Attachment to send: `C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip`",
                    "Attachment sha256: `hash`",
                    "The mutable latest email/zip paths are reference-only.",
                    "Policy review: operator decision packet is review-only; shadow_only_exception requires explicit operator choice",
                    "## Operator Decision",
                    "Operator decision status: `READY_REVIEW_ONLY_PACKET`",
                    "Operator decision tiny-live ready: `false`",
                    "Operator decision auto-apply allowed: `false`",
                    str(manual_dispatch_slip_md),
                    "Korean manual dispatch slip status: `READY_MANUAL_DISPATCH_EXECUTION_SLIP`",
                    "Korean manual dispatch slip attachment: `C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip`",
                    "Korean manual dispatch slip attachment sha256: `hash`",
                ]
            ),
            encoding="utf-8",
        )
        operator_decision_md = return_dir / "operator_decision.md"
        operator_decision_md.write_text(
            "\n".join(
                [
                    "This packet is approval: `false`",
                    "Auto-apply allowed: `false`",
                    "shadow_only_exception",
                    "still block paper/live/order intents",
                    "do_not_create_order_intent_from_this_packet",
                    "do_not_enable_paper",
                    "do_not_enable_live",
                    "do_not_enable_broker_submit",
                    '"pretrade_firewall_default_decision": "BLOCK"',
                ]
            ),
            encoding="utf-8",
        )
        shadow_exception_contract_md = return_dir / "shadow_exception_contract.md"
        shadow_exception_contract_md.write_text(
            "\n".join(
                [
                    "This file is approval: `false`",
                    "Auto-apply allowed: `false`",
                    "Contract changes allowed by this file: `false`",
                    "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY",
                    "do_not_create_order_intent",
                    "do_not_enable_paper",
                    "do_not_enable_live",
                    "do_not_enable_broker_submit",
                    '"pretrade_firewall_default_decision": "BLOCK"',
                ]
            ),
            encoding="utf-8",
        )
        manual_dispatch_slip_md = return_dir / "manual_dispatch_slip.md"
        manual_dispatch_slip_md.write_text(
            "\n".join(
                [
                    "Manual dispatch slip: READY",
                    "Pre-send verification: PASS_PRESEND_ACTIVE_SEND_FILES_VERIFIED",
                    "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                    "hash",
                    "write_cand022_dispatch_sent_confirmation.py",
                    "Post-write sequence contract",
                    "immediate_safe_commands",
                    "copy_review_required_before_refresh",
                    '"pretrade_firewall_default_decision": "BLOCK"',
                ]
            ),
            encoding="utf-8",
        )
        guard_path = return_dir / "DISABLE_DUAL_REPO_RESEARCH_LOOP"
        guard_path.write_text("disabled_by_test\n", encoding="utf-8")
        fixtures = {
            str(audit_mod.TINY_LIVE_AUDIT): {"completion_decision": "COMPLETE", "failed_required_check_ids": [], "safety": audit_mod.SAFETY},
            str(audit_mod.NEXT_ACTION_ROUTER): {
                "recommended_next_action_id": "send_external_provider_dispatch_packet",
                "can_autonomously_enable_trading": False,
                "blocked_by_external_input": True,
                "autonomous_continuation": {
                    "decision": "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS",
                    "can_continue_local_work": False,
                    "allowed_local_actions": ["refresh_status_reports", "run_read_only_audits"],
                    "blocked_local_actions": [
                        "do_not_start_generic_model_search",
                        "do_not_create_order_intent",
                    ],
                },
                "action_router": [
                    {
                        "action_id": "send_external_provider_dispatch_packet",
                        "frozen_email_markdown": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md",
                        "frozen_email_sha256": "emailhash",
                        "frozen_attachment": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                        "frozen_attachment_sha256": "hash",
                        "manual_dispatch_instruction_packet_md": "C:\\AI\\reports\\operations\\kis_provider_external_dispatch_instruction_packet_latest.md",
                        "after_return_copy_review_required_before_refresh": True,
                        "after_return_refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                        "after_return_refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                        "action_safety": audit_mod.SAFETY,
                    },
                    {
                        "action_id": "review_shadow_only_exception_contract",
                        "status": "READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT",
                        "is_approval": False,
                        "auto_apply_allowed": False,
                        "forbidden_actions": ["do_not_create_order_intent", "do_not_enable_live"],
                    }
                ],
            },
            str(audit_mod.OPERATOR_BRIEF): {
                "single_next_action": "kis_provider_external_dispatch_instruction_packet_latest.md",
                "safety": audit_mod.SAFETY,
                "dispatch_file_policy": {
                    "active_email_markdown": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md",
                    "active_email_sha256": "emailhash",
                    "active_attachment": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                    "active_attachment_sha256": "hash",
                },
                "operator_decision_packet": {
                    "status": "READY_REVIEW_ONLY_PACKET",
                    "tiny_live_ready": False,
                    "auto_apply_allowed": False,
                    "policy_choices": ["data_upgrade_required", "shadow_only_exception"],
                },
            },
            str(audit_mod.REFRESH_STACK): {
                "status": "PASS_REFRESH_STACK_COMPLETED",
                "failed_scripts": [],
                "safety": audit_mod.SAFETY,
                "scripts": [
                    "build_kis_provider_returned_handoff_staging_verifier.py",
                    "build_kis_provider_external_return_receipt_status.py",
                    "build_kis_provider_external_dispatch_send_status.py",
                    "build_cand022_active_thread_goal_audit.py",
                ],
            },
            str(audit_mod.PROVIDER_RETURN_WATCH): {
                "status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
                "blockers": [
                    "dispatch_sent_confirmation_missing_or_invalid",
                    "returned_provider_csvs_missing",
                ],
                "run_refresh_when_ready": False,
                "copy_review_required_before_refresh": True,
                "refresh_stack_invocation_policy": "manual_after_returned_to_handoff_copy_review_ready",
                "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                "non_goals": [
                    "does_not_send_email",
                    "does_not_write_dispatch_confirmation",
                    "does_not_copy_or_generate_provider_csvs",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.PROVIDER_RETURN_WATCH_PROCESS_STATUS): {
                "generated_at": "2026-05-14T04:59:00+09:00",
                "status": "WATCHER_RUNNING",
                "watch_running": True,
                "watcher_process_ids": [4340],
                "ready_for_unattended_wait": True,
                "provider_return_watch_status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
                "provider_return_watch_policy": {
                    "copy_review_required_before_refresh": True,
                    "refresh_stack_invocation_policy": "manual_after_returned_to_handoff_copy_review_ready",
                    "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                    "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                },
                "copy_review_ready_for_manual_followup": False,
                "non_goals": [
                    "does_not_start_watcher",
                    "does_not_stop_processes",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.PROVIDER_WATCH_CONTINUITY): {
                "status": "WATCHER_CONTINUITY_OK",
                "needs_new_watcher": False,
                "min_remaining_minutes": 12.0,
                "max_remaining_minutes": 179.0,
                "existing_watcher_process_ids": [4340, 5176],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.HUMAN_MANDATE_COMPLETION_PACKET): {
                "status": "AWAITING_EXPLICIT_HUMAN_MANDATE_COMPLETION_INSTRUCTION",
                "do_not_auto_apply": True,
                "caps_present": True,
                "can_complete_after_explicit_instruction": True,
                "missing_fields": ["reporting_policy", "incident_policy_confirmed", "mandate_status_complete"],
                "exact_instruction_to_apply_recommended_values": "UPDATE HUMAN_MANDATE REPORTING_POLICY checkpoint_email_frequency_hours=3",
                "exact_instruction_file": "C:\\AI\\reports\\live_readiness\\human_mandate_completion_instruction.latest.txt",
                "guarded_dry_run_command": "python .\\apply_human_mandate_completion.py --operator-instruction-file C:\\AI\\reports\\live_readiness\\human_mandate_completion_instruction.latest.txt --dry-run",
                "guarded_apply_command": "python .\\apply_human_mandate_completion.py --operator-instruction-file C:\\AI\\reports\\live_readiness\\human_mandate_completion_instruction.latest.txt",
                "post_apply_verification_commands": ["python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120"],
                "explicit_non_approval": "Completing human_mandate.yaml is not PAPER APPROVE and not LIVE APPROVE.",
                "forbidden_actions": ["do_not_modify_human_mandate_without_explicit_user_instruction", "do_not_create_order_intent"],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.STAGE6_WAIT_PACKET): {
                "status": "WAIT_OPERATOR_OR_PROVIDER_INPUT_TO_ADVANCE_STAGE6",
                "stage6_reached": False,
                "blocked_by_operator_or_provider": True,
                "dispatch_wait": {
                    "safe_watch_command_after_dispatch": "python .\\run_cand022_provider_return_watch.py",
                    "safe_watch_command_report_only": "python .\\run_cand022_provider_return_watch.py --no-refresh",
                },
                "prompt_to_artifact_completion_audit": {
                    "complete": False,
                    "missing": ["stage6_shadow_queue_allowed_or_shadow_passed"],
                },
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.STAGE6_BLOCKER_CLOSURE_PLAN): {
                "stage6_reached": True,
                "stage6_readiness_decision": "PASS",
                "shadow_queue_allowed": True,
                "shadow_passed": True,
                "blocker_count": 0,
                "blockers": [],
                "guarded_shadow_exception_apply_support": {
                    "latest_apply_guard_ready": True,
                    "latest_apply_appended_shadow_queue": True,
                },
                "guarded_human_mandate_apply_support": {
                    "latest_apply_guard_ready": True,
                    "latest_apply_wrote_human_mandate": True,
                },
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.STAGE6_OPERATING_STATUS): {
                "status": "CAND022_STAGE6_REACHED",
                "broader_stage6_operation": {
                    "running": True,
                    "shadow_queue_candidates": ["CAND-001", "CAND-022"],
                    "cycles_completed": 10,
                    "cycles_requested": 288,
                },
                "cand022_stage6": {
                    "stage6_reached": True,
                    "completion_decision": "COMPLETE",
                    "completion_percent": 100.0,
                },
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.MANUAL_DISPATCH_EXECUTION_SLIP): {
                "status": "READY_MANUAL_DISPATCH_EXECUTION_SLIP",
                "blockers": [],
                "send_now": {
                    "subject": "CAND-022 source-backed provider response draft request",
                    "email_markdown": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md",
                    "email_sha256": "emailhash",
                    "attachment": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                    "attachment_sha256": "hash",
                },
                "after_actual_send": {
                    "preferred_helper_command": "python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send",
                    "post_write_sequence_contract": {
                        "immediate_safe_commands": [
                            "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120"
                        ],
                        "copy_review_required_before_refresh": True,
                        "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                        "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                    },
                },
                "checks": {
                    "presend_verified": True,
                    "send_files_match_presend_verifier": True,
                },
                "non_goals": [
                    "does_not_send_email",
                    "does_not_enable_paper_live_broker_submit_or_order_intent",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.STAGE6_USER_ACTION_CARD): {
                "status": "READY_STAGE6_USER_ACTION_CARD",
                "stage6_reached": False,
                "stage6_completion_decision": "NOT_COMPLETE",
                "stage6_completion_percent": 85.7,
                "recommended_path": {
                    "action_id": "send_external_provider_dispatch_packet",
                    "eml_draft": str(eml_draft),
                    "eml_draft_status": "READY_DISPATCH_EML_DRAFT_NO_SEND",
                    "after_send_helper_command": (
                        "python .\\write_cand022_dispatch_sent_confirmation.py --sent-at \"<timezone-aware sent time>\" "
                        "--sent-by \"<operator_or_account>\" --recipient-or-channel \"<provider_or_channel>\" --i-confirm-actual-send"
                    ),
                    "post_confirmation_watch_command": (
                        "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120"
                    ),
                    "post_write_sequence_contract": {
                        "immediate_safe_commands": [
                            "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120"
                        ],
                        "copy_review_required_before_refresh": True,
                        "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                        "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                    },
                },
                "optional_shadow_only_exception": {
                    "is_approval": False,
                    "auto_apply_allowed": False,
                    "exact_instruction": "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY",
                },
                "non_goals": [
                    "does_not_send_email",
                    "does_not_write_dispatch_confirmation",
                    "does_not_copy_or_generate_provider_csvs",
                    "does_not_enable_paper_live_broker_submit_or_order_intent",
                    "does_not_mark_stage6_reached",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.PROVIDER_DISPATCH_EML_DRAFT): {
                "status": "READY_DISPATCH_EML_DRAFT_NO_SEND",
                "eml_draft": str(eml_draft),
                "to_placeholder": "provider_or_channel_to_fill@example.invalid",
                "subject": "CAND-022 source-backed provider response draft request",
                "email_markdown": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md",
                "email_sha256": "emailhash",
                "attachment": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                "attachment_sha256": "hash",
                "blockers": [],
                "non_goals": [
                    "does_not_send_email",
                    "does_not_write_dispatch_confirmation",
                    "does_not_copy_or_generate_provider_csvs",
                    "does_not_enable_paper_live_broker_submit_or_order_intent",
                    "does_not_mark_stage6_reached",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.OPERATOR_DECISION_PACKET): {
                "tiny_live_ready": False,
                "do_not_auto_apply": True,
                "decision_groups": [
                    {
                        "group_id": "kis_pit_survivorship_policy",
                        "operator_choices": [
                            {
                                "choice_id": "shadow_only_exception",
                                "effect": "Allow no-submit shadow observation with explicit caveats; still block paper/live/order intents.",
                            }
                        ],
                    }
                ],
                "forbidden_actions": [
                    "do_not_create_order_intent_from_this_packet",
                    "do_not_enable_paper",
                    "do_not_enable_live",
                    "do_not_enable_broker_submit",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.SHADOW_ONLY_EXCEPTION_CONTRACT): {
                "status": "READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT",
                "is_approval": False,
                "auto_apply_allowed": False,
                "contract_changes_allowed_by_this_file": False,
                "recommended_policy_choice": "shadow_only_exception",
                "forbidden_actions": [
                    "do_not_create_order_intent",
                    "do_not_enable_paper",
                    "do_not_enable_live",
                    "do_not_enable_broker_submit",
                    "do_not_submit_orders",
                    "do_not_treat_this_contract_as_approval",
                ],
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.INSTRUCTION_PACKET): {
                "status": "READY_MANUAL_DISPATCH_INSTRUCTION_PACKET",
                "attachment_to_send": {
                    "path": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                    "sha256": "hash",
                },
                "email": {
                    "source_markdown": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md",
                    "source_sha256": "emailhash",
                },
                "expected_return_files": self.EXPECTED_RETURN_FILES,
                "return_staging_dir": str(return_dir),
                "safety": audit_mod.SAFETY,
                "confirmation_after_send": {
                    "preferred_helper_command": (
                        "python .\\write_cand022_dispatch_sent_confirmation.py --sent-at \"<timezone-aware sent time>\" "
                        "--sent-by \"<operator_or_account>\" --recipient-or-channel \"<provider_or_channel>\" --i-confirm-actual-send"
                    )
                },
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.OPERATOR_CHECKLIST): {
                "status": "READY_OPERATOR_SEND_CONFIRMATION_CHECKLIST",
                "send_confirmation": {
                    "helper": "C:\\AI\\write_cand022_dispatch_sent_confirmation.py",
                    "preferred_helper_command": (
                        "python .\\write_cand022_dispatch_sent_confirmation.py --sent-at \"<timezone-aware sent time>\" "
                        "--sent-by \"<operator_or_account>\" --recipient-or-channel \"<provider_or_channel>\" --i-confirm-actual-send"
                    ),
                    "post_confirmation_watch_command": "python .\\run_cand022_provider_return_watch.py --cycles 180",
                },
                "operator_steps": ["Do not hand-edit frozen metadata. The helper preserves safety."],
                "after_return": {
                    "copy_review_command": "python .\\build_kis_provider_returned_to_handoff_copy_review.py",
                    "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                    "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                },
                "send_files": {
                    "email_markdown": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md",
                    "email_sha256": "emailhash",
                    "attachment": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                    "attachment_sha256": "hash",
                },
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.GUIDANCE_CONSISTENCY): {
                "status": "PASS_DISPATCH_GUIDANCE_HELPER_FIRST",
                "blockers": [],
                "watch_token": "run_cand022_provider_return_watch.py",
                "watch_required_targets": [
                    "operator_status_brief_md",
                    "manual_dispatch_execution_slip_json",
                    "manual_dispatch_execution_slip_md",
                ],
                "inspections": [
                    {
                        "name": "codex_handover_md",
                        "passed": True,
                        "has_helper_token": True,
                        "has_confirm_flag": True,
                        "stale_phrase_hits": [],
                    },
                    {
                        "name": "blocked_handoff_md",
                        "passed": True,
                        "has_helper_token": True,
                        "has_confirm_flag": True,
                        "stale_phrase_hits": [],
                    },
                    {
                        "name": "operator_status_brief_md",
                        "passed": True,
                        "has_helper_token": True,
                        "has_confirm_flag": True,
                        "has_watch_token": True,
                        "stale_phrase_hits": [],
                    },
                    {
                        "name": "manual_dispatch_execution_slip_json",
                        "passed": True,
                        "has_helper_token": True,
                        "has_confirm_flag": True,
                        "has_watch_token": True,
                        "stale_phrase_hits": [],
                    },
                    {
                        "name": "manual_dispatch_execution_slip_md",
                        "passed": True,
                        "has_helper_token": True,
                        "has_confirm_flag": True,
                        "has_watch_token": True,
                        "stale_phrase_hits": [],
                    },
                ],
            },
            str(audit_mod.PRESEND_VERIFIER): {
                "status": "PASS_PRESEND_ACTIVE_SEND_FILES_VERIFIED",
                "blockers": [],
                "checks": {
                    "operator_brief_uses_frozen_source": True,
                    "active_email_path_matches_frozen": True,
                    "active_attachment_path_matches_frozen": True,
                    "active_email_sha256_matches_frozen": True,
                    "active_attachment_sha256_matches_frozen": True,
                },
                "active_send_files": {
                    "email_markdown": {
                        "path": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\email.md",
                        "sha256": "emailhash",
                    },
                    "attachment": {
                        "path": "C:\\AI\\data_snapshots\\kis_pit_membership\\provider_handoff\\external_dispatch\\frozen\\handoff.zip",
                        "sha256": "hash",
                    },
                },
                "expected_frozen_hashes": {"email_sha256": "emailhash", "attachment_sha256": "hash"},
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.SEND_STATUS): {"send_confirmation_valid": True, "send_confirmation_template": str(template_path)},
            str(audit_mod.RETURN_RECEIPT): {
                "status": "READY_RETURNED_PROVIDER_CSVS_FOR_REVIEW",
                "send_confirmation_path": "sent.json",
                "send_confirmation_valid": True,
                "send_confirmation_blockers": [],
                "return_staging_dir": str(return_dir),
                "expected_return_files": self.EXPECTED_RETURN_FILES,
                "safety": audit_mod.SAFETY,
            },
            str(audit_mod.HANDOFF_FILL_PROGRESS): {"completed_rows": 18, "total_rows": 18, "open_rows": 0},
        }

        def fake_read(path: Path) -> dict:
            if str(path) in fixtures:
                return fixtures[str(path)]
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8-sig"))
            return {}

        with patch.object(audit_mod, "read_json_optional", side_effect=fake_read), patch.object(
            audit_mod, "INSTRUCTION_PACKET_MD", instruction_md
        ), patch.object(
            audit_mod, "OPERATOR_DECISION_PACKET_MD", operator_decision_md
        ), patch.object(
            audit_mod, "SHADOW_ONLY_EXCEPTION_CONTRACT_MD", shadow_exception_contract_md
        ), patch.object(
            audit_mod, "MANUAL_DISPATCH_EXECUTION_SLIP_MD", manual_dispatch_slip_md
        ), patch.object(
            audit_mod, "OPERATOR_BRIEF_MD", operator_brief_md
        ), patch.object(
            audit_mod, "OPERATOR_CHECKLIST_MD", operator_checklist_md
        ), patch.object(
            audit_mod, "DUAL_REPO_RESEARCH_LOOP_GUARD", guard_path
        ):
            report = audit_mod.build_report("2026-05-14T05:00:00+09:00")

        self.assertEqual(report["status"], "COMPLETE")
        self.assertFalse(report["do_not_mark_goal_complete"])
        self.assertEqual(report["missing_or_blocked_check_ids"], [])


if __name__ == "__main__":
    unittest.main()
