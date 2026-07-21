from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_stage6_entry_path_audit.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_stage6_entry_path_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_mod)


class Cand022Stage6EntryPathAuditTests(unittest.TestCase):
    def test_audit_reports_ready_wait_operator_without_marking_stage6_reached(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage6 = root / "stage6.json"
            plan = root / "plan.json"
            brief = root / "brief.json"
            router = root / "router.json"
            preflight = root / "preflight.json"
            slip = root / "slip.json"
            stack = root / "stack.json"
            acceptance = root / "acceptance.json"
            queue = root / "shadow_queue.jsonl"
            stage6.write_text(
                json.dumps(
                    {
                        "readiness_decision": "BLOCK",
                        "shadow_queue_allowed": False,
                        "shadow_passed": False,
                        "shadow_only_exception_acceptance": {"active": False},
                        "blockers": ["human_mandate_incomplete"],
                        "safety": audit_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            plan.write_text(
                json.dumps(
                    {
                        "guarded_shadow_exception_apply_support": {
                            "apply_script_present": True,
                            "dry_run_supported": True,
                        }
                    }
                ),
                encoding="utf-8",
            )
            brief.write_text(
                json.dumps(
                    {
                        "manual_dispatch_execution_slip": {
                            "helper_command": "python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send"
                        }
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
                                "post_confirmation_watch_command": "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            preflight.write_text(
                json.dumps(
                    {
                        "status": "WAIT_EXPLICIT_SHADOW_ONLY_EXCEPTION_INSTRUCTION",
                        "blocked_checks": ["operator_instruction_exact_match"],
                        "required_exact_instruction": "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY",
                        "guarded_apply_commands": {
                            "dry_run": "python .\\apply_cand022_shadow_only_exception.py --dry-run",
                            "apply": "python .\\apply_cand022_shadow_only_exception.py",
                        },
                        "post_apply_verification_commands": [
                            "python .\\build_cand022_stage6_shadow_readiness_packet.py",
                            "python .\\run_stage6_shadow_loop.py --cycles 1 --dry-run",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            slip.write_text(json.dumps({"status": "READY_MANUAL_DISPATCH_EXECUTION_SLIP"}), encoding="utf-8")
            stack.write_text(
                json.dumps({"status": "PASS_REFRESH_STACK_COMPLETED", "failed_scripts": [], "safety": audit_mod.SAFETY}),
                encoding="utf-8",
            )
            queue.write_text(json.dumps({"candidate_id": "CAND-001"}) + "\n", encoding="utf-8")

            report = audit_mod.build_audit(
                "2026-05-14T09:40:00+09:00",
                stage6_path=stage6,
                plan_path=plan,
                operator_brief_path=brief,
                router_path=router,
                preflight_path=preflight,
                dispatch_slip_path=slip,
                refresh_stack_path=stack,
                acceptance_path=acceptance,
                queue_path=queue,
            )

        self.assertFalse(report["stage6_reached"])
        self.assertEqual(report["entry_path_status"], "READY_WAIT_OPERATOR_OR_PROVIDER_INPUT")
        self.assertEqual(report["provider_dispatch_path"]["status"], "READY_WAIT_ACTUAL_SEND_AND_RETURNED_ROWS")
        self.assertIn("run_cand022_provider_return_watch.py", report["provider_dispatch_path"]["after_send_watch_command"])
        self.assertEqual(report["shadow_only_exception_path"]["status"], "READY_WAIT_EXACT_OPERATOR_INSTRUCTION")
        self.assertTrue(report["shadow_only_exception_path"]["checks"]["operator_instruction_only_blocker"])
        self.assertIn("does_not_mark_stage6_reached", report["non_goals"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_audit_blocks_when_refresh_stack_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage6 = root / "stage6.json"
            plan = root / "plan.json"
            brief = root / "brief.json"
            router = root / "router.json"
            preflight = root / "preflight.json"
            slip = root / "slip.json"
            stack = root / "stack.json"
            acceptance = root / "acceptance.json"
            queue = root / "shadow_queue.jsonl"
            stage6.write_text(json.dumps({"readiness_decision": "BLOCK", "shadow_queue_allowed": False, "shadow_passed": False, "shadow_only_exception_acceptance": {"active": False}, "safety": audit_mod.SAFETY}), encoding="utf-8")
            plan.write_text(json.dumps({"guarded_shadow_exception_apply_support": {"apply_script_present": True, "dry_run_supported": True}}), encoding="utf-8")
            brief.write_text(json.dumps({}), encoding="utf-8")
            router.write_text(json.dumps({"recommended_next_action_id": "send_external_provider_dispatch_packet"}), encoding="utf-8")
            preflight.write_text(json.dumps({"status": "WAIT_EXPLICIT_SHADOW_ONLY_EXCEPTION_INSTRUCTION", "blocked_checks": ["operator_instruction_exact_match"], "post_apply_verification_commands": ["x"]}), encoding="utf-8")
            slip.write_text(json.dumps({"status": "READY_MANUAL_DISPATCH_EXECUTION_SLIP"}), encoding="utf-8")
            stack.write_text(json.dumps({"status": "BLOCK_REFRESH_STACK_FAILED", "failed_scripts": ["x.py"], "safety": audit_mod.SAFETY}), encoding="utf-8")
            queue.write_text("", encoding="utf-8")

            report = audit_mod.build_audit(
                "2026-05-14T09:40:00+09:00",
                stage6_path=stage6,
                plan_path=plan,
                operator_brief_path=brief,
                router_path=router,
                preflight_path=preflight,
                dispatch_slip_path=slip,
                refresh_stack_path=stack,
                acceptance_path=acceptance,
                queue_path=queue,
            )

        self.assertEqual(report["entry_path_status"], "BLOCK_ENTRY_PATH_NOT_READY")
        self.assertEqual(report["provider_dispatch_path"]["status"], "BLOCK_PROVIDER_PATH")

    def test_audit_does_not_block_provider_path_for_downstream_refresh_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage6 = root / "stage6.json"
            plan = root / "plan.json"
            brief = root / "brief.json"
            router = root / "router.json"
            preflight = root / "preflight.json"
            slip = root / "slip.json"
            stack = root / "stack.json"
            acceptance = root / "acceptance.json"
            queue = root / "shadow_queue.jsonl"
            stage6.write_text(json.dumps({"readiness_decision": "BLOCK", "shadow_queue_allowed": False, "shadow_passed": False, "shadow_only_exception_acceptance": {"active": False}, "safety": audit_mod.SAFETY}), encoding="utf-8")
            plan.write_text(json.dumps({"guarded_shadow_exception_apply_support": {"apply_script_present": True, "dry_run_supported": True}}), encoding="utf-8")
            brief.write_text(json.dumps({}), encoding="utf-8")
            router.write_text(
                json.dumps(
                    {
                        "recommended_next_action_id": "send_external_provider_dispatch_packet",
                        "action_router": [{"action_id": "send_external_provider_dispatch_packet"}],
                    }
                ),
                encoding="utf-8",
            )
            preflight.write_text(json.dumps({"status": "WAIT_EXPLICIT_SHADOW_ONLY_EXCEPTION_INSTRUCTION", "blocked_checks": ["operator_instruction_exact_match"], "post_apply_verification_commands": ["x"]}), encoding="utf-8")
            slip.write_text(json.dumps({"status": "READY_MANUAL_DISPATCH_EXECUTION_SLIP"}), encoding="utf-8")
            stack.write_text(json.dumps({"status": "BLOCK_REFRESH_STACK_FAILED", "failed_scripts": ["build_cand022_blocked_wait_state.py"], "safety": audit_mod.SAFETY}), encoding="utf-8")
            queue.write_text("", encoding="utf-8")

            report = audit_mod.build_audit(
                "2026-05-14T09:40:00+09:00",
                stage6_path=stage6,
                plan_path=plan,
                operator_brief_path=brief,
                router_path=router,
                preflight_path=preflight,
                dispatch_slip_path=slip,
                refresh_stack_path=stack,
                acceptance_path=acceptance,
                queue_path=queue,
            )

        self.assertEqual(report["entry_path_status"], "READY_WAIT_OPERATOR_OR_PROVIDER_INPUT")
        self.assertEqual(report["provider_dispatch_path"]["status"], "READY_WAIT_ACTUAL_SEND_AND_RETURNED_ROWS")
        self.assertEqual(
            report["provider_dispatch_path"]["refresh_stack_failed_scripts"],
            ["build_cand022_blocked_wait_state.py"],
        )


if __name__ == "__main__":
    unittest.main()
