from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stage0_13_autonomous_loop_completion_audit.py")
SPEC = importlib.util.spec_from_file_location("build_stage0_13_autonomous_loop_completion_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


class Stage013AutonomousLoopCompletionAuditTests(unittest.TestCase):
    def test_running_safe_loop_completes_automation_goal_when_stage13_is_blocked(self) -> None:
        stages = [
            {
                "id": idx,
                "status": "BLOCKED" if idx >= 8 else "PASS",
                "autonomous_action": "BLOCK_OR_REPORT_ONLY_UNLESS_ALL_GATES_PASS" if idx >= 8 else "AUTO_RUN_ALLOWED",
                "blockers": ["blocked"] if idx >= 8 else [],
            }
            for idx in range(14)
        ]
        report = audit.build_report(
            "2026-05-15T00:00:00+09:00",
            stage_board={
                "completion_decision": "NOT_COMPLETE",
                "stages": stages,
                "safety_policy": {
                    "does_enable_paper": False,
                    "does_enable_live": False,
                    "does_enable_broker_submit": False,
                    "does_create_order_intent": False,
                },
                "safety": audit.SAFETY,
            },
            watchdog={
                "status": "running",
                "cycles_requested": "unbounded",
                "unbounded": True,
                "cycles_completed": 31,
                "run_once_safe_each_cycle": True,
                "last_run_once_safe_results": [{"name": "stage13_completion_audit", "status": "PASS"}],
                "safety": audit.SAFETY,
            },
            stage13={
                "completion_decision": "NOT_COMPLETE",
                "stage13_complete": False,
                "failed_required_stage_ids": ["stage8", "stage13"],
                "prompt_to_artifact_checklist": [{"stage_id": "stage13", "passed": False}],
                "safety": audit.SAFETY,
            },
            processes=[
                {"CommandLine": "python C:\\AI\\run_full_pipeline_safe_watchdog_loop.py --cycles 0 --run-once-safe-each-cycle"},
                {"CommandLine": "python C:\\AI\\run_gatekeeper_refresh_loop.py --cycles 1"},
                {"CommandLine": "python C:\\AI\\run_crypto_recursive_improvement_loop.py --cycles 96"},
            ],
        )

        self.assertEqual(report["completion_decision"], "COMPLETE")
        self.assertEqual(report["automation_completion_decision"], "COMPLETE")
        self.assertEqual(report["stage13_deployment_completion_decision"], "NOT_COMPLETE")
        self.assertEqual(report["automation_state"], "SAFE_UNATTENDED_LOOP_RUNNING")
        self.assertFalse(report["stage13_complete"])
        self.assertFalse(report["stage13_complete_required_for_automation_goal"])
        self.assertEqual(report["missing_or_blocked"], [])
        checklist = {row["requirement_id"]: row for row in report["prompt_to_artifact_checklist"]}
        self.assertTrue(checklist["watchdog_running_unattended"]["passed"])
        self.assertTrue(checklist["watchdog_unbounded"]["passed"])
        self.assertTrue(checklist["watchdog_singleton"]["passed"])
        self.assertTrue(checklist["execution_ladder_blocked_safely"]["passed"])
        self.assertTrue(checklist["safety_invariants_preserved"]["passed"])

    def test_missing_core_loop_is_reported(self) -> None:
        stages = [
            {
                "id": idx,
                "status": "BLOCKED" if idx >= 8 else "PASS",
                "autonomous_action": "BLOCK_OR_REPORT_ONLY_UNLESS_ALL_GATES_PASS" if idx >= 8 else "AUTO_RUN_ALLOWED",
            }
            for idx in range(14)
        ]

        report = audit.build_report(
            "2026-05-15T00:00:00+09:00",
            stage_board={"completion_decision": "NOT_COMPLETE", "stages": stages, "safety": audit.SAFETY},
            watchdog={
                "status": "running",
                "cycles_requested": "unbounded",
                "unbounded": True,
                "cycles_completed": 1,
                "run_once_safe_each_cycle": True,
                "last_run_once_safe_results": [{"name": "stage13_completion_audit", "status": "PASS"}],
                "safety": audit.SAFETY,
            },
            stage13={
                "completion_decision": "NOT_COMPLETE",
                "stage13_complete": False,
                "prompt_to_artifact_checklist": [],
                "safety": audit.SAFETY,
            },
            processes=[{"CommandLine": "python C:\\AI\\run_full_pipeline_safe_watchdog_loop.py --cycles 0"}],
        )

        checklist = {row["requirement_id"]: row for row in report["prompt_to_artifact_checklist"]}
        self.assertFalse(checklist["core_loops_running"]["passed"])
        self.assertIn("run_gatekeeper_refresh_loop.py", checklist["core_loops_running"]["missing_or_blocked"])
        self.assertIn("run_crypto_recursive_improvement_loop.py", report["missing_or_blocked"])

    def test_safety_drift_blocks_audit_pass(self) -> None:
        unsafe = dict(audit.SAFETY)
        unsafe["live_enabled"] = True
        stages = [
            {
                "id": idx,
                "status": "BLOCKED" if idx >= 8 else "PASS",
                "autonomous_action": "BLOCK_OR_REPORT_ONLY_UNLESS_ALL_GATES_PASS" if idx >= 8 else "AUTO_RUN_ALLOWED",
            }
            for idx in range(14)
        ]

        report = audit.build_report(
            "2026-05-15T00:00:00+09:00",
            stage_board={"completion_decision": "NOT_COMPLETE", "stages": stages, "safety": unsafe},
            watchdog={
                "status": "running",
                "cycles_requested": "unbounded",
                "unbounded": True,
                "cycles_completed": 1,
                "run_once_safe_each_cycle": True,
                "last_run_once_safe_results": [{"status": "PASS"}],
                "safety": audit.SAFETY,
            },
            stage13={"completion_decision": "NOT_COMPLETE", "stage13_complete": False, "prompt_to_artifact_checklist": [], "safety": audit.SAFETY},
            processes=[
                {"CommandLine": "python C:\\AI\\run_full_pipeline_safe_watchdog_loop.py --cycles 0"},
                {"CommandLine": "python C:\\AI\\run_gatekeeper_refresh_loop.py"},
                {"CommandLine": "python C:\\AI\\run_crypto_recursive_improvement_loop.py"},
            ],
        )

        checklist = {row["requirement_id"]: row for row in report["prompt_to_artifact_checklist"]}
        self.assertFalse(checklist["safety_invariants_preserved"]["passed"])
        self.assertIn("safety_invariants_preserved_not_satisfied", report["missing_or_blocked"])

    def test_finite_watchdog_fails_unbounded_requirement(self) -> None:
        stages = [
            {
                "id": idx,
                "status": "BLOCKED" if idx >= 8 else "PASS",
                "autonomous_action": "BLOCK_OR_REPORT_ONLY_UNLESS_ALL_GATES_PASS" if idx >= 8 else "AUTO_RUN_ALLOWED",
            }
            for idx in range(14)
        ]

        report = audit.build_report(
            "2026-05-15T00:00:00+09:00",
            stage_board={"completion_decision": "NOT_COMPLETE", "stages": stages, "safety": audit.SAFETY},
            watchdog={
                "status": "running",
                "cycles_requested": 288,
                "unbounded": False,
                "cycles_completed": 1,
                "run_once_safe_each_cycle": True,
                "last_run_once_safe_results": [{"status": "PASS"}],
                "safety": audit.SAFETY,
            },
            stage13={"completion_decision": "NOT_COMPLETE", "stage13_complete": False, "prompt_to_artifact_checklist": [], "safety": audit.SAFETY},
            processes=[
                {"CommandLine": "python C:\\AI\\run_full_pipeline_safe_watchdog_loop.py --cycles 288"},
                {"CommandLine": "python C:\\AI\\run_gatekeeper_refresh_loop.py"},
                {"CommandLine": "python C:\\AI\\run_crypto_recursive_improvement_loop.py"},
            ],
        )

        checklist = {row["requirement_id"]: row for row in report["prompt_to_artifact_checklist"]}
        self.assertFalse(checklist["watchdog_unbounded"]["passed"])
        self.assertIn("watchdog_unbounded_not_satisfied", report["missing_or_blocked"])

    def test_duplicate_watchdog_processes_fail_singleton_requirement(self) -> None:
        stages = [
            {
                "id": idx,
                "status": "BLOCKED" if idx >= 8 else "PASS",
                "autonomous_action": "BLOCK_OR_REPORT_ONLY_UNLESS_ALL_GATES_PASS" if idx >= 8 else "AUTO_RUN_ALLOWED",
            }
            for idx in range(14)
        ]

        report = audit.build_report(
            "2026-05-15T00:00:00+09:00",
            stage_board={"completion_decision": "NOT_COMPLETE", "stages": stages, "safety": audit.SAFETY},
            watchdog={
                "status": "running",
                "cycles_requested": "unbounded",
                "unbounded": True,
                "cycles_completed": 1,
                "run_once_safe_each_cycle": True,
                "last_run_once_safe_results": [{"status": "PASS"}],
                "safety": audit.SAFETY,
            },
            stage13={"completion_decision": "NOT_COMPLETE", "stage13_complete": False, "prompt_to_artifact_checklist": [], "safety": audit.SAFETY},
            processes=[
                {"CommandLine": "python C:\\AI\\run_full_pipeline_safe_watchdog_loop.py --cycles 0"},
                {"CommandLine": "python C:\\AI\\run_full_pipeline_safe_watchdog_loop.py --cycles 0"},
                {"CommandLine": "python C:\\AI\\run_gatekeeper_refresh_loop.py"},
                {"CommandLine": "python C:\\AI\\run_crypto_recursive_improvement_loop.py"},
            ],
        )

        checklist = {row["requirement_id"]: row for row in report["prompt_to_artifact_checklist"]}
        self.assertFalse(checklist["watchdog_singleton"]["passed"])
        self.assertIn("watchdog_singleton_not_satisfied", report["missing_or_blocked"])


if __name__ == "__main__":
    unittest.main()
