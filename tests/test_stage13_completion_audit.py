from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stage13_completion_audit.py")
SPEC = importlib.util.spec_from_file_location("build_stage13_completion_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class Stage13CompletionAuditTests(unittest.TestCase):
    def test_current_external_blockers_prevent_completion(self) -> None:
        report = audit.build_report(
            "2026-05-14T00:00:00+09:00",
            active_audit={
                "status": "NOT_COMPLETE_BLOCKED_BY_EXTERNAL_DISPATCH_AND_PROVIDER_ROWS",
                "missing_or_blocked_check_ids": [
                    "dispatch_sent_confirmation_recorded",
                    "returned_provider_csvs_received",
                ],
                "single_next_action": "send frozen packet",
                "safety": audit.SAFETY,
            },
            tiny_live={
                "summary": {
                    "stage5_internal_evidence_passed": True,
                    "shadow_queue_allowed": False,
                    "shadow_passed": False,
                },
                "failed_required_check_ids": [
                    "human_mandate_complete",
                    "kis_pit_manifest_operation_ready",
                    "membership_files_operation_ready",
                    "stage6_shadow_ready_and_passed",
                    "pretrade_firewall_passed_without_unsafe_submit",
                ],
                "safety": audit.SAFETY,
            },
            wait_state={
                "status": "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS",
                "missing_or_blocked_check_ids": ["source_backed_rows_complete"],
                "safety": audit.SAFETY,
            },
            watcher_process_status={
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
                "safety": audit.SAFETY,
            },
            transition={
                "decision_records_written": 47,
                "blocked_transition_count": 29,
                "shadow_queue_records": 1,
                "stage5_passed_records": 2,
                "safety": audit.SAFETY,
            },
            stage6_entry={
                "stage6_reached": False,
                "entry_path_status": "READY_WAIT_OPERATOR_OR_PROVIDER_INPUT",
                "provider_dispatch_path": {"status": "READY_WAIT_ACTUAL_SEND_AND_RETURNED_ROWS"},
                "shadow_only_exception_path": {"status": "READY_WAIT_EXACT_OPERATOR_INSTRUCTION"},
            },
        )

        self.assertEqual(report["completion_decision"], "NOT_COMPLETE")
        self.assertEqual(report["canonical_stage_source"], r"C:\AI\AGENTS.md")
        self.assertTrue(str(report["stage_policy_implementation"]).endswith("build_stage13_completion_audit.py"))
        self.assertIn("BITHUMB_KRW", report["objective_restatement"])
        self.assertIn("KIS_COMBINED_KRW", report["objective_restatement"])
        self.assertEqual(report["current_milestone"], "PROVE_TINY_LIVE_PRECONDITIONS_UNDER_HARD_CAP_POLICY")
        self.assertEqual(report["current_target_stage_id"], 9)
        self.assertEqual(report["current_target_stage_name"], "Tiny Limited Live Request")
        self.assertFalse(report["current_target_stage_reached"])
        self.assertFalse(report["stage13_complete"])
        self.assertTrue(report["blocked_by_external_input"])
        self.assertIn("stage13", report["failed_required_stage_ids"])
        self.assertIn("external_dispatch", report["failed_required_stage_ids"])
        self.assertNotIn("stage6", report["failed_required_stage_ids"])
        self.assertNotIn("stage7", report["failed_required_stage_ids"])
        self.assertNotIn("stage8", report["failed_required_stage_ids"])
        self.assertIn("dispatch_sent_confirmation_recorded", report["missing_or_blocked_check_ids"])
        self.assertEqual(report["single_next_action"], "send frozen packet")
        retired_row = next(row for row in report["prompt_to_artifact_checklist"] if row["stage_id"] == "retired_shadow_paper_state")
        bithumb_row = next(row for row in report["prompt_to_artifact_checklist"] if row["stage_id"] == "axis_bithumb_krw")
        self.assertFalse(bithumb_row["required_for_stage13"])
        self.assertIn("bithumb_oos_walkforward", report["source_files"])
        self.assertIn("bithumb_nonzero_signal_scout", report["source_files"])
        self.assertIn("bithumb_orca_oos_family_review", report["source_files"])
        self.assertIn("bithumb_gatekeeper_review_packet", report["source_files"])
        self.assertIn("bithumb_shadow_preflight", report["source_files"])
        self.assertIn("BITHUMB_KRW", report["axis_next_actions"])
        self.assertIn("KIS_COMBINED_KRW", report["axis_next_actions"])
        self.assertFalse(retired_row["required_for_stage13"])
        self.assertTrue(retired_row["passed"])
        self.assertEqual(
            retired_row["observed"]["interpretation"],
            "shadow_and_paper_are_removed_from_required_stage_progress",
        )
        watcher_row = next(row for row in report["prompt_to_artifact_checklist"] if row["stage_id"] == "provider_return_watch_process")
        self.assertTrue(watcher_row["passed"])
        self.assertEqual(watcher_row["observed"]["watcher_process_ids"], [4340])
        self.assertIn("provider_return_watch_process_status", report["source_files"])
        self.assertIn("stage6_goal_completion_audit", report["source_files"])
        self.assertFalse(report["safety"]["paper_enabled"])
        self.assertEqual(report["safety"]["pretrade_firewall_default_decision"], "BLOCK")

    def test_safety_drift_is_failed_even_if_other_inputs_exist(self) -> None:
        unsafe = dict(audit.SAFETY)
        unsafe["order_intent_created"] = True
        report = audit.build_report(
            "2026-05-14T00:00:00+09:00",
            active_audit={"missing_or_blocked_check_ids": [], "safety": unsafe},
            tiny_live={"summary": {"stage5_internal_evidence_passed": True, "shadow_passed": True}, "failed_required_check_ids": [], "safety": unsafe},
            wait_state={"status": "CLEAR", "missing_or_blocked_check_ids": [], "safety": unsafe},
            watcher_process_status={
                "status": "WATCHER_RUNNING",
                "ready_for_unattended_wait": True,
                "provider_return_watch_policy": {
                    "copy_review_required_before_refresh": True,
                    "refresh_stack_invocation_policy": "manual_after_returned_to_handoff_copy_review_ready",
                },
                "safety": unsafe,
            },
            transition={"decision_records_written": 1, "shadow_queue_records": 1, "stage5_passed_records": 1, "safety": unsafe},
        )

        self.assertIn("safety", report["failed_required_stage_ids"])
        safety_row = next(row for row in report["prompt_to_artifact_checklist"] if row["stage_id"] == "safety")
        self.assertFalse(safety_row["passed"])

    def test_markdown_includes_retired_shadow_paper_state(self) -> None:
        report = audit.build_report(
            "2026-05-14T00:00:00+09:00",
            active_audit={"missing_or_blocked_check_ids": [], "safety": audit.SAFETY},
            tiny_live={
                "summary": {"stage5_internal_evidence_passed": True, "shadow_queue_allowed": False, "shadow_passed": False},
                "failed_required_check_ids": ["stage6_shadow_ready_and_passed"],
                "safety": audit.SAFETY,
            },
            wait_state={"status": "WAIT", "missing_or_blocked_check_ids": [], "safety": audit.SAFETY},
            watcher_process_status={
                "status": "WATCHER_RUNNING",
                "ready_for_unattended_wait": True,
                "provider_return_watch_policy": {
                    "copy_review_required_before_refresh": True,
                    "refresh_stack_invocation_policy": "manual_after_returned_to_handoff_copy_review_ready",
                },
                "safety": audit.SAFETY,
            },
            transition={"decision_records_written": 1, "shadow_queue_records": 1, "stage5_passed_records": 1, "safety": audit.SAFETY},
            stage6_entry={
                "stage6_reached": False,
                "entry_path_status": "READY_WAIT_OPERATOR_OR_PROVIDER_INPUT",
                "provider_dispatch_path": {"status": "READY_WAIT_ACTUAL_SEND_AND_RETURNED_ROWS"},
                "shadow_only_exception_path": {"status": "READY_WAIT_EXACT_OPERATOR_INSTRUCTION"},
            },
        )

        md = audit.render_markdown(report)

        self.assertIn("## Retired Shadow/Paper State", md)
        self.assertIn("current_target_stage", md)
        self.assertIn("Stage 9 - Tiny Limited Live Request", md)
        self.assertIn("retired_from_required_stage_progress", md)
        self.assertIn("shadow_and_paper_are_removed_from_required_stage_progress", md)

    def test_watcher_process_status_is_informational_not_stage13_required(self) -> None:
        report = audit.build_report(
            "2026-05-14T00:00:00+09:00",
            active_audit={"missing_or_blocked_check_ids": [], "safety": audit.SAFETY},
            tiny_live={
                "summary": {"stage5_internal_evidence_passed": True, "shadow_passed": True},
                "failed_required_check_ids": [],
                "safety": audit.SAFETY,
            },
            wait_state={"status": "CLEAR", "missing_or_blocked_check_ids": [], "safety": audit.SAFETY},
            watcher_process_status={
                "status": "WATCHER_NOT_RUNNING_WAITING_FOR_EXTERNAL_INPUT",
                "ready_for_unattended_wait": False,
                "safety": audit.SAFETY,
            },
            transition={"decision_records_written": 1, "shadow_queue_records": 1, "stage5_passed_records": 1, "safety": audit.SAFETY},
        )

        watcher_row = next(row for row in report["prompt_to_artifact_checklist"] if row["stage_id"] == "provider_return_watch_process")
        self.assertFalse(watcher_row["required_for_stage13"])
        self.assertFalse(watcher_row["passed"])
        self.assertIn("provider_return_watch_process_not_ready", report["missing_or_blocked_check_ids"])

    def test_official_kis_gap_matrix_replaces_external_dispatch_requirement(self) -> None:
        report = audit.build_report(
            "2026-05-16T09:00:00+09:00",
            active_audit={
                "missing_or_blocked_check_ids": ["dispatch_sent_confirmation_recorded"],
                "single_next_action": "old external dispatch action",
                "safety": audit.SAFETY,
            },
            tiny_live={
                "summary": {"stage5_internal_evidence_passed": True, "shadow_passed": False},
                "failed_required_check_ids": [
                    "kis_pit_manifest_operation_ready",
                    "membership_files_operation_ready",
                    "stage6_shadow_ready_and_passed",
                ],
                "safety": audit.SAFETY,
            },
            wait_state={
                "status": "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS",
                "missing_or_blocked_check_ids": ["returned_provider_csvs_received"],
                "safety": audit.SAFETY,
            },
            watcher_process_status={"status": "WATCHER_RUNNING", "ready_for_unattended_wait": True, "safety": audit.SAFETY},
            transition={"decision_records_written": 1, "shadow_queue_records": 1, "stage5_passed_records": 1, "safety": audit.SAFETY},
            official_kis_route={
                "status": "OFFICIAL_KIS_ROUTE_RESCOPED",
                "pipeline_decision": {"retire_default_external_provider_dispatch": True},
            },
            operator_status_brief={"single_next_action": "official KIS current-readiness, historical PIT blocked"},
            kis_historical_gap_matrix={
                "status": "BLOCK_HISTORICAL_PIT_SURVIVORSHIP_GAPS",
                "gate_summary": {"first_blocked_gate_id": "G1_MEMBERSHIP_INTERVALS_OPERATION_READY"},
                "remaining_blockers": ["canonical_membership_evidence_quality_caveated_not_operation_ready"],
            },
            kis_source_acquisition_queue={"single_next_action": "acquire first operation-ready membership row"},
            kis_intake_import_preflight={
                "status": "BLOCK_INTAKE_IMPORT_PREFLIGHT",
                "ready_row_count": 0,
                "blocked_row_count": 18,
                "blockers": ["required_fields_missing", "evidence_quality_not_operation_ready"],
            },
            kis_intake_work_order={
                "status": "BLOCK_INTAKE_WORK_ORDER_OPEN",
                "minimal_cand022_blocked_task_count": 18,
                "single_next_action": "fill work order",
            },
            kis_next_evidence_fill_card={
                "status": "BLOCK_NEXT_EVIDENCE_FILL_REQUIRED",
                "queue_id": "KIS_SRC_001",
                "symbol": "MU",
            },
            kis_next_evidence_bundle_apply={
                "status": "BLOCK_KIS_PIT_NEXT_EVIDENCE_BUNDLE",
                "files_mutated": False,
                "blockers": ["registry_update_blocked", "intake_row_update_blocked"],
            },
            kis_intake_row_update={
                "status": "BLOCK_INTAKE_ROW_UPDATE",
                "intake_file_mutated": False,
                "blockers": ["required_update_fields_missing"],
            },
            kis_source_artifact_registry_update={
                "status": "BLOCK_SOURCE_ARTIFACT_REGISTRY_UPDATE",
                "registry_file_mutated": False,
                "blockers": ["artifact_path_missing"],
            },
            kis_source_artifact_registry={
                "status": "BLOCK_SOURCE_ARTIFACT_REGISTRY",
                "registry_row_count": 0,
                "blockers": ["no_ready_rows_to_match_artifacts"],
            },
            kis_intake_source_provenance={
                "status": "BLOCK_INTAKE_SOURCE_PROVENANCE",
                "blocked_ready_row_count": 0,
                "blockers": ["no_ready_rows_to_verify"],
            },
            kis_canonical_import_apply={
                "status": "BLOCK_CANONICAL_IMPORT_APPLY",
                "canonical_files_mutated": False,
                "blockers": ["intake_preflight_not_ready", "no_ready_rows_to_import"],
            },
            kis_axis_wide_membership_handoff_package={
                "status": "BLOCK_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE",
                "request_count": 0,
            },
            kis_axis_wide_membership_response_validator={
                "status": "BLOCK_AXIS_WIDE_MEMBERSHIP_RESPONSE",
                "valid_row_count": 0,
                "blocked_row_count": 4,
            },
            kis_axis_wide_membership_import={
                "status": "BLOCK_AXIS_WIDE_MEMBERSHIP_IMPORT",
                "canonical_files_mutated": False,
            },
            kis_axis_wide_membership_coverage_progress={},
        )

        external_row = next(row for row in report["prompt_to_artifact_checklist"] if row["stage_id"] == "external_dispatch")
        stage1_row = next(row for row in report["prompt_to_artifact_checklist"] if row["stage_id"] == "stage1")
        self.assertFalse(report["blocked_by_external_input"])
        self.assertFalse(external_row["required_for_stage13"])
        self.assertTrue(external_row["passed"])
        self.assertTrue(stage1_row["passed"])
        self.assertEqual(
            stage1_row["observed"]["current_universe_mode"],
            "KIS_OFFICIAL_GITHUB_AND_API_CAVEATED",
        )
        self.assertEqual(
            stage1_row["observed"]["pit_survivorship_role"],
            "live_promotion_caveat_not_current_pipeline_blocker",
        )
        self.assertIn(
            "canonical_membership_evidence_quality_caveated_not_operation_ready",
            stage1_row["live_promotion_caveats"],
        )
        self.assertEqual(
            stage1_row["observed"]["historical_gap_first_blocked_gate"],
            "G1_MEMBERSHIP_INTERVALS_OPERATION_READY",
        )
        self.assertEqual(stage1_row["observed"]["intake_import_preflight_status"], "BLOCK_INTAKE_IMPORT_PREFLIGHT")
        self.assertEqual(stage1_row["observed"]["intake_work_order_status"], "BLOCK_INTAKE_WORK_ORDER_OPEN")
        self.assertEqual(stage1_row["observed"]["next_evidence_fill_card_queue_id"], "KIS_SRC_001")
        self.assertEqual(stage1_row["observed"]["next_evidence_fill_card_symbol"], "MU")
        self.assertEqual(
            stage1_row["observed"]["next_evidence_bundle_apply_status"],
            "BLOCK_KIS_PIT_NEXT_EVIDENCE_BUNDLE",
        )
        self.assertFalse(stage1_row["observed"]["next_evidence_bundle_files_mutated"])
        self.assertEqual(stage1_row["observed"]["intake_row_update_status"], "BLOCK_INTAKE_ROW_UPDATE")
        self.assertFalse(stage1_row["observed"]["intake_row_update_file_mutated"])
        self.assertEqual(
            stage1_row["observed"]["source_artifact_registry_update_status"],
            "BLOCK_SOURCE_ARTIFACT_REGISTRY_UPDATE",
        )
        self.assertFalse(stage1_row["observed"]["source_artifact_registry_update_file_mutated"])
        self.assertEqual(stage1_row["observed"]["source_artifact_registry_status"], "BLOCK_SOURCE_ARTIFACT_REGISTRY")
        self.assertEqual(stage1_row["observed"]["intake_source_provenance_status"], "BLOCK_INTAKE_SOURCE_PROVENANCE")
        self.assertEqual(stage1_row["observed"]["canonical_import_apply_status"], "BLOCK_CANONICAL_IMPORT_APPLY")
        self.assertFalse(stage1_row["observed"]["canonical_import_files_mutated"])
        self.assertEqual(
            stage1_row["observed"]["axis_wide_membership_handoff_status"],
            "BLOCK_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE",
        )
        self.assertEqual(
            stage1_row["observed"]["axis_wide_membership_response_validator_status"],
            "BLOCK_AXIS_WIDE_MEMBERSHIP_RESPONSE",
        )
        self.assertEqual(
            stage1_row["observed"]["axis_wide_membership_import_status"],
            "BLOCK_AXIS_WIDE_MEMBERSHIP_IMPORT",
        )
        self.assertIn("intake_import_preflight_blocked", stage1_row["live_promotion_caveats"])
        self.assertIn("next_evidence_bundle_apply_blocked", stage1_row["live_promotion_caveats"])
        self.assertIn("registry_update_blocked", stage1_row["live_promotion_caveats"])
        self.assertIn("intake_row_update_blocked", stage1_row["live_promotion_caveats"])
        self.assertIn("artifact_path_missing", stage1_row["live_promotion_caveats"])
        self.assertIn("Next required gate is Stage 9", report["single_next_action"])
        self.assertIn("LIVE APPROVE", report["single_next_action"])
        self.assertIn("kis_pit_source_acquisition_queue", report["source_files"])
        self.assertIn("kis_pit_intake_import_preflight", report["source_files"])
        self.assertIn("kis_pit_intake_work_order", report["source_files"])
        self.assertIn("kis_pit_next_evidence_fill_card", report["source_files"])
        self.assertIn("kis_pit_next_evidence_bundle_apply", report["source_files"])
        self.assertIn("kis_pit_intake_row_update", report["source_files"])
        self.assertIn("kis_pit_source_artifact_registry_update", report["source_files"])
        self.assertIn("kis_pit_source_artifact_registry_verifier", report["source_files"])
        self.assertIn("kis_pit_intake_source_provenance_verifier", report["source_files"])
        self.assertIn("kis_pit_canonical_import_apply", report["source_files"])
        self.assertIn("kis_axis_wide_membership_handoff_package", report["source_files"])

    def test_stage13_prefers_axis_wide_handoff_next_action_over_generic_manifest_blocker(self) -> None:
        report = audit.build_report(
            "2026-05-16T10:30:00+09:00",
            active_audit={"missing_or_blocked_check_ids": [], "safety": audit.SAFETY},
            tiny_live={
                "summary": {"stage5_internal_evidence_passed": True, "shadow_passed": False},
                "failed_required_check_ids": [
                    "kis_pit_manifest_operation_ready",
                    "membership_files_operation_ready",
                    "stage6_shadow_ready_and_passed",
                ],
                "safety": audit.SAFETY,
            },
            wait_state={"status": "WAIT", "missing_or_blocked_check_ids": [], "safety": audit.SAFETY},
            watcher_process_status={"status": "WATCHER_RUNNING", "ready_for_unattended_wait": True, "safety": audit.SAFETY},
            transition={"decision_records_written": 1, "shadow_queue_records": 1, "stage5_passed_records": 1, "safety": audit.SAFETY},
            official_kis_route={
                "status": "OFFICIAL_KIS_ROUTE_RESCOPED",
                "pipeline_decision": {"retire_default_external_provider_dispatch": True},
            },
            kis_historical_gap_matrix={
                "status": "BLOCK_HISTORICAL_PIT_SURVIVORSHIP_GAPS",
                "gate_summary": {"first_blocked_gate_id": "G1_MEMBERSHIP_INTERVALS_OPERATION_READY"},
                "remaining_blockers": ["canonical_membership_evidence_quality_caveated_not_operation_ready"],
            },
            kis_source_acquisition_queue={
                "queue_counts": {"total": 4, "minimal_cand022_unblock": 0, "axis_wide_operation_ready": 4},
                "single_next_action": "generic axis queue action",
            },
            kis_intake_import_preflight={"status": "READY_FOR_MANUAL_CANONICAL_IMPORT_REVIEW"},
            kis_intake_work_order={"status": "READY_FOR_PREFLIGHT_RECHECK", "minimal_cand022_blocked_task_count": 0},
            kis_axis_wide_membership_handoff_package={
                "status": "READY_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE",
                "request_count": 4,
                "single_next_action": "fill axis-wide response template",
            },
            kis_axis_wide_membership_response_validator={
                "status": "BLOCK_AXIS_WIDE_MEMBERSHIP_RESPONSE",
                "valid_row_count": 0,
                "blocked_row_count": 4,
                "replacement_coverage_sufficient": False,
                "replacement_coverage_rows": [
                    {
                        "request_id": "KIS_AXIS_001",
                        "axis": "kis_us_stocks",
                        "required_replacement_row_count": 7392,
                        "valid_replacement_row_count": 0,
                        "remaining_replacement_row_count": 7392,
                    }
                ],
                "next_safe_action": "fill blank axis-wide rows",
            },
            kis_axis_wide_membership_import={
                "status": "BLOCK_AXIS_WIDE_MEMBERSHIP_IMPORT",
                "canonical_files_mutated": False,
            },
            kis_axis_wide_membership_coverage_progress={
                "status": "BLOCK_AXIS_WIDE_MEMBERSHIP_COVERAGE_PROGRESS",
                "ready_axis_count": 0,
                "blocked_axis_count": 4,
                "valid_response_row_count": 0,
                "blocked_response_row_count": 4,
                "single_next_action": "fill blank axis-wide rows",
            },
            kis_operation_ready_manifest={
                "status": "BLOCK_OPERATION_READY_MANIFEST",
                "blockers": ["membership_verifier_not_operation_ready", "upgrade_plan_not_ready_for_registry_review"],
            },
        )

        stage1_row = next(row for row in report["prompt_to_artifact_checklist"] if row["stage_id"] == "stage1")
        self.assertIn("Next required gate is Stage 9", report["single_next_action"])
        self.assertIn("LIVE APPROVE", report["single_next_action"])
        self.assertEqual(
            stage1_row["observed"]["axis_wide_membership_handoff_status"],
            "READY_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE",
        )
        self.assertEqual(stage1_row["observed"]["axis_wide_membership_handoff_request_count"], 4)
        self.assertEqual(
            stage1_row["observed"]["axis_wide_membership_response_validator_status"],
            "BLOCK_AXIS_WIDE_MEMBERSHIP_RESPONSE",
        )
        self.assertEqual(stage1_row["observed"]["axis_wide_membership_response_valid_row_count"], 0)
        self.assertEqual(stage1_row["observed"]["axis_wide_membership_response_blocked_row_count"], 4)
        self.assertFalse(stage1_row["observed"]["axis_wide_membership_response_replacement_coverage_sufficient"])
        self.assertEqual(
            stage1_row["observed"]["axis_wide_membership_response_replacement_coverage_rows"][0][
                "required_replacement_row_count"
            ],
            7392,
        )
        self.assertEqual(stage1_row["observed"]["axis_wide_membership_import_status"], "BLOCK_AXIS_WIDE_MEMBERSHIP_IMPORT")
        self.assertEqual(
            stage1_row["observed"]["axis_wide_membership_coverage_progress_status"],
            "BLOCK_AXIS_WIDE_MEMBERSHIP_COVERAGE_PROGRESS",
        )
        self.assertEqual(stage1_row["observed"]["axis_wide_membership_coverage_blocked_axis_count"], 4)

    def test_stage13_surfaces_axis_wide_import_review_when_validator_ready(self) -> None:
        report = audit.build_report(
            "2026-05-16T12:30:00+09:00",
            active_audit={"missing_or_blocked_check_ids": [], "safety": audit.SAFETY},
            tiny_live={
                "summary": {"stage5_internal_evidence_passed": True, "shadow_passed": False},
                "failed_required_check_ids": [
                    "kis_pit_manifest_operation_ready",
                    "membership_files_operation_ready",
                    "stage6_shadow_ready_and_passed",
                ],
                "safety": audit.SAFETY,
            },
            wait_state={"status": "WAIT", "missing_or_blocked_check_ids": [], "safety": audit.SAFETY},
            watcher_process_status={"status": "WATCHER_RUNNING", "ready_for_unattended_wait": True, "safety": audit.SAFETY},
            transition={"decision_records_written": 1, "shadow_queue_records": 1, "stage5_passed_records": 1, "safety": audit.SAFETY},
            official_kis_route={
                "status": "OFFICIAL_KIS_ROUTE_RESCOPED",
                "pipeline_decision": {"retire_default_external_provider_dispatch": True},
            },
            kis_historical_gap_matrix={
                "status": "BLOCK_HISTORICAL_PIT_SURVIVORSHIP_GAPS",
                "gate_summary": {"first_blocked_gate_id": "G1_MEMBERSHIP_INTERVALS_OPERATION_READY"},
                "remaining_blockers": ["canonical_membership_evidence_quality_caveated_not_operation_ready"],
            },
            kis_source_acquisition_queue={
                "queue_counts": {"total": 4, "minimal_cand022_unblock": 0, "axis_wide_operation_ready": 4},
                "single_next_action": "generic axis queue action",
            },
            kis_intake_import_preflight={"status": "READY_FOR_MANUAL_CANONICAL_IMPORT_REVIEW"},
            kis_intake_work_order={"status": "READY_FOR_PREFLIGHT_RECHECK", "minimal_cand022_blocked_task_count": 0},
            kis_axis_wide_membership_handoff_package={
                "status": "READY_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE",
                "request_count": 4,
                "single_next_action": "fill axis-wide response template",
            },
            kis_axis_wide_membership_response_validator={
                "status": "READY_AXIS_WIDE_MEMBERSHIP_IMPORT_REVIEW",
                "valid_row_count": 4,
                "blocked_row_count": 0,
                "replacement_coverage_sufficient": True,
                "next_safe_action": "review valid rows",
            },
            kis_axis_wide_membership_import={
                "status": "DRY_RUN_READY_FOR_AXIS_WIDE_MEMBERSHIP_IMPORT",
                "canonical_files_mutated": False,
            },
            kis_axis_wide_membership_coverage_progress={
                "status": "PARTIAL_AXIS_WIDE_MEMBERSHIP_PROGRESS",
                "ready_axis_count": 0,
                "blocked_axis_count": 0,
                "valid_response_row_count": 4,
                "blocked_response_row_count": 0,
                "single_next_action": "Review and apply axis-wide membership import with the guarded confirmation phrase.",
            },
            kis_operation_ready_manifest={
                "status": "BLOCK_OPERATION_READY_MANIFEST",
                "blockers": ["membership_verifier_not_operation_ready"],
            },
        )

        stage1_row = next(row for row in report["prompt_to_artifact_checklist"] if row["stage_id"] == "stage1")
        self.assertIn("Next required gate is Stage 9", report["single_next_action"])
        self.assertIn("LIVE APPROVE", report["single_next_action"])
        self.assertEqual(
            stage1_row["observed"]["axis_wide_membership_import_status"],
            "DRY_RUN_READY_FOR_AXIS_WIDE_MEMBERSHIP_IMPORT",
        )
        self.assertFalse(stage1_row["observed"]["axis_wide_membership_import_canonical_files_mutated"])

    def test_stage13_prefers_worklist_fill_progress_next_action(self) -> None:
        report = audit.build_report(
            "2026-05-16T14:30:00+09:00",
            active_audit={"missing_or_blocked_check_ids": [], "safety": audit.SAFETY},
            tiny_live={
                "summary": {"stage5_internal_evidence_passed": True, "shadow_passed": False},
                "failed_required_check_ids": [
                    "kis_pit_manifest_operation_ready",
                    "membership_files_operation_ready",
                    "stage6_shadow_ready_and_passed",
                ],
                "safety": audit.SAFETY,
            },
            wait_state={"status": "WAIT", "missing_or_blocked_check_ids": [], "safety": audit.SAFETY},
            watcher_process_status={"status": "WATCHER_RUNNING", "ready_for_unattended_wait": True, "safety": audit.SAFETY},
            transition={"decision_records_written": 1, "shadow_queue_records": 1, "stage5_passed_records": 1, "safety": audit.SAFETY},
            official_kis_route={
                "status": "OFFICIAL_KIS_ROUTE_RESCOPED",
                "pipeline_decision": {"retire_default_external_provider_dispatch": True},
            },
            kis_historical_gap_matrix={
                "status": "BLOCK_HISTORICAL_PIT_SURVIVORSHIP_GAPS",
                "gate_summary": {"first_blocked_gate_id": "G1_MEMBERSHIP_INTERVALS_OPERATION_READY"},
                "remaining_blockers": ["canonical_membership_evidence_quality_caveated_not_operation_ready"],
            },
            kis_axis_wide_membership_coverage_progress={
                "status": "BLOCK_AXIS_WIDE_MEMBERSHIP_COVERAGE_PROGRESS",
                "ready_axis_count": 0,
                "blocked_axis_count": 4,
                "single_next_action": "generic coverage action",
            },
            kis_axis_wide_membership_worklist_fill_progress={
                "status": "BLOCK_WORKLIST_FILL_PROGRESS",
                "complete_row_count": 0,
                "blocked_row_count": 16444,
                "completion_ratio": 0.0,
                "single_next_action": "fill replacement worklist fields",
            },
            kis_axis_wide_historical_source_feasibility_matrix={
                "status": "BLOCK_NO_DIRECT_OPERATION_READY_HISTORICAL_SOURCE_CAPTURED",
                "direct_operation_ready_source_count": 0,
                "promising_source_count": 2,
            },
            kis_axis_wide_source_export_intake_contract={
                "status": "BLOCK_SOURCE_EXPORT_INTAKE",
                "valid_export_count": 0,
                "manifest_path": r"C:\AI\data_snapshots\kis_pit_membership\axis_wide_source_exports\axis_wide_source_export_manifest.csv",
            },
            kis_axis_wide_source_export_inbox_status={
                "status": "BLOCK_NO_SOURCE_EXPORT_FILES_IN_INBOX",
                "actionable_file_count": 0,
                "unreferenced_normalized_export_count": 0,
                "unreferenced_raw_or_unknown_export_count": 0,
            },
            kis_axis_wide_source_export_next_command={
                "status": "BLOCK_NO_ACTIONABLE_SOURCE_EXPORT_FILE",
                "command_kind": "none",
            },
            krx_data_marketplace_access_probe={
                "status": "BLOCK_KRX_DATA_MARKETPLACE_UNATTENDED_ACCESS",
                "operation_ready": False,
            },
            kis_axis_wide_source_export_operator_packet={
                "status": "READY_OPERATOR_SOURCE_EXPORT_PACKET",
                "valid_export_count": 0,
                "single_next_action": "use operator packet for source export intake",
            },
            kis_axis_wide_source_exports_to_replacement_worklist={
                "status": "BLOCK_SOURCE_EXPORTS_TO_REPLACEMENT_WORKLIST",
                "matched_worklist_row_count": 0,
                "unmatched_worklist_row_count": 16444,
                "coverage_ratio": 0.0,
                "full_coverage_ready": False,
                "worklist_mutated": False,
            },
            kis_axis_wide_membership_worklist_to_shards={
                "status": "BLOCK_WORKLIST_TO_RESPONSE_SHARDS",
                "response_shards_mutated": False,
                "next_safe_action": "convert worklist to shards",
            },
        )

        stage1_row = next(row for row in report["prompt_to_artifact_checklist"] if row["stage_id"] == "stage1")
        self.assertFalse(report["blocked_by_external_input"])
        self.assertNotIn("reviewed_axis_wide_source_export_missing", report["external_input_blockers"])
        self.assertIn("Next required gate is Stage 9", report["single_next_action"])
        self.assertIn("LIVE APPROVE", report["single_next_action"])
        self.assertEqual(stage1_row["observed"]["axis_wide_membership_worklist_fill_status"], "BLOCK_WORKLIST_FILL_PROGRESS")
        self.assertEqual(stage1_row["observed"]["axis_wide_membership_worklist_blocked_row_count"], 16444)
        self.assertEqual(
            stage1_row["observed"]["axis_wide_historical_source_feasibility_status"],
            "BLOCK_NO_DIRECT_OPERATION_READY_HISTORICAL_SOURCE_CAPTURED",
        )
        self.assertEqual(stage1_row["observed"]["axis_wide_historical_source_direct_operation_ready_source_count"], 0)
        self.assertEqual(stage1_row["observed"]["axis_wide_source_export_intake_status"], "BLOCK_SOURCE_EXPORT_INTAKE")
        self.assertEqual(stage1_row["observed"]["axis_wide_source_export_intake_valid_export_count"], 0)
        self.assertEqual(
            stage1_row["observed"]["axis_wide_source_export_inbox_status"],
            "BLOCK_NO_SOURCE_EXPORT_FILES_IN_INBOX",
        )
        self.assertEqual(stage1_row["observed"]["axis_wide_source_export_inbox_actionable_file_count"], 0)
        self.assertEqual(
            stage1_row["observed"]["axis_wide_source_export_next_command_status"],
            "BLOCK_NO_ACTIONABLE_SOURCE_EXPORT_FILE",
        )
        self.assertEqual(stage1_row["observed"]["axis_wide_source_export_next_command_kind"], "none")
        self.assertEqual(
            stage1_row["observed"]["krx_data_marketplace_access_probe_status"],
            "BLOCK_KRX_DATA_MARKETPLACE_UNATTENDED_ACCESS",
        )
        self.assertFalse(stage1_row["observed"]["krx_data_marketplace_access_probe_operation_ready"])
        self.assertEqual(
            stage1_row["observed"]["axis_wide_source_export_operator_packet_status"],
            "READY_OPERATOR_SOURCE_EXPORT_PACKET",
        )
        self.assertEqual(
            stage1_row["observed"]["axis_wide_source_exports_to_worklist_status"],
            "BLOCK_SOURCE_EXPORTS_TO_REPLACEMENT_WORKLIST",
        )
        self.assertEqual(stage1_row["observed"]["axis_wide_source_exports_to_worklist_unmatched_row_count"], 16444)
        self.assertEqual(stage1_row["observed"]["axis_wide_source_exports_to_worklist_coverage_ratio"], 0.0)
        self.assertFalse(stage1_row["observed"]["axis_wide_source_exports_to_worklist_full_coverage_ready"])
        self.assertFalse(stage1_row["observed"]["axis_wide_source_exports_to_worklist_mutated"])
        self.assertIn("kis_axis_wide_historical_source_feasibility_matrix", report["source_files"])
        self.assertIn("kis_axis_wide_source_export_intake_contract", report["source_files"])
        self.assertIn("kis_axis_wide_source_export_inbox_status", report["source_files"])
        self.assertIn("kis_axis_wide_source_export_next_command", report["source_files"])
        self.assertIn("krx_data_marketplace_access_probe", report["source_files"])
        self.assertIn("kis_axis_wide_source_export_operator_packet", report["source_files"])
        self.assertIn("kis_axis_wide_source_exports_to_replacement_worklist", report["source_files"])

    def test_read_json_returns_default_for_transient_empty_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.json"
            empty.write_text("", encoding="utf-8")

            result = audit.read_json(empty, {"fallback": True})

        self.assertEqual(result, {"fallback": True})

    def test_read_json_reads_valid_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            valid = Path(tmp) / "valid.json"
            valid.write_text(json.dumps({"ok": True}), encoding="utf-8")

            result = audit.read_json(valid, {"fallback": True})

        self.assertEqual(result, {"ok": True})

    def test_write_json_replaces_atomically_without_tmp_residue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "audit.latest.json"

            audit.write_json(target, {"ok": True})

            result = json.loads(target.read_text(encoding="utf-8"))
            tmp_files = list(Path(tmp).glob("*.tmp"))

        self.assertEqual(result, {"ok": True})
        self.assertEqual(tmp_files, [])


if __name__ == "__main__":
    unittest.main()
