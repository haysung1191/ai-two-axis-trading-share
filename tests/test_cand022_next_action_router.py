from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_next_action_router.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_next_action_router", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
router_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(router_mod)


class Cand022NextActionRouterTests(unittest.TestCase):
    def test_router_prioritizes_data_intake_when_data_and_mandate_are_blocked(self) -> None:
        router = router_mod.build_router(
            "2026-05-14T00:00:00+09:00",
            {
                "objective": "test",
                "completion_decision": "NOT_COMPLETE",
                "failed_required_check_ids": [
                    "kis_pit_manifest_operation_ready",
                    "provider_response_validated",
                    "provider_response_import_preview_ready",
                    "intake_templates_complete",
                    "human_mandate_complete",
                ],
            },
            {
                "status": "AWAITING_EXPLICIT_HUMAN_MANDATE_COMPLETION_INSTRUCTION",
                "missing_fields": ["reporting_policy"],
                "exact_instruction_to_apply_recommended_values": "UPDATE HUMAN_MANDATE REPORTING_POLICY ...",
                "exact_instruction_file": r"C:\AI\reports\live_readiness\human_mandate_completion_instruction.latest.txt",
                "guarded_dry_run_command": r"python .\apply_human_mandate_completion.py --operator-instruction-file C:\AI\reports\live_readiness\human_mandate_completion_instruction.latest.txt --dry-run",
                "guarded_apply_command": r"python .\apply_human_mandate_completion.py --operator-instruction-file C:\AI\reports\live_readiness\human_mandate_completion_instruction.latest.txt",
                "post_apply_verification_commands": ["python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120"],
                "explicit_non_approval": "Completing human_mandate.yaml is not PAPER APPROVE and not LIVE APPROVE.",
            },
            {
                "templates": {"membership": "membership.csv", "event": "event.csv", "replay": "replay.csv"},
                "inspections": {
                    "membership": {"row_count": 7, "incomplete_rows": [{"symbol": "MU"}]},
                    "event": {"row_count": 7, "incomplete_rows": [{"symbol": "MU"}]},
                    "replay": {"row_count": 4, "incomplete_rows": [{"scenario": "ticker_change"}]},
                },
            },
            {
                "status": "BLOCK_PROVIDER_RESPONSE_FIELD_CLOSURE_ROWS_OPEN",
                "closure_row_count": 18,
                "missing_counts": {"membership": 7, "event_or_no_event": 7, "replay": 4},
            },
            {
                "status": "BLOCK_HANDOFF_FILL_PROGRESS_OPEN",
                "completed_rows": 0,
                "total_rows": 18,
                "open_rows": 18,
                "completion_percent": 0.0,
            },
            {
                "status": "READY_EXTERNAL_DISPATCH_MANIFEST",
                "email_markdown": {"path": "email.md", "sha256": "emailhash"},
                "attachment": {"path": "handoff.zip", "sha256": "ziphash"},
                "return_staging_dir": "returned",
                "expected_return_files": [
                    "cand022_membership_response_draft.csv",
                    "cand022_event_or_no_event_response_draft.csv",
                    "cand022_replay_response_draft.csv",
                ],
            },
            {
                "status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
                "freeze_dir": "frozen",
                "frozen_files": {
                    "email_markdown": {"path": "frozen/email.md", "sha256": "frozenemailhash"},
                    "attachment": {"path": "frozen/handoff.zip", "sha256": "frozenziphash"},
                },
            },
            {
                "status": "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION",
                "send_confirmation_template": "template.json",
                "send_confirmation_path": "sent.json",
                "send_confirmation_present": False,
                "send_confirmation_valid": False,
                "send_confirmation_blockers": ["dispatch_sent_confirmation_missing"],
                "next_safe_action": "run python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send",
                "post_confirmation_watch_command": "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120",
            },
            {
                "status": "READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT",
                "is_approval": False,
                "auto_apply_allowed": False,
                "recommended_policy_choice": "shadow_only_exception",
                "required_explicit_operator_instruction_before_any_contract_change": (
                    "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY"
                ),
                "allowed_scope_if_operator_explicitly_accepts_later": ["record_no_submit_shadow_observation_only"],
                "still_required_before_tiny_live": ["source_backed_kis_pit_membership_rows"],
                "forbidden_actions": ["do_not_create_order_intent", "do_not_enable_live", "do_not_submit_orders"],
            },
            {
                "status": "WAIT_EXPLICIT_SHADOW_ONLY_EXCEPTION_INSTRUCTION",
                "can_apply_now": False,
                "blocked_checks": ["operator_instruction_exact_match"],
                "guarded_apply_commands": {
                    "dry_run": 'python .\\run_cand022_shadow_only_exception_apply_and_verify.py --operator-instruction "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY"',
                    "apply": 'python .\\run_cand022_shadow_only_exception_apply_and_verify.py --operator-instruction "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY" --execute --i-confirm-apply-shadow-only-exception',
                },
                "preferred_guarded_apply_and_verify_commands": {
                    "dry_run": 'python .\\run_cand022_shadow_only_exception_apply_and_verify.py --operator-instruction "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY"',
                    "apply": 'python .\\run_cand022_shadow_only_exception_apply_and_verify.py --operator-instruction "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY" --execute --i-confirm-apply-shadow-only-exception',
                },
                "confirm_flag_required_for_real_apply": "--i-confirm-apply-shadow-only-exception",
                "real_apply_requires_execute_flag": True,
                "low_level_apply_script_is_not_operator_surface": True,
                "post_apply_verification_commands": [
                    "python .\\build_cand022_stage6_shadow_readiness_packet.py",
                    "python .\\run_stage6_shadow_loop.py --cycles 1 --dry-run",
                ],
            },
        )

        self.assertEqual(router["recommended_next_action_id"], "send_external_provider_dispatch_packet")
        self.assertFalse(router["can_autonomously_enable_trading"])
        self.assertEqual(
            router["autonomous_continuation"]["decision"],
            "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS",
        )
        self.assertFalse(router["autonomous_continuation"]["can_continue_local_work"])
        self.assertIn("do_not_start_generic_model_search", router["autonomous_continuation"]["blocked_local_actions"])
        self.assertIn("refresh_status_reports", router["autonomous_continuation"]["allowed_local_actions"])
        action_ids = [action["action_id"] for action in router["action_router"]]
        self.assertIn("do_not_progress_to_submit_or_order_intent", action_ids)
        self.assertIn("send_external_provider_dispatch_packet", action_ids)
        self.assertIn("fill_kis_pit_authoritative_intake", action_ids)
        self.assertIn("obtain_explicit_human_mandate_completion_instruction", action_ids)
        self.assertIn("review_shadow_only_exception_contract", action_ids)
        dispatch_action = next(action for action in router["action_router"] if action["action_id"] == "send_external_provider_dispatch_packet")
        self.assertEqual(dispatch_action["status"], "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION")
        self.assertEqual(dispatch_action["send_confirmation_template"], "template.json")
        self.assertFalse(dispatch_action["send_confirmation_valid"])
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", dispatch_action["send_status_next_safe_action"])
        self.assertIn("--i-confirm-actual-send", dispatch_action["send_status_next_safe_action"])
        self.assertIn("run_cand022_provider_return_watch.py", dispatch_action["post_confirmation_watch_command"])
        self.assertIn("--cycles 180", dispatch_action["post_confirmation_watch_command"])
        self.assertTrue(dispatch_action["manual_dispatch_execution_slip_md"].endswith("CAND-022_manual_dispatch_execution_slip.latest.md"))
        self.assertTrue(dispatch_action["manual_dispatch_instruction_packet_md"].endswith("kis_provider_external_dispatch_instruction_packet_latest.md"))
        self.assertTrue(dispatch_action["manual_dispatch_instruction_packet_json"].endswith("kis_provider_external_dispatch_instruction_packet_latest.json"))
        self.assertEqual(dispatch_action["send_confirmation_editable_fields"], ["sent_at", "sent_by", "recipient_or_channel"])
        self.assertIn("schema_version", dispatch_action["send_confirmation_frozen_fields_must_match"])
        self.assertIn("candidate_id", dispatch_action["send_confirmation_frozen_fields_must_match"])
        self.assertIn("frozen_attachment_sha256", dispatch_action["send_confirmation_frozen_fields_must_match"])
        self.assertIn("expected_return_files", dispatch_action["send_confirmation_frozen_fields_must_match"])
        self.assertIn("safety", dispatch_action["send_confirmation_frozen_fields_must_match"])
        self.assertEqual(dispatch_action["attachment"], "handoff.zip")
        self.assertEqual(dispatch_action["frozen_attachment"], "frozen/handoff.zip")
        self.assertEqual(dispatch_action["expected_return_files"][0], "cand022_membership_response_draft.csv")
        self.assertTrue(dispatch_action["after_return_copy_review_required_before_refresh"])
        self.assertEqual(
            dispatch_action["after_return_refresh_allowed_only_if_copy_review_status"],
            "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertEqual(
            dispatch_action["after_return_refresh_forbidden_if_copy_review_status"],
            "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertIn(
            "Do not run the refresh stack until",
            dispatch_action["after_return_copy_review_then_refresh_contract"],
        )
        self.assertEqual(dispatch_action["action_safety"], router_mod.SAFETY)
        self.assertFalse(dispatch_action["action_safety"]["broker_submit_allowed"])
        self.assertFalse(dispatch_action["action_safety"]["order_intent_created"])
        self.assertIn(
            "kis_provider_returned_to_handoff_copy_review_latest.json",
            dispatch_action["after_return_copy_review_artifact"],
        )
        self.assertIn(
            "python .\\build_kis_provider_returned_to_handoff_copy_review.py",
            dispatch_action["after_return_commands"],
        )
        self.assertLess(
            dispatch_action["after_return_commands"].index(
                "python .\\build_kis_provider_returned_to_handoff_copy_review.py"
            ),
            dispatch_action["after_return_commands"].index(
                "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120"
            ),
        )
        data_action = next(action for action in router["action_router"] if action["action_id"] == "fill_kis_pit_authoritative_intake")
        self.assertIn("provider_handoff", data_action["primary_fill_workspace"])
        self.assertTrue(data_action["field_closure_checklist_csv"].endswith("kis_provider_response_field_closure_plan_latest.csv"))
        self.assertEqual(data_action["field_closure_row_count"], 18)
        self.assertEqual(data_action["handoff_fill_progress"]["open_rows"], 18)
        self.assertIn("python .\\build_kis_provider_response_validator.py", data_action["after_fill_commands"])
        self.assertIn("python .\\build_kis_provider_response_field_closure_plan.py", data_action["after_fill_commands"])
        self.assertIn("python .\\build_kis_provider_handoff_fill_progress.py", data_action["after_fill_commands"])
        self.assertIn("python .\\build_kis_provider_response_import_preview.py", data_action["after_fill_commands"])
        self.assertFalse(router["safety"]["broker_submit_allowed"])
        shadow_action = next(action for action in router["action_router"] if action["action_id"] == "review_shadow_only_exception_contract")
        self.assertEqual(shadow_action["status"], "READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT")
        self.assertFalse(shadow_action["is_approval"])
        self.assertFalse(shadow_action["auto_apply_allowed"])
        self.assertEqual(shadow_action["recommended_policy_choice"], "shadow_only_exception")
        self.assertEqual(shadow_action["preflight_status"], "WAIT_EXPLICIT_SHADOW_ONLY_EXCEPTION_INSTRUCTION")
        self.assertFalse(shadow_action["preflight_can_apply_now"])
        self.assertEqual(shadow_action["preflight_blocked_checks"], ["operator_instruction_exact_match"])
        self.assertIn("run_cand022_shadow_only_exception_apply_and_verify.py", shadow_action["guarded_dry_run_command"])
        self.assertNotIn("--execute", shadow_action["guarded_dry_run_command"])
        self.assertIn("run_cand022_shadow_only_exception_apply_and_verify.py", shadow_action["guarded_apply_command"])
        self.assertIn("--execute", shadow_action["guarded_apply_command"])
        self.assertIn("--i-confirm-apply-shadow-only-exception", shadow_action["guarded_apply_command"])
        self.assertEqual(
            shadow_action["confirm_flag_required_for_real_apply"],
            "--i-confirm-apply-shadow-only-exception",
        )
        self.assertTrue(shadow_action["real_apply_requires_execute_flag"])
        self.assertTrue(shadow_action["low_level_apply_script_is_not_operator_surface"])
        self.assertIn("build_cand022_stage6_shadow_readiness_packet.py", " ".join(shadow_action["post_apply_verification_commands"]))
        self.assertIn("NO_SUBMIT", shadow_action["required_explicit_operator_instruction_before_any_contract_change"])
        self.assertIn("do_not_create_order_intent", shadow_action["forbidden_actions"])
        self.assertIn("Do not apply this contract", shadow_action["forbidden_shortcut"])
        self.assertIn("shadow_only_exception_contract", router["source_files"])
        self.assertIn("returned_to_handoff_copy_review", router["source_files"])
        mandate_action = next(
            action
            for action in router["action_router"]
            if action["action_id"] == "obtain_explicit_human_mandate_completion_instruction"
        )
        self.assertTrue(mandate_action["exact_instruction_file"].endswith("human_mandate_completion_instruction.latest.txt"))
        self.assertIn("apply_human_mandate_completion.py", mandate_action["guarded_dry_run_command"])
        self.assertIn("--dry-run", mandate_action["guarded_dry_run_command"])
        self.assertIn("apply_human_mandate_completion.py", mandate_action["guarded_apply_command"])
        self.assertIn("run_cand022_provider_response_refresh_stack.py", " ".join(mandate_action["post_apply_verification_commands"]))
        self.assertIn("not PAPER APPROVE", mandate_action["explicit_non_approval"])

    def test_router_prioritizes_fill_when_dispatch_manifest_is_not_ready(self) -> None:
        router = router_mod.build_router(
            "2026-05-14T00:00:00+09:00",
            {
                "objective": "test",
                "completion_decision": "NOT_COMPLETE",
                "failed_required_check_ids": ["provider_response_validated"],
            },
            {},
            {"templates": {}, "inspections": {}},
            {"status": "BLOCK_PROVIDER_RESPONSE_FIELD_CLOSURE_ROWS_OPEN"},
            {"status": "BLOCK_HANDOFF_FILL_PROGRESS_OPEN", "open_rows": 18},
            {"status": "BLOCK_EXTERNAL_DISPATCH_MANIFEST"},
        )

        self.assertEqual(router["recommended_next_action_id"], "fill_kis_pit_authoritative_intake")
        self.assertEqual(router["autonomous_continuation"]["decision"], "CONTINUE_SAFE_DATA_CLOSURE")
        self.assertTrue(router["autonomous_continuation"]["can_continue_local_work"])
        action_ids = [action["action_id"] for action in router["action_router"]]
        self.assertNotIn("send_external_provider_dispatch_packet", action_ids)

    def test_router_uses_mandate_when_data_is_not_blocked(self) -> None:
        router = router_mod.build_router(
            "2026-05-14T00:00:00+09:00",
            {
                "objective": "test",
                "completion_decision": "NOT_COMPLETE",
                "failed_required_check_ids": ["human_mandate_complete"],
            },
            {
                "status": "AWAITING_EXPLICIT_HUMAN_MANDATE_COMPLETION_INSTRUCTION",
                "missing_fields": ["reporting_policy"],
                "exact_instruction_to_apply_recommended_values": "UPDATE HUMAN_MANDATE REPORTING_POLICY ...",
                "exact_instruction_file": r"C:\AI\reports\live_readiness\human_mandate_completion_instruction.latest.txt",
                "guarded_dry_run_command": r"python .\apply_human_mandate_completion.py --operator-instruction-file C:\AI\reports\live_readiness\human_mandate_completion_instruction.latest.txt --dry-run",
                "guarded_apply_command": r"python .\apply_human_mandate_completion.py --operator-instruction-file C:\AI\reports\live_readiness\human_mandate_completion_instruction.latest.txt",
                "post_apply_verification_commands": ["python .\\build_human_mandate_completion_packet.py"],
                "explicit_non_approval": "Completing human_mandate.yaml is not PAPER APPROVE and not LIVE APPROVE.",
            },
            {"templates": {}, "inspections": {}},
        )

        self.assertEqual(router["recommended_next_action_id"], "obtain_explicit_human_mandate_completion_instruction")
        self.assertFalse(router["can_autonomously_enable_trading"])
        self.assertEqual(router["autonomous_continuation"]["decision"], "WAIT_FOR_OPERATOR_MANDATE_DECISION")
        self.assertFalse(router["autonomous_continuation"]["can_continue_local_work"])
        mandate_action = next(
            action
            for action in router["action_router"]
            if action["action_id"] == "obtain_explicit_human_mandate_completion_instruction"
        )
        self.assertIn("human_mandate_completion_instruction.latest.txt", mandate_action["exact_instruction_file"])
        self.assertIn("--operator-instruction-file", mandate_action["guarded_apply_command"])


if __name__ == "__main__":
    unittest.main()
