from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_blocked_wait_state.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_blocked_wait_state", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
wait_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wait_mod)


def router_payload(wait: dict) -> dict:
    return {
        "autonomous_continuation": wait,
        "action_router": [
            {
                "action_id": "send_external_provider_dispatch_packet",
                "status": "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION",
                "after_return_copy_review_required_before_refresh": True,
                "after_return_copy_review_artifact": (
                    "C:\\AI\\reports\\operations\\kis_provider_returned_to_handoff_copy_review_latest.json"
                ),
                "after_return_refresh_allowed_only_if_copy_review_status": (
                    "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW"
                ),
                "after_return_refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                "after_return_copy_review_then_refresh_contract": (
                    "Run build_kis_provider_returned_to_handoff_copy_review.py first."
                ),
                "action_safety": wait_mod.SAFETY,
            }
        ],
        "safety": wait_mod.SAFETY,
    }


class Cand022BlockedWaitStateTests(unittest.TestCase):
    def test_wait_state_passes_only_when_external_dispatch_or_provider_rows_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            router = root / "router.json"
            audit = root / "audit.json"
            brief = root / "brief.json"
            send = root / "send.json"
            receipt = root / "receipt.json"
            stage6_wait = root / "stage6_wait.json"
            wait = {
                "decision": "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS",
                "can_continue_local_work": False,
                "allowed_local_actions": ["refresh_status_reports", "run_read_only_audits"],
                "blocked_local_actions": [
                    "do_not_start_generic_model_search",
                    "do_not_create_order_intent",
                ],
            }
            router.write_text(json.dumps(router_payload(wait)), encoding="utf-8")
            brief.write_text(json.dumps({"autonomous_continuation": wait, "safety": wait_mod.SAFETY}), encoding="utf-8")
            audit.write_text(
                json.dumps(
                    {
                        "status": "NOT_COMPLETE_BLOCKED_BY_EXTERNAL_DISPATCH_AND_PROVIDER_ROWS",
                        "missing_or_blocked_check_ids": [
                            "dispatch_sent_confirmation_recorded",
                            "returned_provider_csvs_received",
                            "source_backed_rows_complete",
                            "tiny_live_preconditions_complete",
                        ],
                        "safety": wait_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            send.write_text(
                json.dumps(
                    {
                        "status": "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION",
                        "send_confirmation_valid": False,
                        "send_confirmation_blockers": ["dispatch_sent_confirmation_missing"],
                        "safety": wait_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            receipt.write_text(
                json.dumps(
                    {
                        "status": "WAITING_FOR_RETURNED_PROVIDER_CSVS",
                        "missing_files": ["cand022_membership_response_draft.csv"],
                        "safety": wait_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            stage6_wait.write_text(
                json.dumps(
                    {
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
                            "after_return_copy_review": {
                                "artifact": "C:\\AI\\reports\\operations\\kis_provider_returned_to_handoff_copy_review_latest.json",
                                "required_before_refresh": True,
                            },
                            "after_return_command": "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120",
                        },
                        "prompt_to_artifact_completion_audit": {
                            "complete": False,
                            "missing": ["stage6_shadow_queue_allowed_or_shadow_passed"],
                        },
                        "safety": wait_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = wait_mod.build_report(
                "2026-05-14T06:45:00+09:00",
                router_path=router,
                active_audit_path=audit,
                operator_brief_path=brief,
                send_status_path=send,
                return_receipt_path=receipt,
                stage6_wait_packet_path=stage6_wait,
            )

        self.assertEqual(report["status"], "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS")
        self.assertFalse(report["can_continue_local_work"])
        self.assertEqual(report["blockers"], [])
        self.assertIn("do_not_start_generic_model_search", report["blocked_local_actions"])
        self.assertIn("refresh_status_reports", report["allowed_local_actions"])
        self.assertIn("dispatch_sent_confirmation_recorded", report["missing_or_blocked_check_ids"])
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", report["recommended_operator_action"])
        self.assertIn("--i-confirm-actual-send", report["recommended_operator_action"])
        self.assertEqual(report["stage6_wait_packet"]["status"], "WAIT_OPERATOR_OR_PROVIDER_INPUT_TO_ADVANCE_STAGE6")
        self.assertFalse(report["stage6_wait_packet"]["stage6_reached"])
        self.assertIn("run_cand022_provider_return_watch.py", report["stage6_wait_packet"]["safe_watch_command_after_dispatch"])
        self.assertIn("--no-refresh", report["stage6_wait_packet"]["safe_watch_command_report_only"])
        self.assertTrue(report["stage6_wait_packet"]["after_return_copy_review"]["required_before_refresh"])
        self.assertIn(
            "kis_provider_returned_to_handoff_copy_review_latest.json",
            report["stage6_wait_packet"]["after_return_copy_review"]["artifact"],
        )
        self.assertIn("run_cand022_provider_response_refresh_stack.py", report["stage6_wait_packet"]["after_return_command"])
        self.assertEqual(report["router_dispatch_action"]["action_safety"], wait_mod.SAFETY)
        self.assertTrue(report["router_dispatch_action"]["after_return_copy_review_required_before_refresh"])
        self.assertEqual(
            report["router_dispatch_action"]["after_return_refresh_allowed_only_if_copy_review_status"],
            "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertEqual(
            report["router_dispatch_action"]["after_return_refresh_forbidden_if_copy_review_status"],
            "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertIn("stage6_shadow_queue_allowed_or_shadow_passed", report["stage6_wait_packet"]["missing"])
        self.assertIn("does_not_mark_goal_complete", report["non_goals"])
        self.assertEqual(report["safety"], wait_mod.SAFETY)

        md = wait_mod.render_md(report)
        self.assertIn("WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS", md)
        self.assertIn("Can continue local work: `false`", md)
        self.assertIn("do_not_start_generic_model_search", md)

    def test_wait_state_blocks_if_router_and_operator_brief_disagree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            router = root / "router.json"
            audit = root / "audit.json"
            brief = root / "brief.json"
            send = root / "send.json"
            receipt = root / "receipt.json"
            stage6_wait = root / "stage6_wait.json"
            router.write_text(
                json.dumps(
                    router_payload(
                        {
                            "decision": "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS",
                            "can_continue_local_work": False,
                        }
                    )
                ),
                encoding="utf-8",
            )
            brief.write_text(
                json.dumps(
                    {
                        "autonomous_continuation": {
                            "decision": "CONTINUE_SAFE_DATA_CLOSURE",
                            "can_continue_local_work": True,
                        },
                        "safety": wait_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            audit.write_text(
                json.dumps(
                    {
                        "status": "NOT_COMPLETE_BLOCKED_BY_EXTERNAL_DISPATCH_AND_PROVIDER_ROWS",
                        "missing_or_blocked_check_ids": [
                            "dispatch_sent_confirmation_recorded",
                            "returned_provider_csvs_received",
                            "source_backed_rows_complete",
                            "tiny_live_preconditions_complete",
                        ],
                        "safety": wait_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            send.write_text(json.dumps({"send_confirmation_valid": False, "safety": wait_mod.SAFETY}), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS", "safety": wait_mod.SAFETY}), encoding="utf-8")
            stage6_wait.write_text(
                json.dumps(
                    {
                        "status": "WAIT_OPERATOR_OR_PROVIDER_INPUT_TO_ADVANCE_STAGE6",
                        "stage6_reached": False,
                        "blocked_by_operator_or_provider": True,
                        "dispatch_wait": {
                            "safe_watch_command_after_dispatch": "python .\\run_cand022_provider_return_watch.py",
                            "safe_watch_command_report_only": "python .\\run_cand022_provider_return_watch.py --no-refresh",
                            "after_return_copy_review": {
                                "artifact": "C:\\AI\\reports\\operations\\kis_provider_returned_to_handoff_copy_review_latest.json",
                                "required_before_refresh": True,
                            },
                            "after_return_command": "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120",
                        },
                        "prompt_to_artifact_completion_audit": {"complete": False},
                        "safety": wait_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = wait_mod.build_report(
                "2026-05-14T06:45:00+09:00",
                router_path=router,
                active_audit_path=audit,
                operator_brief_path=brief,
                send_status_path=send,
                return_receipt_path=receipt,
                stage6_wait_packet_path=stage6_wait,
            )

        self.assertEqual(report["status"], "BLOCKED_WAIT_STATE_INCONSISTENT")
        self.assertIn("operator_brief_matches_wait_state", report["blockers"])

    def test_wait_state_blocks_if_stage6_wait_packet_disagrees(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            router = root / "router.json"
            audit = root / "audit.json"
            brief = root / "brief.json"
            send = root / "send.json"
            receipt = root / "receipt.json"
            stage6_wait = root / "stage6_wait.json"
            wait = {"decision": "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS", "can_continue_local_work": False}
            router.write_text(json.dumps(router_payload(wait)), encoding="utf-8")
            brief.write_text(json.dumps({"autonomous_continuation": wait, "safety": wait_mod.SAFETY}), encoding="utf-8")
            audit.write_text(
                json.dumps(
                    {
                        "status": "NOT_COMPLETE_BLOCKED_BY_EXTERNAL_DISPATCH_AND_PROVIDER_ROWS",
                        "missing_or_blocked_check_ids": [
                            "dispatch_sent_confirmation_recorded",
                            "returned_provider_csvs_received",
                            "source_backed_rows_complete",
                            "tiny_live_preconditions_complete",
                        ],
                        "safety": wait_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            send.write_text(json.dumps({"send_confirmation_valid": False, "safety": wait_mod.SAFETY}), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS", "safety": wait_mod.SAFETY}), encoding="utf-8")
            stage6_wait.write_text(
                json.dumps(
                    {
                        "status": "STAGE6_REACHED",
                        "stage6_reached": True,
                        "blocked_by_operator_or_provider": False,
                        "dispatch_wait": {},
                        "prompt_to_artifact_completion_audit": {"complete": True},
                    }
                ),
                encoding="utf-8",
            )

            report = wait_mod.build_report(
                "2026-05-14T06:45:00+09:00",
                router_path=router,
                active_audit_path=audit,
                operator_brief_path=brief,
                send_status_path=send,
                return_receipt_path=receipt,
                stage6_wait_packet_path=stage6_wait,
            )

        self.assertEqual(report["status"], "BLOCKED_WAIT_STATE_INCONSISTENT")
        self.assertIn("stage6_wait_packet_matches_wait_state", report["blockers"])
        self.assertIn("stage6_wait_packet_has_safe_watch_commands", report["blockers"])

    def test_wait_state_allows_stage6_reached_when_still_blocked_by_external_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            router = root / "router.json"
            audit = root / "audit.json"
            brief = root / "brief.json"
            send = root / "send.json"
            receipt = root / "receipt.json"
            stage6_wait = root / "stage6_wait.json"
            wait = {"decision": "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS", "can_continue_local_work": False}
            router.write_text(json.dumps(router_payload(wait)), encoding="utf-8")
            brief.write_text(json.dumps({"autonomous_continuation": wait, "safety": wait_mod.SAFETY}), encoding="utf-8")
            audit.write_text(
                json.dumps(
                    {
                        "status": "NOT_COMPLETE_BLOCKED_BY_EXTERNAL_DISPATCH_AND_PROVIDER_ROWS",
                        "missing_or_blocked_check_ids": [
                            "dispatch_sent_confirmation_recorded",
                            "returned_provider_csvs_received",
                            "source_backed_rows_complete",
                            "tiny_live_preconditions_complete",
                        ],
                        "safety": wait_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            send.write_text(json.dumps({"send_confirmation_valid": False, "safety": wait_mod.SAFETY}), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS", "safety": wait_mod.SAFETY}), encoding="utf-8")
            stage6_wait.write_text(
                json.dumps(
                    {
                        "status": "STAGE6_REACHED",
                        "stage6_reached": True,
                        "blocked_by_operator_or_provider": True,
                        "dispatch_wait": {
                            "safe_watch_command_after_dispatch": "python .\\run_cand022_provider_return_watch.py",
                            "safe_watch_command_report_only": "python .\\run_cand022_provider_return_watch.py --no-refresh",
                            "copy_review_before_refresh_enforced": True,
                            "after_return_copy_review": {
                                "artifact": "C:\\AI\\reports\\operations\\kis_provider_returned_to_handoff_copy_review_latest.json",
                                "required_before_refresh": True,
                                "status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                            },
                            "after_return_command": "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120",
                        },
                        "prompt_to_artifact_completion_audit": {"complete": True},
                        "safety": wait_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = wait_mod.build_report(
                "2026-05-14T06:45:00+09:00",
                router_path=router,
                active_audit_path=audit,
                operator_brief_path=brief,
                send_status_path=send,
                return_receipt_path=receipt,
                stage6_wait_packet_path=stage6_wait,
            )

        self.assertEqual(report["status"], "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS")
        self.assertEqual(report["blockers"], [])
        self.assertTrue(report["stage6_wait_packet"]["stage6_reached"])

    def test_wait_state_blocks_if_stage6_wait_packet_safety_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            router = root / "router.json"
            audit = root / "audit.json"
            brief = root / "brief.json"
            send = root / "send.json"
            receipt = root / "receipt.json"
            stage6_wait = root / "stage6_wait.json"
            wait = {"decision": "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS", "can_continue_local_work": False}
            router.write_text(json.dumps(router_payload(wait)), encoding="utf-8")
            brief.write_text(json.dumps({"autonomous_continuation": wait, "safety": wait_mod.SAFETY}), encoding="utf-8")
            audit.write_text(
                json.dumps(
                    {
                        "status": "NOT_COMPLETE_BLOCKED_BY_EXTERNAL_DISPATCH_AND_PROVIDER_ROWS",
                        "missing_or_blocked_check_ids": [
                            "dispatch_sent_confirmation_recorded",
                            "returned_provider_csvs_received",
                            "source_backed_rows_complete",
                            "tiny_live_preconditions_complete",
                        ],
                        "safety": wait_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            send.write_text(json.dumps({"send_confirmation_valid": False, "safety": wait_mod.SAFETY}), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS", "safety": wait_mod.SAFETY}), encoding="utf-8")
            unsafe = dict(wait_mod.SAFETY)
            unsafe["broker_submit_allowed"] = True
            stage6_wait.write_text(
                json.dumps(
                    {
                        "status": "WAIT_OPERATOR_OR_PROVIDER_INPUT_TO_ADVANCE_STAGE6",
                        "stage6_reached": False,
                        "blocked_by_operator_or_provider": True,
                        "dispatch_wait": {
                            "safe_watch_command_after_dispatch": "python .\\run_cand022_provider_return_watch.py",
                            "safe_watch_command_report_only": "python .\\run_cand022_provider_return_watch.py --no-refresh",
                            "after_return_copy_review": {
                                "artifact": "C:\\AI\\reports\\operations\\kis_provider_returned_to_handoff_copy_review_latest.json",
                                "required_before_refresh": True,
                            },
                            "after_return_command": "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120",
                        },
                        "prompt_to_artifact_completion_audit": {"complete": False},
                        "safety": unsafe,
                    }
                ),
                encoding="utf-8",
            )

            report = wait_mod.build_report(
                "2026-05-14T06:45:00+09:00",
                router_path=router,
                active_audit_path=audit,
                operator_brief_path=brief,
                send_status_path=send,
                return_receipt_path=receipt,
                stage6_wait_packet_path=stage6_wait,
            )

        self.assertEqual(report["status"], "BLOCKED_WAIT_STATE_INCONSISTENT")
        self.assertIn("safety_preserved", report["blockers"])

    def test_wait_state_blocks_if_router_dispatch_action_safety_is_not_locked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            router = root / "router.json"
            audit = root / "audit.json"
            brief = root / "brief.json"
            send = root / "send.json"
            receipt = root / "receipt.json"
            stage6_wait = root / "stage6_wait.json"
            wait = {"decision": "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS", "can_continue_local_work": False}
            payload = router_payload(wait)
            payload["action_router"][0]["action_safety"] = {**wait_mod.SAFETY, "order_intent_created": True}
            router.write_text(json.dumps(payload), encoding="utf-8")
            brief.write_text(json.dumps({"autonomous_continuation": wait, "safety": wait_mod.SAFETY}), encoding="utf-8")
            audit.write_text(
                json.dumps(
                    {
                        "status": "NOT_COMPLETE_BLOCKED_BY_EXTERNAL_DISPATCH_AND_PROVIDER_ROWS",
                        "missing_or_blocked_check_ids": [
                            "dispatch_sent_confirmation_recorded",
                            "returned_provider_csvs_received",
                            "source_backed_rows_complete",
                            "tiny_live_preconditions_complete",
                        ],
                        "safety": wait_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            send.write_text(json.dumps({"send_confirmation_valid": False, "safety": wait_mod.SAFETY}), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS", "safety": wait_mod.SAFETY}), encoding="utf-8")
            stage6_wait.write_text(
                json.dumps(
                    {
                        "status": "WAIT_OPERATOR_OR_PROVIDER_INPUT_TO_ADVANCE_STAGE6",
                        "stage6_reached": False,
                        "blocked_by_operator_or_provider": True,
                        "dispatch_wait": {
                            "safe_watch_command_after_dispatch": "python .\\run_cand022_provider_return_watch.py",
                            "safe_watch_command_report_only": "python .\\run_cand022_provider_return_watch.py --no-refresh",
                            "copy_review_before_refresh_enforced": True,
                            "after_return_copy_review": {
                                "artifact": "C:\\AI\\reports\\operations\\kis_provider_returned_to_handoff_copy_review_latest.json",
                                "required_before_refresh": True,
                                "status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                            },
                            "after_return_command": "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120",
                        },
                        "prompt_to_artifact_completion_audit": {"complete": False},
                        "safety": wait_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = wait_mod.build_report(
                "2026-05-14T06:45:00+09:00",
                router_path=router,
                active_audit_path=audit,
                operator_brief_path=brief,
                send_status_path=send,
                return_receipt_path=receipt,
                stage6_wait_packet_path=stage6_wait,
            )

        self.assertEqual(report["status"], "BLOCKED_WAIT_STATE_INCONSISTENT")
        self.assertIn("router_dispatch_action_safety_locked", report["blockers"])


if __name__ == "__main__":
    unittest.main()
