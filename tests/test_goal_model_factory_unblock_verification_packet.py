from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_goal_model_factory_unblock_verification_packet.py")
SPEC = importlib.util.spec_from_file_location("build_goal_model_factory_unblock_verification_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
packet_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_builder)


class GoalModelFactoryUnblockVerificationPacketTests(unittest.TestCase):
    def test_packet_maps_both_remaining_blockers_to_verification_steps(self) -> None:
        packet = packet_builder.build_packet(
            remaining_blockers={
                "blockers": [
                    {"deliverable": "two_axis_model_factory_scope"},
                    {
                        "deliverable": "current_paper_activation_gate",
                        "paper_cycle_source": {
                            "source": r"C:\AI\overnight_runs\paper_autotrade_loop_latest.json",
                            "cycle_source": "paper_autotrade_loop_latest.cycles_completed",
                            "paper_loop_cycles_completed": 252,
                            "paper_loop_last_status": "ok",
                            "paper_loop_activate": False,
                            "paper_loop_cycles_requested": 1,
                            "progress_delta_cycles": 0,
                            "gatekeeper_refresh_does_not_increment_this_counter": True,
                            "requires_explicit_paper_activation_for_new_active_cycles": True,
                        },
                    },
                ]
            },
            kis_handoff={
                "status": "WAITING_FOR_OPERATOR_ENV_VALUES",
                "missing_requirements": ["app_key", "app_secret"],
                "preferred_env_names": {"app_key": "KIS_APP_KEY", "app_secret": "KIS_APP_SECRET"},
                "verification_commands_after_operator_sets_values": [
                    "python .\\build_kis_environment_readiness_report.py"
                ],
                "safety": {
                    "secret_values_inspected": False,
                    "secret_values_written": False,
                },
            },
            kis_readiness={"status": "BLOCKED"},
            stock_preflight={"status": "BLOCKED", "blockers": ["KIS_ENV_MISSING"]},
            kis_universe={"kis_api_environment_ready": False},
            paper_promotion={
                "thresholds": {
                    "min_cycles_for_promotion_review": 288,
                    "min_non_flat_signals_for_promotion": 5,
                    "min_executable_orders_for_promotion": 5,
                },
                "replay_policy": {
                    "historical_replay_counts_as_promotion_evidence": False,
                    "historical_replay_excluded": True,
                },
                "evidence": {
                    "paper_cycles_completed": 252,
                    "evidence_deficit": {"paper_loop_cycles_missing": 36},
                    "combined_evidence": {
                        "combined_non_flat_signal_count": 54,
                        "combined_executable_order_evidence_count": 54,
                    },
                }
            },
            paper_velocity={
                "readiness_summary": {
                    "paper_evidence_readiness_percent": 87.5,
                    "promotion_review_ready": False,
                    "dominant_blocking_dimensions": ["paper_cycles"],
                }
            },
            risk_guard={"status": "PASS", "halt_count": 0},
        )

        self.assertEqual(packet["status"], "WAITING_FOR_BLOCKER_CLEARANCE")
        self.assertEqual(packet["blocker_count"], 2)
        self.assertEqual(
            packet["blocker_deliverables"],
            ["current_paper_activation_gate", "two_axis_model_factory_scope"],
        )
        self.assertEqual(packet["verification_steps"][0]["blocker"], "two_axis_model_factory_scope")
        self.assertTrue(packet["verification_steps"][0]["operator_input_required"])
        self.assertIn(
            "python .\\build_kis_environment_readiness_report.py",
            packet["verification_steps"][0]["commands"],
        )
        self.assertEqual(packet["verification_steps"][1]["blocker"], "current_paper_activation_gate")
        self.assertEqual(packet["unblock_summary"]["paper_cycles_completed"], 252)
        self.assertEqual(packet["unblock_summary"]["paper_cycles_missing"], 36)
        self.assertEqual(
            packet["unblock_summary"]["paper_cycle_source"]["source"],
            r"C:\AI\overnight_runs\paper_autotrade_loop_latest.json",
        )
        self.assertEqual(
            packet["unblock_summary"]["paper_cycle_source"]["cycle_source"],
            "paper_autotrade_loop_latest.cycles_completed",
        )
        self.assertEqual(packet["unblock_summary"]["paper_cycle_source"]["paper_loop_cycles_completed"], 252)
        self.assertEqual(packet["unblock_summary"]["paper_cycle_source"]["paper_loop_last_status"], "ok")
        self.assertFalse(packet["unblock_summary"]["paper_cycle_source"]["paper_loop_activate"])
        self.assertEqual(packet["unblock_summary"]["paper_cycle_source"]["paper_loop_cycles_requested"], 1)
        self.assertEqual(packet["unblock_summary"]["paper_cycle_source"]["progress_delta_cycles"], 0)
        self.assertTrue(
            packet["unblock_summary"]["paper_cycle_source"]["gatekeeper_refresh_does_not_increment_this_counter"]
        )
        self.assertTrue(
            packet["unblock_summary"]["paper_cycle_source"][
                "requires_explicit_paper_activation_for_new_active_cycles"
            ]
        )
        self.assertEqual(packet["unblock_summary"]["non_flat_signal_count"], 54)
        self.assertTrue(packet["unblock_summary"]["non_flat_signals_ready"])
        self.assertEqual(packet["unblock_summary"]["executable_order_count"], 54)
        self.assertTrue(packet["unblock_summary"]["executable_orders_ready"])
        self.assertFalse(packet["unblock_summary"]["historical_replay_counts_as_promotion_evidence"])
        self.assertTrue(packet["unblock_summary"]["historical_replay_excluded"])
        self.assertEqual(packet["recheck_readiness"]["status"], "WAITING_FOR_BLOCKER_CLEARANCE")
        self.assertFalse(packet["recheck_readiness"]["kis_recheck_ready"])
        self.assertFalse(packet["recheck_readiness"]["paper_recheck_ready"])
        self.assertEqual(packet["recheck_readiness"]["ready_recheck_lanes"], [])
        self.assertIn(
            "KIS_ENV_VALUES_STILL_MISSING",
            packet["recheck_readiness"]["blocked_recheck_reasons"]["two_axis_model_factory_scope"],
        )
        self.assertIn(
            "PAPER_CYCLES_BELOW_TARGET",
            packet["recheck_readiness"]["blocked_recheck_reasons"]["current_paper_activation_gate"],
        )
        self.assertEqual(
            packet["verification_steps"][0]["current_status"]["preferred_env_names"]["app_key"],
            "KIS_APP_KEY",
        )
        self.assertEqual(
            packet["verification_steps"][1]["expected_pass_conditions"]["paper_cycles_completed_min"],
            288,
        )
        self.assertIn("Set-Location -LiteralPath C:\\AI", packet["verification_steps"][1]["commands"])
        self.assertIn(
            "powershell -ExecutionPolicy Bypass -File C:\\AI\\run_goal_model_factory_unblock_recheck.ps1 -Execute",
            packet["verification_steps"][1]["commands"],
        )
        self.assertEqual(
            packet["verification_steps"][1]["current_status"]["paper_cycle_source"]["cycle_source"],
            "paper_autotrade_loop_latest.cycles_completed",
        )
        self.assertEqual(
            packet["verification_steps"][1]["current_status"]["paper_cycle_source"]["paper_loop_cycles_completed"],
            252,
        )
        self.assertTrue(
            packet["verification_steps"][1]["current_status"]["paper_cycle_source"][
                "gatekeeper_refresh_does_not_increment_this_counter"
            ]
        )
        self.assertTrue(
            packet["verification_steps"][1]["current_status"]["paper_cycle_source"][
                "requires_explicit_paper_activation_for_new_active_cycles"
            ]
        )
        self.assertFalse(
            packet["verification_steps"][1]["expected_pass_conditions"][
                "historical_replay_counts_as_promotion_evidence"
            ]
        )
        self.assertEqual(
            packet["recheck_runner"]["path"],
            r"C:\AI\run_goal_model_factory_unblock_recheck.ps1",
        )
        self.assertEqual(packet["recheck_runner"]["default_mode"], "PRINT_ONLY")
        self.assertIn("-Execute", packet["recheck_runner"]["execute_completion_recheck_command"])
        self.assertTrue(
            any("build_goal_model_factory_unblock_verification_packet.py" in command for command in packet["completion_recheck_commands"])
        )

    def test_packet_is_review_only_and_never_enables_order_paths(self) -> None:
        packet = packet_builder.build_packet(
            remaining_blockers={"blockers": []},
            kis_handoff={"safety": {"secret_values_inspected": False, "secret_values_written": False}},
            kis_readiness={},
            stock_preflight={},
            kis_universe={},
            paper_promotion={},
            paper_velocity={},
            risk_guard={"status": "PASS", "halt_count": 0},
        )

        self.assertEqual(packet["status"], "NO_BLOCKERS_REPORTED")
        self.assertFalse(packet["safety"]["secret_values_included"])
        self.assertFalse(packet["safety"]["secret_values_inspected"])
        self.assertFalse(packet["safety"]["secret_values_written"])
        self.assertFalse(packet["safety"]["does_set_environment"])
        self.assertFalse(packet["safety"]["does_call_kis_api"])
        self.assertFalse(packet["safety"]["does_enable_paper"])
        self.assertFalse(packet["safety"]["does_enable_live"])
        self.assertFalse(packet["safety"]["broker_submit_allowed_by_this_packet"])
        self.assertFalse(packet["safety"]["private_submit_allowed_by_this_packet"])
        self.assertFalse(packet["safety"]["real_orders_allowed_by_this_packet"])
        self.assertEqual(packet["safety"]["real_orders"], 0)
        self.assertTrue(packet["recheck_readiness"]["completion_recheck_ready"])

    def test_recheck_readiness_marks_lanes_ready_after_blocker_conditions_clear(self) -> None:
        packet = packet_builder.build_packet(
            remaining_blockers={
                "blockers": [
                    {"deliverable": "two_axis_model_factory_scope"},
                    {"deliverable": "current_paper_activation_gate"},
                ]
            },
            kis_handoff={
                "status": "WAITING_FOR_OPERATOR_ENV_VALUES",
                "missing_requirements": [],
                "safety": {
                    "secret_values_inspected": False,
                    "secret_values_written": False,
                },
            },
            kis_readiness={"status": "BLOCKED"},
            stock_preflight={"status": "BLOCKED", "blockers": ["KIS_ENV_MISSING"]},
            kis_universe={"kis_api_environment_ready": False},
            paper_promotion={
                "thresholds": {
                    "min_cycles_for_promotion_review": 288,
                    "min_non_flat_signals_for_promotion": 5,
                    "min_executable_orders_for_promotion": 5,
                },
                "replay_policy": {
                    "historical_replay_counts_as_promotion_evidence": False,
                    "historical_replay_excluded": True,
                },
                "evidence": {
                    "paper_cycles_completed": 288,
                    "evidence_deficit": {"paper_loop_cycles_missing": 0},
                    "combined_evidence": {
                        "combined_non_flat_signal_count": 54,
                        "combined_executable_order_evidence_count": 54,
                    },
                },
            },
            paper_velocity={
                "readiness_summary": {
                    "paper_evidence_readiness_percent": 100,
                    "promotion_review_ready": True,
                    "dominant_blocking_dimensions": [],
                }
            },
            risk_guard={"status": "PASS", "halt_count": 0},
        )

        self.assertEqual(packet["recheck_readiness"]["status"], "READY_FOR_BLOCKER_RECHECK")
        self.assertTrue(packet["recheck_readiness"]["kis_recheck_ready"])
        self.assertTrue(packet["recheck_readiness"]["paper_recheck_ready"])
        self.assertEqual(
            packet["recheck_readiness"]["ready_recheck_lanes"],
            ["two_axis_model_factory_scope", "current_paper_activation_gate"],
        )
        self.assertEqual(packet["recheck_readiness"]["blocked_recheck_reasons"]["two_axis_model_factory_scope"], [])
        self.assertEqual(packet["recheck_readiness"]["blocked_recheck_reasons"]["current_paper_activation_gate"], [])

    def test_paper_recheck_allows_risk_freshness_warn_when_hard_safety_passes(self) -> None:
        packet = packet_builder.build_packet(
            remaining_blockers={"blockers": [{"deliverable": "current_paper_activation_gate"}]},
            kis_handoff={},
            kis_readiness={},
            stock_preflight={},
            kis_universe={},
            paper_promotion={
                "thresholds": {
                    "min_cycles_for_promotion_review": 288,
                    "min_non_flat_signals_for_promotion": 5,
                    "min_executable_orders_for_promotion": 5,
                },
                "replay_policy": {
                    "historical_replay_counts_as_promotion_evidence": False,
                    "historical_replay_excluded": True,
                },
                "evidence": {
                    "paper_cycles_completed": 288,
                    "combined_evidence": {
                        "combined_non_flat_signal_count": 5,
                        "combined_executable_order_evidence_count": 5,
                    },
                },
            },
            paper_velocity={},
            risk_guard={
                "status": "WARN",
                "halt_count": 0,
                "checks": [
                    {"name": "live_disabled", "status": "PASS"},
                    {"name": "private_submit_unused", "status": "PASS"},
                    {"name": "real_orders_zero", "status": "PASS"},
                    {"name": "broker_submit_scope", "status": "PASS"},
                    {"name": "latest_run", "status": "WARN"},
                ],
            },
        )

        self.assertTrue(packet["recheck_readiness"]["paper_recheck_ready"])
        self.assertEqual(
            packet["recheck_readiness"]["blocked_recheck_reasons"]["current_paper_activation_gate"],
            [],
        )


if __name__ == "__main__":
    unittest.main()
