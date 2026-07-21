from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\run_full_pipeline_safe_supervisor.py")
SPEC = importlib.util.spec_from_file_location("run_full_pipeline_safe_supervisor", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
supervisor = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = supervisor
SPEC.loader.exec_module(supervisor)


class FullPipelineSafeSupervisorTests(unittest.TestCase):
    def test_loop_specs_keep_live_execution_out_of_supervisor(self) -> None:
        specs = supervisor.loop_specs()

        self.assertGreaterEqual(len(specs), 7)
        command_text = " ".join(" ".join(supervisor.command_for(spec)) for spec in specs).lower()
        self.assertNotIn("private", command_text)
        self.assertNotIn("live-submit", command_text)
        self.assertNotIn("real", command_text)

    def test_stage6_shadow_signal_recorder_is_optional_diagnostic(self) -> None:
        specs = {spec.name: spec for spec in supervisor.loop_specs()}

        self.assertIn("shadow_observation_optional", specs)
        spec = specs["shadow_observation_optional"]
        self.assertEqual(spec.stage, "optional_diagnostic_shadow_review_no_submit")
        self.assertEqual(spec.script, "run_stage6_shadow_loop.py")
        self.assertEqual(spec.args, ("--cycles", "1", "--dry-run"))
        self.assertFalse(spec.required)

    def test_safety_preflight_blocks_live_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            disable = Path(tmp) / "DISABLE_ALL_TRADING"
            disable.write_text("disabled", encoding="utf-8")
            with (
                patch.object(supervisor, "read_json") as read_json,
                patch.object(supervisor, "GLOBAL_DISABLE", disable),
            ):
                read_json.side_effect = [
                    {"live_enabled": True, "paper_enabled": False},
                    {"broker_submit_allowed": True, "broker_submit_scope": "paper_only", "live_enabled": False},
                ]

                preflight = supervisor.safety_preflight()

        self.assertEqual(preflight["status"], "BLOCKED")
        self.assertIn("KILL_SWITCH_LIVE_ENABLED", preflight["blockers"])

    def test_safety_preflight_allows_paper_only_broker_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            disable = Path(tmp) / "DISABLE_ALL_TRADING"
            disable.write_text("disabled", encoding="utf-8")
            with (
                patch.object(supervisor, "read_json") as read_json,
                patch.object(supervisor, "GLOBAL_DISABLE", disable),
            ):
                read_json.side_effect = [
                    {"live_enabled": False, "paper_enabled": False, "shadow_enabled": True},
                    {
                        "policy_mode": "paper_only",
                        "broker_submit_allowed": True,
                        "broker_submit_scope": "paper_only",
                        "live_enabled": False,
                        "private_submit_used": False,
                        "real_orders_allowed": False,
                    },
                ]

                preflight = supervisor.safety_preflight()

        self.assertEqual(preflight["status"], "PASS")
        self.assertFalse(preflight["does_enable_live"])

    def test_research_loops_are_marked_as_guarded(self) -> None:
        guarded = [spec.name for spec in supervisor.loop_specs() if spec.blocked_by_research_disable]

        self.assertIn("research_lane_refresh", guarded)
        self.assertIn("crypto_recursive_improvement", guarded)

    def test_cand022_provider_watch_continuity_is_reported_safely(self) -> None:
        with patch.object(
            supervisor,
            "read_json",
            return_value={
                "status": "WATCHER_CONTINUITY_OK",
                "needs_new_watcher": False,
                "existing_watch_running": True,
                "existing_watcher_process_ids": [123, 456],
                "max_remaining_minutes": 240.0,
                "provider_return_watch_status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
                "provider_return_watch_blockers": ["dispatch_sent_confirmation_missing_or_invalid"],
                "safety": {
                    "paper_enabled": False,
                    "live_enabled": False,
                    "broker_submit_allowed": False,
                    "private_submit_used": False,
                    "real_orders": 0,
                    "order_intent_created": False,
                    "pretrade_firewall_default_decision": "BLOCK",
                },
            },
        ):
            report = supervisor.cand022_provider_watch_continuity()

        self.assertEqual(report["status"], "WATCHER_CONTINUITY_OK")
        self.assertTrue(report["existing_watch_running"])
        self.assertEqual(report["existing_watcher_process_ids"], [123, 456])
        self.assertFalse(report["safety"]["live_enabled"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_stage6_operating_status_is_reported_safely(self) -> None:
        with patch.object(
            supervisor,
            "read_json",
            return_value={
                "status": "STAGE6_RUNNING_CAND022_NOT_COMPLETE",
                "stage6_contract_name": "Shadow Operation",
                "broader_stage6_operation": {
                    "running": True,
                    "shadow_queue_candidates": ["CAND-001"],
                    "cycles_completed": 3,
                    "cycles_requested": 288,
                },
                "cand022_stage6": {
                    "stage6_reached": False,
                    "completion_decision": "NOT_COMPLETE",
                    "completion_percent": 90.5,
                    "missing_or_blocked": ["dispatch_sent_confirmation_recorded"],
                },
                "safety": {
                    "paper_enabled": False,
                    "live_enabled": False,
                    "broker_submit_allowed": False,
                    "private_submit_used": False,
                    "real_orders": 0,
                    "order_intent_created": False,
                    "pretrade_firewall_default_decision": "BLOCK",
                },
            },
        ):
            report = supervisor.stage6_operating_status()

        self.assertEqual(report["status"], "STAGE6_RUNNING_CAND022_NOT_COMPLETE")
        self.assertTrue(report["broader_stage6_running"])
        self.assertEqual(report["broader_stage6_candidates"], ["CAND-001"])
        self.assertFalse(report["cand022_stage6_reached"])
        self.assertEqual(report["cand022_completion_percent"], 90.5)
        self.assertFalse(report["safety"]["paper_enabled"])
        self.assertFalse(report["safety"]["live_enabled"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_process_rows_filters_own_discovery_command(self) -> None:
        fake = [
            {
                "ProcessId": 1,
                "CommandLine": "powershell Get-CimInstance Win32_Process '*C:\\AI\\run_dual_repo_overnight_research.py*'",
            },
            {
                "ProcessId": 2,
                "CommandLine": "python C:\\AI\\run_gatekeeper_refresh_loop.py --cycles 1",
            },
            {
                "ProcessId": 3,
                "CommandLine": "python .\\run_cand022_provider_return_watch.py --cycles 240",
            },
        ]
        with patch("subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = __import__("json").dumps(fake)

            rows = supervisor.process_rows()

        self.assertEqual(len(rows), 2)
        self.assertIn("run_gatekeeper_refresh_loop.py", rows[0]["CommandLine"])
        self.assertIn("run_cand022_provider_return_watch.py", rows[1]["CommandLine"])

    def test_shadow_observation_known_blocker_prevents_restart_spam(self) -> None:
        spec = [item for item in supervisor.loop_specs() if item.name == "shadow_observation_optional"][0]
        with patch.object(
            supervisor,
            "read_json",
            return_value={
                "last_cycle": {
                    "observation": {"blockers": ["OOS_PARAMETERS_NOT_FOUND_FOR_REGISTERED_CANDIDATE"]}
                }
            },
        ):
            reason = supervisor.known_loop_blocker(spec)

        self.assertEqual(reason, "blocked_by_OOS_PARAMETERS_NOT_FOUND_FOR_REGISTERED_CANDIDATE")

    def test_stage_specs_cover_zero_to_thirteen_without_submit_loop(self) -> None:
        specs = supervisor.stage_specs()

        self.assertEqual([row["id"] for row in specs], list(range(14)))
        stage8_plus = [row for row in specs if row["id"] >= 8]
        self.assertTrue(stage8_plus)
        for row in stage8_plus:
            loop_text = str(row["loop"]).lower()
            self.assertTrue(
                "blocked" in loop_text
                or "readiness" in loop_text
                or "audit" in loop_text
                or "report" in loop_text
                or "dry-run" in loop_text
            )
            self.assertNotIn("submit_order", loop_text)

    def test_stage_status_board_blocks_execution_ladder_by_default(self) -> None:
        fake_stage13 = {
            "completion_decision": "NOT_COMPLETE",
            "stage13_complete": False,
            "blocked_by_external_input": True,
            "failed_required_stage_ids": ["stage8", "stage9", "stage10", "stage11", "stage12", "stage13"],
            "prompt_to_artifact_checklist": [
                {"stage_id": "stage8", "passed": False, "missing_or_blocked": ["paper_or_broker_paper_not_approved"]},
                {"stage_id": "stage9", "passed": False, "missing_or_blocked": ["pretrade_firewall_not_passed"]},
            ],
        }
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(supervisor, "STAGE_STATUS_JSON", Path(tmp) / "status.json"),
            patch.object(supervisor, "STAGE_STATUS_MD", Path(tmp) / "status.md"),
            patch.object(supervisor, "process_rows", return_value=[]),
            patch.object(supervisor, "read_json", side_effect=[fake_stage13, {}]),
        ):
            board = supervisor.build_stage_status_board([])

        stage_by_id = {row["id"]: row for row in board["stages"]}
        self.assertEqual(stage_by_id[6]["autonomous_action"], "OPTIONAL_DIAGNOSTIC_ONLY_NOT_REQUIRED")
        self.assertEqual(stage_by_id[7]["autonomous_action"], "OPTIONAL_DIAGNOSTIC_ONLY_NOT_REQUIRED")
        self.assertEqual(stage_by_id[8]["autonomous_action"], "BLOCK_OR_REPORT_ONLY_UNLESS_EXACT_LIVE_APPROVAL_AND_FIREWALL_PASS")
        self.assertEqual(stage_by_id[9]["autonomous_action"], "BLOCK_OR_REPORT_ONLY_UNLESS_EXACT_LIVE_APPROVAL_AND_FIREWALL_PASS")
        self.assertEqual(stage_by_id[10]["autonomous_action"], "BLOCK_OR_REPORT_ONLY_UNLESS_EXACT_LIVE_APPROVAL_AND_FIREWALL_PASS")
        self.assertFalse(board["safety_policy"]["does_create_order_intent"])
        self.assertFalse(board["safety_policy"]["does_enable_live"])

    def test_run_once_safe_actions_does_not_include_submit_commands(self) -> None:
        with (
            patch.object(supervisor, "run_safe_command") as run_safe,
            patch.object(supervisor, "shadow_queue_candidate_ids", return_value=["CAND-022"]),
        ):
            run_safe.side_effect = lambda name, command, timeout_seconds=180: {
                "name": name,
                "command": command,
                "status": "PASS",
                "returncode": 0,
            }

            results = supervisor.run_once_safe_actions()

        command_text = " ".join(" ".join(map(str, row["command"])) for row in results).lower()
        self.assertIn("build_stage13_completion_audit.py", command_text)
        self.assertIn("build_pipeline_direct_next_command.py", command_text)
        self.assertNotIn("run_stage6_shadow_loop.py", command_text)
        self.assertNotIn("run_stage7_local_sim_from_shadow.py", command_text)
        self.assertNotIn("submit_order", command_text)
        self.assertNotIn("build_tiny_live_order_intent.py", command_text)
        self.assertNotIn("broker_gateway", command_text)


if __name__ == "__main__":
    unittest.main()
