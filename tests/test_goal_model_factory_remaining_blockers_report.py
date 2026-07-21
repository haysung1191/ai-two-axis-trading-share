from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_goal_model_factory_remaining_blockers_report.py")
SPEC = importlib.util.spec_from_file_location("build_goal_model_factory_remaining_blockers_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
remaining = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(remaining)


class GoalModelFactoryRemainingBlockersReportTests(unittest.TestCase):
    def test_report_maps_kis_and_paper_blockers_without_order_paths(self) -> None:
        report = remaining.build_report(
            audit={
                "status": "NOT_COMPLETE",
                "completion_allowed": False,
                "missing_or_incomplete": [
                    {"requirement": "Prompt-to-artifact deliverable: two_axis_model_factory_scope"},
                    {"requirement": "Prompt-to-artifact deliverable: current_paper_activation_gate"},
                ],
            },
            checklist={"status": "NOT_COMPLETE"},
            paper={
                "decision": "KEEP_PAPER_COLLECT_EVIDENCE",
                "evidence_gaps": ["INSUFFICIENT_PAPER_CYCLES"],
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
                        "combined_non_flat_signal_count": 53,
                        "combined_executable_order_evidence_count": 53,
                    },
                    "paper_safety": {
                        "broker_submit_allowed": True,
                        "broker_submit_scope": "paper_only",
                        "live_enabled_flag": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                    },
                },
            },
            progress_delta={
                "current": {"observed_at_utc": "2026-05-03T14:13:13+00:00"},
                "delta_from_previous": {"paper_cycles_delta": 0},
                "pace_summary": {"eta_status": "ETA_AVAILABLE", "estimated_hours_to_cycle_target": 3.4},
            },
            paper_loop={
                "generated_at_utc": "2026-05-03T12:57:51+00:00",
                "cycles_completed": 252,
                "cycles_requested": 1,
                "last_status": "ok",
                "activate": False,
            },
            kis_handoff={
                "status": "WAITING_FOR_OPERATOR_ENV_VALUES",
                "missing_requirements": ["app_key", "app_secret"],
                "verification_commands_after_operator_sets_values": [
                    "python .\\build_kis_environment_readiness_report.py"
                ],
                "safety": {
                    "secret_values_inspected": False,
                    "secret_values_written": False,
                    "does_set_environment": False,
                    "does_call_kis_api": False,
                },
            },
            risk_guard={"status": "PASS", "halt_count": 0},
            operational={"status": "WARN", "blockers": [], "actionable_warnings": []},
            gatekeeper_phrase_packet={
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "ready_phrase_count": 1,
                "blocked_decision_count": 0,
                "next_phrase": {
                    "decision_id": "paper_smoke_review",
                    "candidate_id": "small_account_growth_paper",
                    "exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                    "review_only_effect": (
                        "Records evidence review only. It does not approve promotion, shadow registration, "
                        "paper/live, broker submit, private submit, or real orders."
                    ),
                },
                "board_permissions": {
                    "promotion_allowed_by_this_packet": False,
                    "shadow_registration_allowed_by_this_packet": False,
                    "paper_enabled_by_this_packet": False,
                    "live_allowed_by_this_packet": False,
                    "broker_submit_allowed_by_this_packet": False,
                    "private_submit_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                },
            },
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["blocker_count"], 2)
        self.assertEqual(report["codex_unblockable_now_count"], 0)
        self.assertEqual(report["approval_required_count"], 1)
        self.assertEqual(report["operator_input_blocker_count"], 2)
        plan = {item["deliverable"]: item for item in report["blocker_resolution_plan"]}
        self.assertFalse(plan["two_axis_model_factory_scope"]["codex_can_unblock_without_operator"])
        self.assertFalse(plan["two_axis_model_factory_scope"]["approval_required_before_codex_action"])
        self.assertFalse(plan["current_paper_activation_gate"]["codex_can_unblock_without_operator"])
        self.assertTrue(plan["current_paper_activation_gate"]["approval_required_before_codex_action"])
        self.assertEqual(
            plan["current_paper_activation_gate"]["required_approval_phrase"],
            "PAPER APPROVE small_account_growth_paper",
        )
        self.assertEqual(report["recheck_readiness"]["status"], "WAITING_FOR_BLOCKER_CLEARANCE")
        self.assertFalse(report["recheck_readiness"]["kis_recheck_ready"])
        self.assertFalse(report["recheck_readiness"]["paper_recheck_ready"])
        self.assertEqual(report["recheck_readiness"]["ready_recheck_lanes"], [])
        self.assertEqual(
            report["recheck_readiness"]["blocked_recheck_reasons"]["two_axis_model_factory_scope"],
            ["KIS_ENV_VALUES_STILL_MISSING"],
        )
        self.assertEqual(
            report["recheck_readiness"]["blocked_recheck_reasons"]["current_paper_activation_gate"],
            ["PAPER_CYCLES_BELOW_TARGET"],
        )
        blockers = {item["deliverable"]: item for item in report["blockers"]}
        self.assertEqual(blockers["two_axis_model_factory_scope"]["blocker_type"], "external_operator_input")
        self.assertFalse(blockers["two_axis_model_factory_scope"]["codex_can_unblock_without_operator"])
        self.assertFalse(blockers["two_axis_model_factory_scope"]["approval_required_before_codex_action"])
        self.assertEqual(blockers["current_paper_activation_gate"]["blocker_type"], "paper_cycle_evidence")
        self.assertFalse(blockers["current_paper_activation_gate"]["codex_can_unblock_without_operator"])
        self.assertTrue(blockers["current_paper_activation_gate"]["approval_required_before_codex_action"])
        self.assertEqual(
            blockers["current_paper_activation_gate"]["required_approval_phrase"],
            "PAPER APPROVE small_account_growth_paper",
        )
        self.assertIn("Set-Location -LiteralPath C:\\AI", blockers["current_paper_activation_gate"]["verification_commands"])
        self.assertIn(
            "powershell -ExecutionPolicy Bypass -File C:\\AI\\run_goal_model_factory_unblock_recheck.ps1 -Execute",
            blockers["current_paper_activation_gate"]["verification_commands"],
        )
        self.assertEqual(
            plan["current_paper_activation_gate"]["verification_commands"],
            blockers["current_paper_activation_gate"]["verification_commands"],
        )
        self.assertEqual(blockers["current_paper_activation_gate"]["paper_cycles_missing"], 36)
        self.assertEqual(
            blockers["current_paper_activation_gate"]["paper_cycle_source"]["cycle_source"],
            "paper_autotrade_loop_latest.cycles_completed",
        )
        self.assertEqual(
            blockers["current_paper_activation_gate"]["paper_cycle_source"]["paper_loop_cycles_completed"],
            252,
        )
        self.assertTrue(
            blockers["current_paper_activation_gate"]["paper_cycle_source"][
                "gatekeeper_refresh_does_not_increment_this_counter"
            ]
        )
        self.assertTrue(
            blockers["current_paper_activation_gate"]["paper_cycle_source"][
                "requires_explicit_paper_activation_for_new_active_cycles"
            ]
        )
        self.assertIn("do not run paper activation cycles", blockers["current_paper_activation_gate"]["codex_safe_next_action"])
        self.assertFalse(
            blockers["current_paper_activation_gate"]["historical_replay_counts_as_promotion_evidence"]
        )
        self.assertTrue(blockers["current_paper_activation_gate"]["historical_replay_excluded"])
        self.assertEqual(report["gatekeeper_review"]["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertEqual(report["gatekeeper_review"]["next_exact_phrase_to_record"], "REVIEW_PAPER_SMOKE_ONLY")
        self.assertFalse(report["gatekeeper_review"]["promotion_allowed_by_this_packet"])
        self.assertFalse(report["gatekeeper_review"]["shadow_registration_allowed_by_this_packet"])
        self.assertFalse(report["gatekeeper_review"]["paper_enabled_by_this_packet"])
        self.assertFalse(report["gatekeeper_review"]["live_allowed_by_this_packet"])
        self.assertFalse(report["gatekeeper_review"]["broker_submit_allowed_by_this_packet"])
        self.assertFalse(report["gatekeeper_review"]["private_submit_allowed_by_this_packet"])
        self.assertFalse(report["gatekeeper_review"]["real_orders_allowed_by_this_packet"])
        self.assertFalse(report["safety"]["secret_values_included"])
        self.assertFalse(report["safety"]["secret_values_inspected"])
        self.assertFalse(report["safety"]["secret_values_written"])
        self.assertFalse(report["safety"]["does_set_environment"])
        self.assertFalse(report["safety"]["does_call_kis_api"])
        self.assertFalse(report["safety"]["does_enable_paper"])
        self.assertFalse(report["safety"]["does_enable_live"])
        self.assertFalse(report["safety"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["safety"]["real_orders_allowed_by_this_report"])
        self.assertTrue(report["safety"]["paper_broker_submit_allowed"])
        self.assertEqual(report["safety"]["paper_broker_submit_scope"], "paper_only")
        self.assertTrue(report["safety"]["paper_only_broker_scope_ok"])
        self.assertEqual(report["safety"]["paper_real_orders"], 0)

    def test_report_is_clear_when_audit_has_no_missing_requirements(self) -> None:
        report = remaining.build_report(
            audit={"status": "COMPLETE", "completion_allowed": True, "missing_or_incomplete": []},
            checklist={"status": "COMPLETE"},
            paper={},
            progress_delta={},
            paper_loop={},
            kis_handoff={},
            risk_guard={"status": "PASS", "halt_count": 0},
            operational={"status": "PASS", "blockers": [], "actionable_warnings": []},
            gatekeeper_phrase_packet={},
        )

        self.assertEqual(report["status"], "CLEAR")
        self.assertEqual(report["blocker_count"], 0)
        self.assertEqual(report["codex_unblockable_now_count"], 0)
        self.assertEqual(report["approval_required_count"], 0)
        self.assertEqual(report["operator_input_blocker_count"], 0)
        self.assertEqual(report["blocker_resolution_plan"], [])
        self.assertEqual(report["recheck_readiness"]["status"], "NO_BLOCKERS_REPORTED")
        self.assertTrue(report["recheck_readiness"]["completion_recheck_ready"])
        self.assertEqual(report["next_action"], "No remaining blockers found by this report.")

    def test_report_marks_recheck_lanes_ready_when_blocker_conditions_clear(self) -> None:
        report = remaining.build_report(
            audit={
                "status": "NOT_COMPLETE",
                "completion_allowed": False,
                "missing_or_incomplete": [
                    {"requirement": "Prompt-to-artifact deliverable: two_axis_model_factory_scope"},
                    {"requirement": "Prompt-to-artifact deliverable: current_paper_activation_gate"},
                ],
            },
            checklist={"status": "NOT_COMPLETE"},
            paper={
                "decision": "READY_FOR_PROMOTION_REVIEW",
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
                        "combined_non_flat_signal_count": 5,
                        "combined_executable_order_evidence_count": 5,
                    },
                    "paper_safety": {
                        "broker_submit_allowed": True,
                        "broker_submit_scope": "paper_only",
                        "live_enabled_flag": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                    },
                },
            },
            progress_delta={},
            paper_loop={"cycles_completed": 288, "last_status": "ok", "activate": True},
            kis_handoff={
                "status": "READY_FOR_OPERATOR_VERIFICATION",
                "missing_requirements": [],
                "safety": {
                    "secret_values_inspected": False,
                    "secret_values_written": False,
                    "does_set_environment": False,
                    "does_call_kis_api": False,
                },
            },
            risk_guard={"status": "PASS", "halt_count": 0},
            operational={"status": "PASS", "blockers": [], "actionable_warnings": []},
            gatekeeper_phrase_packet={},
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["approval_required_count"], 2)
        self.assertEqual(report["recheck_readiness"]["status"], "READY_FOR_BLOCKER_RECHECK")
        self.assertTrue(report["recheck_readiness"]["kis_recheck_ready"])
        self.assertTrue(report["recheck_readiness"]["paper_recheck_ready"])
        self.assertEqual(
            report["recheck_readiness"]["ready_recheck_lanes"],
            ["two_axis_model_factory_scope", "current_paper_activation_gate"],
        )
        self.assertEqual(report["recheck_readiness"]["blocked_recheck_reasons"]["two_axis_model_factory_scope"], [])
        self.assertEqual(report["recheck_readiness"]["blocked_recheck_reasons"]["current_paper_activation_gate"], [])

        blockers = {item["deliverable"]: item for item in report["blockers"]}
        self.assertEqual(blockers["two_axis_model_factory_scope"]["blocker_type"], "promotion_approval_pending")
        self.assertTrue(blockers["two_axis_model_factory_scope"]["approval_required_before_codex_action"])
        self.assertEqual(
            blockers["two_axis_model_factory_scope"]["required_approval_phrase"],
            "PAPER APPROVE small_account_growth_paper",
        )

    def test_paper_recheck_allows_risk_freshness_warn_when_hard_safety_passes(self) -> None:
        report = remaining.build_report(
            audit={
                "status": "NOT_COMPLETE",
                "completion_allowed": False,
                "missing_or_incomplete": [
                    {"requirement": "Prompt-to-artifact deliverable: current_paper_activation_gate"},
                ],
            },
            checklist={"status": "NOT_COMPLETE"},
            paper={
                "decision": "READY_FOR_PROMOTION_REVIEW",
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
            progress_delta={},
            paper_loop={"cycles_completed": 288, "last_status": "ok", "activate": True},
            kis_handoff={},
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
            operational={"status": "WARN", "blockers": [], "actionable_warnings": []},
            gatekeeper_phrase_packet={},
        )

        self.assertTrue(report["recheck_readiness"]["paper_recheck_ready"])
        self.assertEqual(
            report["recheck_readiness"]["blocked_recheck_reasons"]["current_paper_activation_gate"],
            [],
        )


if __name__ == "__main__":
    unittest.main()
