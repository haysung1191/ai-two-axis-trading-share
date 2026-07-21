from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_pipeline_blocked_runtime_safety_snapshot.py")
SPEC = importlib.util.spec_from_file_location("build_pipeline_blocked_runtime_safety_snapshot", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)


class PipelineBlockedRuntimeSafetySnapshotTests(unittest.TestCase):
    def test_ready_dual_repo_task_is_ok_when_disable_guard_exists(self) -> None:
        report = snapshot.build_report(
            [],
            [
                {"TaskName": "CodexDualRepoResearchLoop", "State": "Ready"},
                {"TaskName": "MomentumSplitModelsInitialEntryAutoTrade", "State": "Disabled"},
            ],
            {"paper_enabled": False, "live_enabled": False},
            True,
            {
                "paper_enabled": False,
                "live_enabled": False,
                "broker_submit_allowed": False,
                "private_submit_used": False,
                "real_orders": 0,
                "order_intent_created": False,
                "pretrade_firewall_default_decision": "BLOCK",
            },
        )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["blockers"], [])

    def test_blocks_ready_dual_repo_task_without_guard_or_live_enabled(self) -> None:
        report = snapshot.build_report(
            [],
            [{"TaskName": "CodexDualRepoResearchLoop", "State": "Ready"}],
            {"paper_enabled": False, "live_enabled": True},
            False,
            {
                "paper_enabled": False,
                "live_enabled": False,
                "broker_submit_allowed": False,
                "private_submit_used": False,
                "real_orders": 0,
                "order_intent_created": False,
                "pretrade_firewall_default_decision": "BLOCK",
            },
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("dual_repo_task_ready_without_disable_guard", report["blockers"])
        self.assertIn("live_enabled_not_false", report["blockers"])

    def test_running_python_process_is_warning_not_order_blocker(self) -> None:
        report = snapshot.build_report(
            [{"ProcessId": 123, "CommandLine": "python C:\\AI\\safe.py"}],
            [],
            {"paper_enabled": False, "live_enabled": False},
            True,
            {
                "paper_enabled": False,
                "live_enabled": False,
                "broker_submit_allowed": False,
                "private_submit_used": False,
                "real_orders": 0,
                "order_intent_created": False,
                "pretrade_firewall_default_decision": "BLOCK",
            },
        )

        self.assertEqual(report["status"], "PASS")
        self.assertIn("c_ai_python_processes_running", report["warnings"])

    def test_blocks_direct_safety_order_intent_or_broker_submit(self) -> None:
        report = snapshot.build_report(
            [],
            [],
            {"paper_enabled": False, "live_enabled": False},
            True,
            {
                "paper_enabled": False,
                "live_enabled": False,
                "broker_submit_allowed": True,
                "private_submit_used": False,
                "real_orders": 0,
                "order_intent_created": True,
                "pretrade_firewall_default_decision": "BLOCK",
            },
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("direct_safety_broker_submit_allowed_not_False", report["blockers"])
        self.assertIn("direct_safety_order_intent_created_not_False", report["blockers"])

    def test_allows_limited_live_preflight_state_only_with_global_disable(self) -> None:
        report = snapshot.build_report(
            [],
            [],
            {"paper_enabled": False, "live_enabled": False},
            True,
            {
                "paper_enabled": False,
                "live_enabled": True,
                "broker_submit_allowed": True,
                "private_submit_used": False,
                "real_orders": 0,
                "order_intent_created": True,
                "pretrade_firewall_default_decision": "ALLOW_LIMITED_LIVE",
            },
            direct_status="TINY_LIVE_PREFLIGHT_PASSED_BROKER_SUBMIT_BLOCKED_BY_GLOBAL_DISABLE",
            global_disable_all_trading_exists=True,
        )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["blockers"], [])
        self.assertTrue(report["global_disable_all_trading_exists"])


if __name__ == "__main__":
    unittest.main()
