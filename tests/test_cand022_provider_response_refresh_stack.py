from __future__ import annotations

import importlib.util
import unittest
from unittest.mock import patch
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\run_cand022_provider_response_refresh_stack.py")
SPEC = importlib.util.spec_from_file_location("run_cand022_provider_response_refresh_stack", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
stack_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stack_mod)


class Cand022ProviderResponseRefreshStackTests(unittest.TestCase):
    def test_script_list_contains_no_forbidden_submit_actions(self) -> None:
        violations = [
            script
            for script in stack_mod.SAFE_REFRESH_SCRIPTS
            if any(token in script.lower() for token in stack_mod.FORBIDDEN_SCRIPTS)
        ]
        self.assertEqual(violations, [])

    def test_dry_run_report_is_safe_and_ready(self) -> None:
        with patch.object(stack_mod, "official_route_retired_external_dispatch", return_value=False):
            report = stack_mod.build_report("2026-05-14T00:00:00+09:00", dry_run=True, timeout_seconds=1)

        self.assertEqual(report["status"], "DRY_RUN_READY")
        self.assertTrue(report["dry_run"])
        self.assertEqual(report["failed_scripts"], [])
        self.assertEqual(report["script_step_count"], len(report["scripts"]))
        self.assertLess(report["unique_script_count"], report["script_step_count"])
        self.assertEqual(
            report["duplicate_scripts"],
            [
                "build_cand022_operator_status_brief.py",
                "build_cand022_stage6_two_path_decision_slip.py",
                "build_cand022_stage6_user_action_card.py",
            ],
        )
        self.assertIn("Duplicate script steps are intentional", report["interpretation"])
        self.assertFalse(report["safety"]["order_intent_created"])
        self.assertIn("build_kis_provider_response_validator.py", report["scripts"])
        self.assertIn("build_kis_provider_response_evidence_policy.py", report["scripts"])
        self.assertIn("build_kis_provider_public_source_probe_report.py", report["scripts"])
        self.assertIn("build_kis_official_open_trading_api_source_probe.py", report["scripts"])
        self.assertIn("build_kis_provider_response_local_source_audit.py", report["scripts"])
        self.assertIn("build_kis_provider_response_gap_matrix.py", report["scripts"])
        self.assertIn("build_kis_provider_response_field_closure_plan.py", report["scripts"])
        self.assertIn("build_kis_provider_response_draft_workbook.py", report["scripts"])
        self.assertIn("build_kis_provider_response_draft_validator.py", report["scripts"])
        self.assertIn("build_kis_provider_response_copy_review_packet.py", report["scripts"])
        self.assertIn("build_kis_provider_response_external_handoff_bundle.py", report["scripts"])
        self.assertIn("build_kis_provider_response_handoff_integrity_verifier.py", report["scripts"])
        self.assertIn("build_kis_provider_handoff_delivery_package.py", report["scripts"])
        self.assertIn("build_kis_provider_handoff_delivery_verifier.py", report["scripts"])
        self.assertIn("build_kis_provider_handoff_request_note.py", report["scripts"])
        self.assertIn("build_kis_provider_handoff_email_draft.py", report["scripts"])
        self.assertIn("build_kis_provider_returned_handoff_staging_verifier.py", report["scripts"])
        self.assertIn("build_kis_provider_returned_to_handoff_copy_review.py", report["scripts"])
        self.assertIn("build_kis_provider_external_request_readiness_audit.py", report["scripts"])
        self.assertIn("build_kis_provider_external_dispatch_manifest.py", report["scripts"])
        self.assertIn("build_kis_provider_external_return_receipt_status.py", report["scripts"])
        self.assertIn("build_kis_provider_external_dispatch_send_status.py", report["scripts"])
        self.assertIn("run_cand022_provider_return_watch.py", report["scripts"])
        self.assertIn("build_cand022_provider_return_watch_process_status.py", report["scripts"])
        self.assertIn("ensure_cand022_provider_return_watch_continuity.py", report["scripts"])
        self.assertIn("build_kis_provider_external_dispatch_operator_checklist.py", report["scripts"])
        self.assertIn("build_kis_provider_external_presend_verifier.py", report["scripts"])
        self.assertIn("build_kis_provider_external_dispatch_instruction_packet.py", report["scripts"])
        self.assertIn("build_cand022_manual_dispatch_execution_slip.py", report["scripts"])
        self.assertIn("build_cand022_dispatch_guidance_consistency_audit.py", report["scripts"])
        self.assertIn("build_cand022_dispatch_stale_freeze_surface_audit.py", report["scripts"])
        self.assertIn("build_cand022_active_thread_goal_audit.py", report["scripts"])
        self.assertIn("build_cand022_blocked_wait_state.py", report["scripts"])
        self.assertIn("build_stage13_completion_audit.py", report["scripts"])
        self.assertIn("build_stage6_operating_status.py", report["scripts"])
        self.assertIn("build_kis_historical_pit_survivorship_gap_matrix.py", report["scripts"])
        self.assertIn("build_kis_pit_source_acquisition_queue.py", report["scripts"])
        self.assertIn("build_kis_axis_wide_membership_handoff_package.py", report["scripts"])
        self.assertIn("build_kis_axis_wide_membership_replacement_worklist.py", report["scripts"])
        self.assertIn("build_kis_axis_wide_source_export_intake_contract.py", report["scripts"])
        self.assertIn("build_krx_data_marketplace_access_probe.py", report["scripts"])
        self.assertIn("build_kis_axis_wide_source_export_operator_packet.py", report["scripts"])
        self.assertIn("apply_kis_axis_wide_source_exports_to_replacement_worklist.py", report["scripts"])
        self.assertIn("build_kis_axis_wide_membership_worklist_fill_progress.py", report["scripts"])
        self.assertIn("build_kis_axis_wide_historical_source_feasibility_matrix.py", report["scripts"])
        self.assertIn("apply_kis_axis_wide_membership_worklist_to_shards.py", report["scripts"])
        self.assertIn("build_kis_axis_wide_membership_response_validator.py", report["scripts"])
        self.assertIn("apply_kis_axis_wide_membership_import.py", report["scripts"])
        self.assertIn("build_kis_axis_wide_membership_coverage_progress.py", report["scripts"])
        self.assertIn("build_kis_pit_intake_import_preflight.py", report["scripts"])
        self.assertIn("build_kis_pit_intake_work_order.py", report["scripts"])
        self.assertIn("build_kis_pit_next_evidence_fill_card.py", report["scripts"])
        self.assertIn("update_kis_pit_intake_row.py", report["scripts"])
        self.assertIn("update_kis_pit_source_artifact_registry.py", report["scripts"])
        self.assertIn("apply_kis_pit_next_evidence_bundle.py", report["scripts"])
        self.assertIn("build_kis_pit_source_artifact_registry_verifier.py", report["scripts"])
        self.assertIn("build_kis_pit_intake_source_provenance_verifier.py", report["scripts"])
        self.assertIn("apply_kis_pit_intake_canonical_import.py", report["scripts"])
        self.assertIn("build_kis_provider_handoff_draft_validator.py", report["scripts"])
        self.assertIn("build_kis_provider_handoff_fill_progress.py", report["scripts"])
        self.assertIn("build_kis_provider_handoff_to_internal_copy_review.py", report["scripts"])
        self.assertIn("build_cand022_operator_decision_packet.py", report["scripts"])
        self.assertIn("build_cand022_shadow_only_exception_contract.py", report["scripts"])
        self.assertIn("build_cand022_shadow_exception_apply_preflight.py", report["scripts"])
        self.assertIn("build_cand022_current_signal_observation.py", report["scripts"])
        self.assertIn("build_cand022_kis_tradable_mapping_audit.py", report["scripts"])
        self.assertIn("build_cand022_stage6_prequeue_dry_run.py", report["scripts"])
        self.assertIn("build_cand022_stage6_shadow_loop_dry_run.py", report["scripts"])
        self.assertIn("build_cand022_stage6_shadow_readiness_packet.py", report["scripts"])
        self.assertIn("build_cand022_stage6_blocker_closure_plan.py", report["scripts"])
        self.assertIn("run_cand022_shadow_only_exception_apply_and_verify.py", report["scripts"])
        self.assertIn("build_cand022_stage6_goal_completion_audit.py", report["scripts"])
        self.assertIn("build_cand022_stage6_entry_path_audit.py", report["scripts"])
        self.assertIn("build_cand022_stage6_operator_wait_packet.py", report["scripts"])
        self.assertIn("build_cand022_next_action_router.py", report["scripts"])
        self.assertIn("build_cand022_operator_status_brief.py", report["scripts"])
        self.assertIn("build_cand022_stage6_user_action_card.py", report["scripts"])
        self.assertIn("build_cand022_stage6_two_path_decision_slip.py", report["scripts"])
        self.assertIn("build_cand022_provider_dispatch_eml_draft.py", report["scripts"])
        self.assertIn("build_cand022_dispatch_confirmation_dry_run_from_eml.py", report["scripts"])

    def test_official_kis_route_skips_retired_external_dispatch_send_prep(self) -> None:
        with patch.object(stack_mod, "official_route_retired_external_dispatch", return_value=True):
            report = stack_mod.build_report("2026-05-16T00:00:00+09:00", dry_run=True, timeout_seconds=1)

        self.assertEqual(report["status"], "DRY_RUN_READY")
        self.assertTrue(report["official_kis_route_retired_external_dispatch"])
        self.assertIn("build_cand022_manual_dispatch_execution_slip.py", report["skipped_scripts"])
        self.assertIn("build_cand022_provider_dispatch_eml_draft.py", report["skipped_scripts"])
        self.assertIn("build_cand022_dispatch_confirmation_dry_run_from_eml.py", report["skipped_scripts"])
        self.assertIn("build_cand022_dispatch_guidance_consistency_audit.py", report["skipped_scripts"])
        self.assertIn("build_cand022_dispatch_stale_freeze_surface_audit.py", report["skipped_scripts"])
        self.assertIn("build_cand022_blocked_wait_state.py", report["skipped_scripts"])
        self.assertNotIn("build_cand022_manual_dispatch_execution_slip.py", report["scripts"])
        self.assertIn("build_kis_pit_membership_verifier.py", report["scripts"])

    def test_refresh_stack_keeps_status_surfaces_in_dependency_order(self) -> None:
        scripts = stack_mod.SAFE_REFRESH_SCRIPTS

        def idx(script: str) -> int:
            return scripts.index(script)

        def last_idx(script: str) -> int:
            return len(scripts) - 1 - list(reversed(scripts)).index(script)

        self.assertLess(
            idx("build_kis_provider_external_dispatch_manifest.py"),
            idx("build_kis_provider_external_dispatch_send_status.py"),
        )
        self.assertLess(
            idx("build_kis_provider_returned_handoff_staging_verifier.py"),
            idx("build_kis_provider_returned_to_handoff_copy_review.py"),
        )
        self.assertLess(
            idx("build_kis_provider_returned_to_handoff_copy_review.py"),
            idx("build_kis_provider_external_return_receipt_status.py"),
        )
        self.assertLess(
            idx("build_kis_provider_external_return_receipt_status.py"),
            idx("build_kis_provider_external_dispatch_send_status.py"),
        )
        self.assertLess(
            idx("build_kis_provider_external_dispatch_send_status.py"),
            idx("run_cand022_provider_return_watch.py"),
        )
        self.assertLess(
            idx("run_cand022_provider_return_watch.py"),
            idx("build_cand022_provider_return_watch_process_status.py"),
        )
        self.assertLess(
            idx("build_cand022_provider_return_watch_process_status.py"),
            idx("ensure_cand022_provider_return_watch_continuity.py"),
        )
        self.assertLess(
            idx("ensure_cand022_provider_return_watch_continuity.py"),
            idx("build_kis_provider_external_dispatch_operator_checklist.py"),
        )
        self.assertLess(
            idx("build_kis_provider_handoff_fill_progress.py"),
            idx("build_cand022_next_action_router.py"),
        )
        self.assertLess(
            idx("build_kis_provider_external_dispatch_send_status.py"),
            idx("build_cand022_next_action_router.py"),
        )
        self.assertLess(
            idx("build_kis_pit_source_acquisition_queue.py"),
            idx("build_kis_axis_wide_membership_handoff_package.py"),
        )
        self.assertLess(
            idx("build_kis_pit_intake_work_order.py"),
            idx("build_kis_pit_source_acquisition_queue.py"),
        )
        self.assertLess(
            idx("build_kis_axis_wide_membership_handoff_package.py"),
            idx("build_kis_axis_wide_membership_replacement_worklist.py"),
        )
        self.assertLess(
            idx("build_kis_axis_wide_membership_replacement_worklist.py"),
            idx("build_kis_axis_wide_source_export_intake_contract.py"),
        )
        self.assertLess(
            idx("build_kis_axis_wide_source_export_intake_contract.py"),
            idx("build_krx_data_marketplace_access_probe.py"),
        )
        self.assertLess(
            idx("build_krx_data_marketplace_access_probe.py"),
            idx("build_kis_axis_wide_source_export_operator_packet.py"),
        )
        self.assertLess(
            idx("build_kis_axis_wide_source_export_operator_packet.py"),
            idx("apply_kis_axis_wide_source_exports_to_replacement_worklist.py"),
        )
        self.assertLess(
            idx("apply_kis_axis_wide_source_exports_to_replacement_worklist.py"),
            idx("build_kis_axis_wide_membership_worklist_fill_progress.py"),
        )
        self.assertLess(
            idx("build_kis_axis_wide_membership_worklist_fill_progress.py"),
            idx("build_kis_axis_wide_historical_source_feasibility_matrix.py"),
        )
        self.assertLess(
            idx("build_kis_axis_wide_historical_source_feasibility_matrix.py"),
            idx("apply_kis_axis_wide_membership_worklist_to_shards.py"),
        )
        self.assertLess(
            idx("apply_kis_axis_wide_membership_worklist_to_shards.py"),
            idx("build_kis_axis_wide_membership_response_validator.py"),
        )
        self.assertLess(
            idx("build_kis_axis_wide_membership_response_validator.py"),
            idx("apply_kis_axis_wide_membership_import.py"),
        )
        self.assertLess(
            idx("apply_kis_axis_wide_membership_import.py"),
            idx("build_kis_axis_wide_membership_coverage_progress.py"),
        )
        self.assertLess(
            idx("build_kis_axis_wide_membership_coverage_progress.py"),
            idx("build_kis_pit_next_evidence_fill_card.py"),
        )
        self.assertEqual(
            stack_mod.SCRIPT_EXTRA_ARGS["run_cand022_provider_return_watch.py"],
            ["--cycles", "1", "--sleep-seconds", "0", "--no-refresh"],
        )
        self.assertEqual(
            stack_mod.SCRIPT_EXTRA_ARGS["ensure_cand022_provider_return_watch_continuity.py"],
            ["--start-if-needed"],
        )
        self.assertLess(
            idx("build_cand022_next_action_router.py"),
            idx("build_cand022_operator_status_brief.py"),
        )
        self.assertLess(
            idx("build_cand022_operator_status_brief.py"),
            idx("build_cand022_stage6_user_action_card.py"),
        )
        self.assertLess(
            idx("build_cand022_stage6_user_action_card.py"),
            idx("build_cand022_stage6_two_path_decision_slip.py"),
        )
        self.assertLess(
            idx("build_cand022_stage6_two_path_decision_slip.py"),
            idx("build_kis_provider_external_presend_verifier.py"),
        )
        self.assertLess(
            idx("build_kis_provider_external_presend_verifier.py"),
            idx("build_kis_provider_external_dispatch_instruction_packet.py"),
        )
        self.assertLess(
            idx("build_kis_provider_external_dispatch_instruction_packet.py"),
            last_idx("build_cand022_operator_status_brief.py"),
        )
        self.assertLess(
            last_idx("build_cand022_operator_status_brief.py"),
            idx("build_cand022_manual_dispatch_execution_slip.py"),
        )
        self.assertLess(
            idx("build_cand022_manual_dispatch_execution_slip.py"),
            idx("build_cand022_provider_dispatch_eml_draft.py"),
        )
        self.assertLess(
            idx("build_cand022_provider_dispatch_eml_draft.py"),
            idx("build_cand022_dispatch_confirmation_dry_run_from_eml.py"),
        )
        self.assertLess(
            idx("build_cand022_dispatch_confirmation_dry_run_from_eml.py"),
            idx("build_cand022_stage6_entry_path_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_stage6_entry_path_audit.py"),
            idx("build_cand022_stage6_operator_wait_packet.py"),
        )
        self.assertLess(
            idx("build_cand022_stage6_operator_wait_packet.py"),
            idx("build_cand022_dispatch_guidance_consistency_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_dispatch_guidance_consistency_audit.py"),
            idx("build_cand022_dispatch_stale_freeze_surface_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_dispatch_stale_freeze_surface_audit.py"),
            idx("build_cand022_active_thread_goal_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_active_thread_goal_audit.py"),
            idx("build_cand022_blocked_wait_state.py"),
        )
        self.assertLess(
            idx("build_cand022_active_thread_goal_audit.py"),
            idx("build_stage13_completion_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_blocked_wait_state.py"),
            idx("build_stage13_completion_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_stage6_goal_completion_audit.py"),
            idx("build_stage6_operating_status.py"),
        )
        self.assertLess(
            idx("build_stage6_operating_status.py"),
            idx("build_cand022_active_thread_goal_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_active_thread_goal_audit.py"),
            idx("build_stage13_completion_audit.py"),
        )
        self.assertLess(
            idx("build_kis_provider_external_dispatch_send_status.py"),
            idx("build_cand022_active_thread_goal_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_tiny_live_precondition_status.py"),
            idx("build_cand022_operator_decision_packet.py"),
        )
        self.assertLess(
            idx("build_cand022_operator_decision_packet.py"),
            idx("build_cand022_shadow_only_exception_contract.py"),
        )
        self.assertLess(
            idx("build_cand022_shadow_only_exception_contract.py"),
            idx("build_cand022_shadow_exception_apply_preflight.py"),
        )
        self.assertLess(
            idx("build_cand022_shadow_exception_apply_preflight.py"),
            idx("build_cand022_pretrade_firewall_dry_run.py"),
        )
        self.assertLess(
            idx("build_cand022_pretrade_firewall_dry_run.py"),
            idx("build_cand022_current_signal_observation.py"),
        )
        self.assertLess(
            idx("build_cand022_current_signal_observation.py"),
            idx("build_cand022_kis_tradable_mapping_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_kis_tradable_mapping_audit.py"),
            idx("build_cand022_stage6_prequeue_dry_run.py"),
        )
        self.assertLess(
            idx("build_cand022_stage6_prequeue_dry_run.py"),
            idx("build_cand022_stage6_shadow_loop_dry_run.py"),
        )
        self.assertLess(
            idx("build_cand022_stage6_shadow_loop_dry_run.py"),
            idx("build_cand022_stage6_shadow_readiness_packet.py"),
        )
        self.assertLess(
            idx("build_cand022_stage6_shadow_readiness_packet.py"),
            idx("run_cand022_shadow_only_exception_apply_and_verify.py"),
        )
        self.assertLess(
            idx("run_cand022_shadow_only_exception_apply_and_verify.py"),
            idx("build_cand022_stage6_blocker_closure_plan.py"),
        )
        self.assertLess(
            idx("build_cand022_stage6_prequeue_dry_run.py"),
            idx("build_cand022_stage6_blocker_closure_plan.py"),
        )
        self.assertLess(
            idx("build_cand022_stage6_shadow_loop_dry_run.py"),
            idx("build_cand022_stage6_goal_completion_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_stage6_blocker_closure_plan.py"),
            idx("build_cand022_tiny_live_completion_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_operator_decision_packet.py"),
            idx("build_cand022_tiny_live_completion_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_operator_decision_packet.py"),
            idx("build_cand022_active_thread_goal_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_stage6_blocker_closure_plan.py"),
            idx("build_cand022_stage6_goal_completion_audit.py"),
        )
        self.assertLess(
            idx("run_cand022_shadow_only_exception_apply_and_verify.py"),
            idx("build_cand022_stage6_goal_completion_audit.py"),
        )
        self.assertEqual(
            stack_mod.SCRIPT_EXTRA_ARGS["run_cand022_shadow_only_exception_apply_and_verify.py"],
            [
                "--operator-instruction",
                "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY",
            ],
        )
        self.assertLess(
            idx("build_cand022_stage6_goal_completion_audit.py"),
            idx("build_cand022_active_thread_goal_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_stage6_goal_completion_audit.py"),
            idx("build_kis_pit_intake_import_preflight.py"),
        )
        self.assertLess(
            idx("build_kis_pit_intake_import_preflight.py"),
            idx("build_kis_pit_intake_work_order.py"),
        )
        self.assertLess(
            idx("build_kis_pit_intake_work_order.py"),
            idx("build_kis_pit_next_evidence_fill_card.py"),
        )
        self.assertLess(
            idx("build_kis_pit_next_evidence_fill_card.py"),
            idx("update_kis_pit_intake_row.py"),
        )
        self.assertLess(
            idx("update_kis_pit_intake_row.py"),
            idx("update_kis_pit_source_artifact_registry.py"),
        )
        self.assertLess(
            idx("update_kis_pit_source_artifact_registry.py"),
            idx("apply_kis_pit_next_evidence_bundle.py"),
        )
        self.assertLess(
            idx("apply_kis_pit_next_evidence_bundle.py"),
            idx("build_kis_pit_source_artifact_registry_verifier.py"),
        )
        self.assertLess(
            idx("build_kis_pit_source_artifact_registry_verifier.py"),
            idx("build_kis_pit_intake_source_provenance_verifier.py"),
        )
        self.assertLess(
            idx("build_kis_pit_intake_source_provenance_verifier.py"),
            idx("apply_kis_pit_intake_canonical_import.py"),
        )
        self.assertLess(
            idx("apply_kis_pit_intake_canonical_import.py"),
            last_idx("build_cand022_stage6_user_action_card.py"),
        )
        self.assertLess(
            last_idx("build_cand022_stage6_user_action_card.py"),
            last_idx("build_cand022_stage6_two_path_decision_slip.py"),
        )
        self.assertLess(
            last_idx("build_cand022_stage6_two_path_decision_slip.py"),
            idx("build_cand022_active_thread_goal_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_stage6_goal_completion_audit.py"),
            idx("build_stage13_completion_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_stage6_goal_completion_audit.py"),
            idx("build_stage6_operating_status.py"),
        )
        self.assertLess(
            idx("build_stage6_operating_status.py"),
            idx("build_cand022_active_thread_goal_audit.py"),
        )
        self.assertLess(
            idx("build_cand022_active_thread_goal_audit.py"),
            idx("build_stage13_completion_audit.py"),
        )

    def test_dry_run_output_paths_do_not_overwrite_operational_latest(self) -> None:
        paths = stack_mod.output_paths("20260514_030000", dry_run=True)

        self.assertTrue(paths["json"].name.endswith(".dry_run_latest.json"))
        self.assertTrue(paths["md"].name.endswith(".dry_run_latest.md"))
        self.assertNotEqual(paths["json"].name, "CAND-022_provider_response_refresh_stack.latest.json")
        self.assertNotEqual(paths["md"].name, "CAND-022_provider_response_refresh_stack.latest.md")

    def test_normal_output_paths_write_operational_latest(self) -> None:
        paths = stack_mod.output_paths("20260514_030000", dry_run=False)

        self.assertEqual(paths["json"].name, "CAND-022_provider_response_refresh_stack.latest.json")
        self.assertEqual(paths["md"].name, "CAND-022_provider_response_refresh_stack.latest.md")


if __name__ == "__main__":
    unittest.main()
