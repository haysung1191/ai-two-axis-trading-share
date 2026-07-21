from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_stage6_goal_completion_audit.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_stage6_goal_completion_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_mod)


class Cand022Stage6GoalCompletionAuditTests(unittest.TestCase):
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

    def test_stage6_reached_requires_actual_queue_or_shadow_evidence(self) -> None:
        self.assertFalse(
            audit_mod.compute_stage6_reached(
                {"readiness_decision": "PASS_SHADOW_ONLY_EXCEPTION", "shadow_queue_allowed": False},
                {"stage6_reached": False},
            )
        )
        self.assertFalse(
            audit_mod.compute_stage6_reached(
                {"readiness_decision": "BLOCK", "shadow_queue_allowed": False, "shadow_passed": False},
                {"stage6_reached": False},
            )
        )
        self.assertTrue(
            audit_mod.compute_stage6_reached(
                {
                    "readiness_decision": "PASS_SHADOW_ONLY_EXCEPTION",
                    "shadow_queue_allowed": True,
                    "shadow_only_exception_acceptance": {"active": True},
                },
                {"stage6_reached": False},
            )
        )
        self.assertTrue(
            audit_mod.compute_stage6_reached(
                {"readiness_decision": "BLOCK", "shadow_queue_allowed": False, "shadow_passed": False},
                {"stage6_reached": True},
            )
        )

    def test_returned_to_handoff_copy_review_accepts_waiting_and_ready_states(self) -> None:
        base = {
            "manual_copy_plan": [
                {"allowed_only_if_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW"},
                {"allowed_only_if_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW"},
                {"allowed_only_if_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW"},
            ],
            "non_goals": [
                "does_not_auto_copy_returned_files",
                "does_not_mutate_provider_response",
                "does_not_mutate_canonical_kis_pit_files",
            ],
            "safety": audit_mod.SAFETY,
        }
        waiting = {
            **base,
            "status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
            "returned_staging_verifier_status": "BLOCK_RETURNED_HANDOFF_STAGING",
            "blockers": [
                "membership_returned_file_missing",
                "event_or_no_event_returned_file_missing",
                "replay_returned_file_missing",
            ],
        }
        ready = {
            **base,
            "status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
            "returned_staging_verifier_status": "READY_RETURNED_HANDOFF_FOR_REVIEW",
            "blockers": [],
        }
        bad_dry_proxy = {
            **base,
            "status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
            "returned_staging_verifier_status": "BLOCK_RETURNED_HANDOFF_STAGING",
            "blockers": ["membership_returned_file_missing"],
        }

        self.assertTrue(audit_mod.returned_to_handoff_copy_review_ok(waiting))
        self.assertTrue(audit_mod.returned_to_handoff_copy_review_ok(ready))
        self.assertFalse(audit_mod.returned_to_handoff_copy_review_ok(bad_dry_proxy))

    def test_eml_inspection_ok_requires_all_structural_checks(self) -> None:
        checks = {
            "eml_exists": True,
            "to_placeholder_present": True,
            "subject_matches": True,
            "no_send_header_present": True,
            "generated_at_header_matches": True,
            "is_multipart": True,
            "single_attachment_present": True,
            "attachment_filename_matches": True,
            "attachment_payload_sha256_matches": True,
        }
        self.assertTrue(audit_mod.eml_inspection_ok({"eml_inspection": {"checks": checks, "blockers": []}}))
        missing = dict(checks)
        missing.pop("attachment_payload_sha256_matches")
        self.assertFalse(audit_mod.eml_inspection_ok({"eml_inspection": {"checks": missing, "blockers": []}}))
        failed = dict(checks)
        failed["attachment_payload_sha256_matches"] = False
        self.assertFalse(audit_mod.eml_inspection_ok({"eml_inspection": {"checks": failed, "blockers": []}}))
        self.assertFalse(
            audit_mod.eml_inspection_ok(
                {"eml_inspection": {"checks": checks, "blockers": ["attachment_payload_sha256_matches"]}}
            )
        )

    def test_current_audit_is_not_complete_until_queue_allowed_or_shadow_passed(self) -> None:
        audit = audit_mod.build_audit("2026-05-14T12:35:00+09:00")

        self.assertEqual(audit["completion_decision"], "NOT_COMPLETE")
        self.assertFalse(audit["stage6_reached"])
        self.assertTrue(audit["do_not_mark_goal_complete"])
        self.assertIn("stage6_queue_allowed_or_shadow_passed", audit["missing_or_blocked_check_ids"])
        self.assertNotIn("human_mandate_incomplete", audit["missing_or_blocked_check_ids"])
        self.assertNotIn("stage6_shadow_loop_cand022_dry_run_ready", audit["missing_or_blocked_check_ids"])
        self.assertNotIn("stage6_entry_paths_ready_waiting_for_operator_or_provider", audit["missing_or_blocked_check_ids"])
        self.assertNotIn("stage6_user_action_card_ready", audit["missing_or_blocked_check_ids"])
        self.assertNotIn("normal_provider_dispatch_presend_ready", audit["missing_or_blocked_check_ids"])
        self.assertNotIn("provider_dispatch_eml_draft_ready", audit["missing_or_blocked_check_ids"])
        self.assertNotIn("return_staging_ready_waiting_for_provider_csvs", audit["missing_or_blocked_check_ids"])
        self.assertNotIn("returned_to_handoff_copy_review_wait_state_ready", audit["missing_or_blocked_check_ids"])
        self.assertNotIn("dispatch_confirmation_dry_run_ready", audit["missing_or_blocked_check_ids"])
        self.assertIn("actual_dispatch_confirmation_recorded_or_shadow_exception_applied", audit["missing_or_blocked_check_ids"])
        self.assertIn("dispatch_sent_confirmation_recorded", audit["missing_or_blocked_check_ids"])
        self.assertNotIn("provider_return_watch_wait_state_ready", audit["missing_or_blocked_check_ids"])
        self.assertNotIn("provider_watch_continuity_ready", audit["missing_or_blocked_check_ids"])
        self.assertNotIn("guarded_shadow_only_exception_apply_ready", audit["missing_or_blocked_check_ids"])
        self.assertNotIn("shadow_only_exception_apply_and_verify_dry_run_ready", audit["missing_or_blocked_check_ids"])
        self.assertNotIn("guarded_human_mandate_apply_ready", audit["missing_or_blocked_check_ids"])
        self.assertIn("stage6_user_action_card", audit["source_files"])
        self.assertIn("stage6_entry_path_audit", audit["source_files"])
        self.assertIn("stage6_shadow_loop_dry_run", audit["source_files"])
        self.assertIn("provider_dispatch_presend_verifier", audit["source_files"])
        self.assertIn("provider_dispatch_eml_draft", audit["source_files"])
        self.assertIn("return_receipt_status", audit["source_files"])
        self.assertIn("returned_to_handoff_copy_review", audit["source_files"])
        self.assertIn("dispatch_send_status", audit["source_files"])
        self.assertIn("dispatch_confirmation_dry_run_from_eml", audit["source_files"])
        self.assertIn("shadow_only_exception_apply_and_verify", audit["source_files"])
        self.assertIn("shadow_only_exception_apply_report", audit["source_files"])
        self.assertIn("human_mandate_completion_packet", audit["source_files"])
        self.assertIn("human_mandate_completion_apply_report", audit["source_files"])
        self.assertIn("provider_return_watch", audit["source_files"])
        self.assertIn("provider_watch_continuity", audit["source_files"])
        self.assertEqual(audit["safety"], audit_mod.SAFETY)

    def test_checklist_counts_prequeue_signal_but_not_as_completion(self) -> None:
        audit = audit_mod.build_audit("2026-05-14T12:35:00+09:00")
        by_id = {row["id"]: row for row in audit["prompt_to_artifact_checklist"]}

        self.assertTrue(by_id["fresh_signal_observation_passed"]["passed"])
        self.assertTrue(by_id["prequeue_recorder_signal_ready"]["passed"])
        self.assertTrue(by_id["stage6_shadow_loop_cand022_dry_run_ready"]["passed"])
        self.assertTrue(by_id["stage6_entry_paths_ready_waiting_for_operator_or_provider"]["passed"])
        self.assertTrue(by_id["stage6_user_action_card_ready"]["passed"])
        self.assertEqual(
            by_id["stage6_user_action_card_ready"]["observed"]["recommended_path"]["post_write_sequence_contract"][
                "immediate_safe_commands"
            ],
            ["python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120"],
        )
        self.assertTrue(
            by_id["stage6_user_action_card_ready"]["observed"]["recommended_path"]["post_write_sequence_contract"][
                "copy_review_required_before_refresh"
            ]
        )
        self.assertEqual(
            by_id["stage6_user_action_card_ready"]["observed"]["recommended_path"]["post_write_sequence_contract"][
                "refresh_allowed_only_if_copy_review_status"
            ],
            "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertTrue(by_id["normal_provider_dispatch_presend_ready"]["passed"])
        self.assertTrue(by_id["provider_dispatch_eml_draft_ready"]["passed"])
        self.assertTrue(
            by_id["provider_dispatch_eml_draft_ready"]["observed"]["eml_inspection"]["checks"][
                "attachment_payload_sha256_matches"
            ]
        )
        self.assertTrue(by_id["return_staging_ready_waiting_for_provider_csvs"]["passed"])
        self.assertTrue(by_id["returned_to_handoff_copy_review_wait_state_ready"]["passed"])
        self.assertTrue(by_id["dispatch_confirmation_dry_run_ready"]["passed"])
        self.assertTrue(
            by_id["dispatch_confirmation_dry_run_ready"]["observed"]["eml_inspection"]["checks"][
                "attachment_payload_sha256_matches"
            ]
        )
        self.assertTrue(
            by_id["dispatch_confirmation_dry_run_ready"]["observed"]["dry_run_writer_report"][
                "post_write_sequence_contract"
            ]["copy_review_required_before_refresh"]
        )
        self.assertTrue(
            by_id["dispatch_confirmation_dry_run_ready"]["observed"]["dry_run_writer_report"][
                "eml_inspection_required"
            ]
        )
        self.assertTrue(
            by_id["dispatch_confirmation_dry_run_ready"]["observed"]["dry_run_writer_report"][
                "eml_inspection_ready"
            ]
        )
        self.assertIn(
            "--eml-report",
            by_id["dispatch_confirmation_dry_run_ready"]["observed"]["actual_after_send_command_template"],
        )
        self.assertEqual(
            by_id["dispatch_confirmation_dry_run_ready"]["observed"]["dry_run_writer_report"][
                "post_write_sequence_contract"
            ]["refresh_allowed_only_if_copy_review_status"],
            "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertFalse(by_id["actual_dispatch_confirmation_recorded_or_shadow_exception_applied"]["passed"])
        self.assertTrue(by_id["provider_return_watch_wait_state_ready"]["passed"])
        self.assertIsNone(by_id["provider_return_watch_wait_state_ready"]["observed"]["copy_review_result"])
        self.assertIsNone(by_id["provider_return_watch_wait_state_ready"]["observed"]["refresh_result"])
        self.assertIn(
            "does_not_run_refresh_before_returned_to_handoff_copy_review",
            by_id["provider_return_watch_wait_state_ready"]["observed"]["non_goals"],
        )
        self.assertIn(
            "kis_provider_returned_to_handoff_copy_review_latest.json",
            by_id["provider_return_watch_wait_state_ready"]["observed"]["source_files"]["copy_review"],
        )
        self.assertTrue(by_id["provider_watch_continuity_ready"]["passed"])
        self.assertTrue(by_id["guarded_shadow_only_exception_apply_ready"]["passed"])
        self.assertTrue(by_id["shadow_only_exception_apply_and_verify_dry_run_ready"]["passed"])
        self.assertTrue(by_id["guarded_human_mandate_apply_ready"]["passed"])
        self.assertEqual(
            by_id["guarded_shadow_only_exception_apply_ready"]["evidence"],
            str(audit_mod.SHADOW_EXCEPTION_APPLY_REPORT),
        )
        self.assertEqual(
            by_id["shadow_only_exception_apply_and_verify_dry_run_ready"]["evidence"],
            str(audit_mod.SHADOW_EXCEPTION_APPLY_AND_VERIFY),
        )
        self.assertIn(
            "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120",
            by_id["shadow_only_exception_apply_and_verify_dry_run_ready"]["observed"][
                "post_apply_verification_commands"
            ],
        )
        self.assertEqual(
            by_id["normal_provider_dispatch_presend_ready"]["evidence"],
            str(audit_mod.PRESEND_VERIFIER),
        )
        self.assertEqual(
            by_id["provider_dispatch_eml_draft_ready"]["evidence"],
            str(audit_mod.PROVIDER_DISPATCH_EML_DRAFT),
        )
        self.assertEqual(
            by_id["return_staging_ready_waiting_for_provider_csvs"]["evidence"],
            str(audit_mod.RETURN_RECEIPT),
        )
        self.assertEqual(
            by_id["returned_to_handoff_copy_review_wait_state_ready"]["evidence"],
            str(audit_mod.RETURNED_TO_HANDOFF_COPY_REVIEW),
        )
        self.assertEqual(
            by_id["dispatch_confirmation_dry_run_ready"]["evidence"],
            str(audit_mod.DISPATCH_CONFIRMATION_DRY_RUN),
        )
        self.assertEqual(
            by_id["actual_dispatch_confirmation_recorded_or_shadow_exception_applied"]["evidence"],
            str(audit_mod.DISPATCH_SEND_STATUS),
        )
        self.assertEqual(
            by_id["provider_return_watch_wait_state_ready"]["evidence"],
            str(audit_mod.PROVIDER_RETURN_WATCH),
        )
        self.assertEqual(
            by_id["guarded_human_mandate_apply_ready"]["evidence"],
            str(audit_mod.HUMAN_MANDATE_APPLY_REPORT),
        )
        self.assertFalse(by_id["stage6_queue_allowed_or_shadow_passed"]["passed"])
        self.assertEqual(
            by_id["stage6_entry_paths_ready_waiting_for_operator_or_provider"]["evidence"],
            str(audit_mod.STAGE6_ENTRY_PATH_AUDIT),
        )
        self.assertEqual(
            by_id["stage6_shadow_loop_cand022_dry_run_ready"]["evidence"],
            str(audit_mod.SHADOW_LOOP_DRY_RUN),
        )
        self.assertLess(audit["completion_percent_by_checklist"], 100.0)


if __name__ == "__main__":
    unittest.main()
