from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\refresh_paper_evidence_review_stack.py")
SPEC = importlib.util.spec_from_file_location("refresh_paper_evidence_review_stack", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
refresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(refresh)


class RefreshPaperEvidenceReviewStackTests(unittest.TestCase):
    def test_steps_include_ordered_review_stack_without_order_paths(self) -> None:
        self.assertIn("build_stock_risk_conversion_robustness_stress.py", refresh.STEPS)
        self.assertIn("build_stock_risk_conversion_sizing_repair_report.py", refresh.STEPS)
        self.assertNotIn("register_bithumb_current_actionable_shadow_candidate.py", refresh.STEPS)
        self.assertIn("build_bithumb_current_actionable_shadow_signal_adapter.py", refresh.STEPS)
        self.assertIn("build_bithumb_current_actionable_shadow_rollover_review_packet.py", refresh.STEPS)
        self.assertIn("build_bithumb_current_actionable_alternate_robustness_review.py", refresh.STEPS)
        self.assertIn("build_bithumb_current_actionable_family_diversity_review.py", refresh.STEPS)
        self.assertIn("build_bithumb_current_actionable_family_parameter_repair_review.py", refresh.STEPS)
        self.assertIn("build_bithumb_current_actionable_family_parameter_repair_gatekeeper_packet.py", refresh.STEPS)
        self.assertIn("build_bithumb_non_orca_entry_source_alternate_child_packet.py", refresh.STEPS)
        self.assertIn("build_bithumb_current_actionable_shadow_human_decision_draft.py", refresh.STEPS)
        self.assertIn("build_btc_eth_intraday_shadow_human_decision_draft.py", refresh.STEPS)
        self.assertIn("build_paper_smoke_human_decision_draft.py", refresh.STEPS)
        self.assertIn("build_kis_environment_operator_handoff.py", refresh.STEPS)
        self.assertIn("build_goal_model_factory_remaining_blockers_report.py", refresh.STEPS)
        self.assertIn("build_goal_model_factory_unblock_verification_packet.py", refresh.STEPS)
        self.assertIn("build_btc_eth_intraday_oos_stability_review.py", refresh.STEPS)
        self.assertIn("build_btc_eth_intraday_robustness_stress.py", refresh.STEPS)
        self.assertIn("build_btc_eth_intraday_robustness_repair_review.py", refresh.STEPS)
        self.assertIn("build_btc_eth_intraday_robustness_repair_delta_review.py", refresh.STEPS)
        self.assertIn("build_btc_eth_intraday_low_turnover_followup_gatekeeper_packet.py", refresh.STEPS)
        self.assertIn("build_gatekeeper_review_decision_phrase_packet.py", refresh.STEPS)
        self.assertIn("build_gatekeeper_decision_priority_report.py", refresh.STEPS)
        self.assertIn("build_model_factory_experiment_queue.py", refresh.STEPS)
        self.assertIn("build_paper_evidence_gap_diagnostic.py", refresh.STEPS)
        self.assertNotIn("run_bithumb_current_actionable_shadow_observation_loop.py", refresh.STEPS)
        progress_delta_index = refresh.STEPS.index("build_paper_evidence_progress_delta.py")
        gap_diagnostic_index = refresh.STEPS.index("build_paper_evidence_gap_diagnostic.py")
        risk_guard_index = refresh.STEPS.index("build_realtime_risk_guard_report.py")
        self.assertLess(progress_delta_index, gap_diagnostic_index)
        self.assertLess(gap_diagnostic_index, risk_guard_index)
        stock_stress_index = refresh.STEPS.index("build_stock_risk_conversion_robustness_stress.py")
        stock_repair_index = refresh.STEPS.index("build_stock_risk_conversion_sizing_repair_report.py")
        stock_packet_index = refresh.STEPS.index("build_stock_conversion_gatekeeper_review_packet.py")
        self.assertLess(stock_stress_index, stock_repair_index)
        self.assertLess(stock_repair_index, stock_packet_index)
        self.assertLess(stock_stress_index, stock_packet_index)
        bithumb_stress_index = refresh.STEPS.index("build_bithumb_current_actionable_robustness_stress.py")
        bithumb_alternate_robustness_index = refresh.STEPS.index("build_bithumb_current_actionable_alternate_robustness_review.py")
        bithumb_family_diversity_index = refresh.STEPS.index("build_bithumb_current_actionable_family_diversity_review.py")
        bithumb_family_parameter_repair_index = refresh.STEPS.index("build_bithumb_current_actionable_family_parameter_repair_review.py")
        bithumb_family_parameter_repair_packet_index = refresh.STEPS.index("build_bithumb_current_actionable_family_parameter_repair_gatekeeper_packet.py")
        bithumb_packet_index = refresh.STEPS.index("build_bithumb_current_actionable_gatekeeper_review_packet.py")
        self.assertLess(bithumb_stress_index, bithumb_alternate_robustness_index)
        self.assertLess(bithumb_alternate_robustness_index, bithumb_family_diversity_index)
        self.assertLess(bithumb_family_diversity_index, bithumb_family_parameter_repair_index)
        self.assertLess(bithumb_family_parameter_repair_index, bithumb_family_parameter_repair_packet_index)
        self.assertLess(bithumb_family_parameter_repair_packet_index, bithumb_packet_index)
        self.assertLess(bithumb_alternate_robustness_index, bithumb_packet_index)
        self.assertLess(bithumb_stress_index, bithumb_packet_index)
        bithumb_action_index = refresh.STEPS.index("build_bithumb_current_actionable_shadow_registration_action_packet.py")
        bithumb_rollover_index = refresh.STEPS.index("build_bithumb_current_actionable_shadow_rollover_review_packet.py")
        bithumb_draft_index = refresh.STEPS.index("build_bithumb_current_actionable_shadow_human_decision_draft.py")
        bithumb_signal_index = refresh.STEPS.index("build_bithumb_current_actionable_shadow_signal_adapter.py")
        self.assertLess(bithumb_action_index, bithumb_rollover_index)
        self.assertLess(bithumb_rollover_index, bithumb_draft_index)
        self.assertLess(bithumb_draft_index, bithumb_signal_index)
        self.assertLess(bithumb_action_index, bithumb_signal_index)
        btc_eth_template_index = refresh.STEPS.index("build_btc_eth_intraday_shadow_decision_template.py")
        btc_eth_draft_index = refresh.STEPS.index("build_btc_eth_intraday_shadow_human_decision_draft.py")
        btc_eth_oos_index = refresh.STEPS.index("build_btc_eth_intraday_oos_walkforward.py")
        btc_eth_stability_index = refresh.STEPS.index("build_btc_eth_intraday_oos_stability_review.py")
        btc_eth_robustness_index = refresh.STEPS.index("build_btc_eth_intraday_robustness_stress.py")
        btc_eth_robustness_repair_index = refresh.STEPS.index("build_btc_eth_intraday_robustness_repair_review.py")
        btc_eth_risk_index = refresh.STEPS.index("build_btc_eth_intraday_risk_conversion.py")
        btc_eth_repair_delta_index = refresh.STEPS.index("build_btc_eth_intraday_robustness_repair_delta_review.py")
        btc_eth_low_turnover_followup_index = refresh.STEPS.index("build_btc_eth_intraday_low_turnover_followup_sweep.py")
        btc_eth_low_turnover_followup_packet_index = refresh.STEPS.index(
            "build_btc_eth_intraday_low_turnover_followup_gatekeeper_packet.py"
        )
        non_orca_entry_source_rebuild_packet_index = refresh.STEPS.index(
            "build_bithumb_non_orca_entry_source_rebuild_gatekeeper_packet.py"
        )
        non_orca_entry_source_alternate_child_index = refresh.STEPS.index(
            "build_bithumb_non_orca_entry_source_alternate_child_packet.py"
        )
        bithumb_family_parameter_repair_review_index = refresh.STEPS.index(
            "build_bithumb_current_actionable_family_parameter_repair_review.py"
        )
        self.assertLess(btc_eth_oos_index, btc_eth_stability_index)
        self.assertLess(btc_eth_stability_index, btc_eth_robustness_index)
        self.assertLess(btc_eth_robustness_index, btc_eth_robustness_repair_index)
        self.assertLess(btc_eth_robustness_repair_index, btc_eth_risk_index)
        self.assertLess(btc_eth_risk_index, btc_eth_repair_delta_index)
        self.assertLess(btc_eth_repair_delta_index, btc_eth_template_index)
        self.assertLess(btc_eth_template_index, btc_eth_draft_index)
        self.assertLess(btc_eth_low_turnover_followup_index, btc_eth_low_turnover_followup_packet_index)
        self.assertLess(btc_eth_low_turnover_followup_packet_index, btc_eth_robustness_repair_index)
        self.assertLess(non_orca_entry_source_rebuild_packet_index, non_orca_entry_source_alternate_child_index)
        self.assertLess(non_orca_entry_source_alternate_child_index, bithumb_family_parameter_repair_review_index)
        pending_board_index = refresh.STEPS.index("build_gatekeeper_pending_decision_board.py")
        phrase_packet_index = refresh.STEPS.index("build_gatekeeper_review_decision_phrase_packet.py")
        pull_through_index = refresh.STEPS.index("build_model_factory_pull_through_board.py")
        paper_smoke_packet_index = refresh.STEPS.index("build_paper_smoke_gatekeeper_review_packet.py")
        paper_smoke_draft_index = refresh.STEPS.index("build_paper_smoke_human_decision_draft.py")
        self.assertLess(paper_smoke_packet_index, paper_smoke_draft_index)
        self.assertLess(paper_smoke_draft_index, pending_board_index)
        self.assertLess(pending_board_index, phrase_packet_index)
        self.assertLess(phrase_packet_index, pull_through_index)

    def test_final_steps_converge_public_operational_and_goal_audit_surfaces(self) -> None:
        def last_index(script: str) -> int:
            return len(refresh.STEPS) - 1 - list(reversed(refresh.STEPS)).index(script)

        final_operational_index = last_index("build_operational_monitor_report.py")
        public_before_operational_index = max(
            index
            for index, script in enumerate(refresh.STEPS[:final_operational_index])
            if script == "build_public_dashboard_export.py"
        )
        final_checklist_index = last_index("build_goal_model_factory_requirement_checklist.py")
        final_audit_index = last_index("build_goal_model_factory_completion_audit.py")
        final_blockers_index = last_index("build_goal_model_factory_remaining_blockers_report.py")
        final_unblock_index = last_index("build_goal_model_factory_unblock_verification_packet.py")
        final_pull_through_index = last_index("build_model_factory_pull_through_board.py")
        final_dashboard_index = last_index("build_pipeline_dashboard.py")
        final_public_after_unblock_index = last_index("build_public_dashboard_export.py")

        self.assertLess(public_before_operational_index, final_operational_index)
        self.assertLess(final_operational_index, final_checklist_index)
        self.assertLess(final_checklist_index, final_audit_index)
        self.assertLess(final_audit_index, final_blockers_index)
        self.assertLess(final_blockers_index, final_unblock_index)
        self.assertLess(final_unblock_index, final_pull_through_index)
        self.assertLess(final_pull_through_index, final_dashboard_index)
        self.assertLess(final_dashboard_index, final_public_after_unblock_index)
        self.assertEqual(final_public_after_unblock_index, len(refresh.STEPS) - 1)

    def test_accepts_taxonomy_and_paper_smoke_collect_evidence_blocks(self) -> None:
        taxonomy = {
            "script": "build_gatekeeper_evidence_taxonomy.py",
            "ok": False,
            "returncode": 1,
            "stdout_tail": (
                '{"status":"BLOCKED","recommended_gatekeeper_lane":'
                '"COLLECT_MORE_REPLAY_OR_LIVE_LIKE_BREADTH",'
                '"pipeline_can_advance_without_waiting_for_5_of_5":false}'
            ),
            "stderr_tail": "",
        }
        smoke = {
            "script": "build_paper_smoke_gatekeeper_review_packet.py",
            "ok": False,
            "returncode": 1,
            "stdout_tail": (
                '{"status":"BLOCKED","review_ready":false,'
                '"blockers":["risk_guard_pass","taxonomy_pass","taxonomy_paper_smoke_not_ready"]}'
            ),
            "stderr_tail": "",
        }

        self.assertTrue(refresh.accepted_step_result(taxonomy))
        self.assertTrue(refresh.accepted_step_result(smoke))

    def test_accepts_family_parameter_repair_packet_risk_guard_block(self) -> None:
        result = {
            "script": "build_bithumb_current_actionable_family_parameter_repair_gatekeeper_packet.py",
            "ok": False,
            "returncode": 1,
            "stdout_tail": '{"status":"BLOCKED","blockers":["risk_guard_hard_safety_pass"]}',
            "stderr_tail": "",
        }

        self.assertTrue(refresh.accepted_step_result(result))

    def test_prompt_to_artifact_incomplete_requirements_are_expected(self) -> None:
        checklist = {
            "missing_or_incomplete": [
                {"requirement": "Prompt-to-artifact deliverable: two_axis_model_factory_scope"},
                {"requirement": "Prompt-to-artifact deliverable: research_conversion_operations_lanes"},
                {"requirement": "Prompt-to-artifact deliverable: current_paper_activation_gate"},
            ]
        }

        self.assertEqual(refresh.unexpected_checklist_requirements(checklist), [])

    def test_realtime_risk_guard_warn_is_expected_collection_warning(self) -> None:
        classified = refresh.operational_warning_classification(
            {"warnings": ["NON_PASS_STATUS:realtime_risk_guard:WARN"]}
        )

        self.assertEqual(classified["expected_collect_evidence_warnings"], ["NON_PASS_STATUS:realtime_risk_guard:WARN"])
        self.assertEqual(classified["actionable_warnings"], [])

    def test_expected_realtime_risk_warn_overrides_legacy_actionable_label(self) -> None:
        classified = refresh.operational_warning_classification(
            {
                "warnings": ["NON_PASS_STATUS:realtime_risk_guard:WARN"],
                "actionable_warnings": ["NON_PASS_STATUS:realtime_risk_guard:WARN"],
            }
        )

        self.assertEqual(classified["expected_collect_evidence_warnings"], ["NON_PASS_STATUS:realtime_risk_guard:WARN"])
        self.assertEqual(classified["actionable_warnings"], [])

    def test_phrase_packet_ready_decision_parity_detects_missing_phrase(self) -> None:
        parity = refresh.phrase_packet_ready_decision_parity(
            {
                "ready_decision_count": 2,
                "items": [
                    {
                        "decision_id": "stock_portfolio_sleeve_pairwise_resilience_review",
                        "ready_for_human_review": True,
                    },
                    {
                        "decision_id": "stock_portfolio_sleeve_pairwise_fragility_repair_review",
                        "ready_for_human_review": True,
                    },
                ],
            },
            {
                "ready_phrase_count": 1,
                "ready_phrases": [
                    {
                        "decision_id": "stock_portfolio_sleeve_pairwise_resilience_review",
                        "ready_for_human_review": True,
                    }
                ],
            },
        )

        self.assertFalse(parity["ok"])
        self.assertEqual(
            parity["missing_from_phrase"],
            ["stock_portfolio_sleeve_pairwise_fragility_repair_review"],
        )

    def test_phrase_packet_ready_decision_parity_accepts_matching_surfaces(self) -> None:
        parity = refresh.phrase_packet_ready_decision_parity(
            {
                "ready_decision_count": 1,
                "items": [
                    {
                        "decision_id": "stock_portfolio_sleeve_pairwise_fragility_repair_review",
                        "ready_for_human_review": True,
                    }
                ],
            },
            {
                "ready_phrase_count": 1,
                "ready_phrases": [
                    {
                        "decision_id": "stock_portfolio_sleeve_pairwise_fragility_repair_review",
                        "ready_for_human_review": True,
                    }
                ],
            },
        )

        self.assertTrue(parity["ok"])
        self.assertEqual(parity["missing_from_phrase"], [])
        self.assertEqual(parity["extra_phrase_ids"], [])

    def test_phrase_packet_public_parity_detects_missing_public_phrase(self) -> None:
        parity = refresh.phrase_packet_public_parity(
            {
                "ready_phrase_count": 2,
                "ready_phrases": [
                    {
                        "decision_id": "stock_portfolio_sleeve_pairwise_resilience_review",
                        "ready_for_human_review": True,
                    },
                    {
                        "decision_id": "stock_portfolio_sleeve_pairwise_fragility_repair_review",
                        "ready_for_human_review": True,
                    },
                ],
            },
            {
                "ready_phrase_count": 1,
                "ready_phrases": [
                    {"decision_id": "stock_portfolio_sleeve_pairwise_resilience_review"}
                ],
            },
        )

        self.assertFalse(parity["ok"])
        self.assertEqual(
            parity["missing_from_public"],
            ["stock_portfolio_sleeve_pairwise_fragility_repair_review"],
        )

    def test_phrase_packet_public_parity_accepts_matching_public_surface(self) -> None:
        parity = refresh.phrase_packet_public_parity(
            {
                "ready_phrase_count": 1,
                "ready_phrases": [
                    {
                        "decision_id": "stock_portfolio_sleeve_pairwise_fragility_repair_review",
                        "ready_for_human_review": True,
                    }
                ],
            },
            {
                "ready_phrase_count": 1,
                "ready_phrases": [
                    {"decision_id": "stock_portfolio_sleeve_pairwise_fragility_repair_review"}
                ],
            },
        )

        self.assertTrue(parity["ok"])
        self.assertEqual(parity["missing_from_public"], [])
        self.assertEqual(parity["extra_public_ids"], [])

    def test_summary_surfaces_safe_bithumb_observation_loop_without_running_it(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "STALLED_ON_EVENT_EVIDENCE",
                        "slowest_gate_dimension": "non_flat_signals",
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            if str(path).endswith("bithumb_current_actionable_shadow_observation_loop_latest.json"):
                return {
                    "last_status": "ok",
                    "cycles_completed": 1,
                    "cycles_requested": 1,
                    "safety": {
                        "does_run_observation_loop": True,
                        "does_start_order_shadow_loop": False,
                        "does_start_shadow_loop": False,
                        "does_emit_order_signal": False,
                        "does_write_order_intent": False,
                        "does_enable_paper": False,
                        "does_enable_live": False,
                        "broker_submit_allowed": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                    },
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "PASS", report["verifier_checks"])
        self.assertTrue(report["bithumb_shadow_observation_loop"]["surface_present"])
        self.assertTrue(report["bithumb_shadow_observation_loop"]["surface_ok"])
        self.assertFalse(report["bithumb_shadow_observation_loop"]["does_start_shadow_loop"])
        self.assertFalse(report["bithumb_shadow_observation_loop"]["broker_submit_allowed"])

    def test_summary_reports_fail_if_any_step_fails_and_keeps_no_order_safety(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {"paper_evidence_readiness_percent": 40.0, "dominant_blocking_dimensions": []},
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            return {}

        with patch.object(refresh, "read_json", side_effect=fake_read_json):
            report = refresh.build_summary(
                [
                    {"script": "ok.py", "returncode": 0, "ok": True},
                    {"script": "fail.py", "returncode": 1, "ok": False},
                ]
            )

        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["safety"]["broker_submit_scope"], "paper_only")
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertFalse(report["safety"]["live_enabled"])
        self.assertFalse(report["safety"]["private_submit_used"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_summary_requires_paper_only_broker_submit_scope_when_paper_evidence_present(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("paper_promotion_evidence_latest.json"):
                return {"evidence": {"paper_safety": {"broker_submit_scope": "private_submit"}}}
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {"paper_evidence_readiness_percent": 40.0, "dominant_blocking_dimensions": []},
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            return {}

        with patch.object(refresh, "read_json", side_effect=fake_read_json):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["verifier_checks"]["broker_submit_scope_ok"])
        self.assertEqual(report["safety"]["broker_submit_scope"], "private_submit")

    def test_summary_accepts_paper_only_broker_submit_scope_when_paper_evidence_present(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("paper_promotion_evidence_latest.json"):
                return {"evidence": {"paper_safety": {"broker_submit_scope": "paper_only"}}}
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {"paper_evidence_readiness_percent": 40.0, "dominant_blocking_dimensions": []},
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            return {}

        with patch.object(refresh, "read_json", side_effect=fake_read_json):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertTrue(report["verifier_checks"]["broker_submit_scope_ok"])
        self.assertEqual(report["safety"]["broker_submit_scope"], "paper_only")

    def test_summary_rejects_direct_bithumb_shadow_registration_step(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "STALLED_ON_EVENT_EVIDENCE",
                        "slowest_gate_dimension": "non_flat_signals",
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            return {}

        blocked_step = {
            "script": "register_bithumb_current_actionable_shadow_candidate.py",
            "returncode": 1,
            "ok": False,
            "stdout_tail": (
                '{"status":"BLOCKED","blockers":["ACTION_PACKET_NOT_READY",'
                '"VALID_SHADOW_REVIEW_ONLY_DECISION_MISSING","HUMAN_DECISION_CANDIDATE_MISMATCH"]}'
            ),
            "stderr_tail": "",
        }

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([blocked_step])

        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["accepted_blocked_steps"], [])

    def test_summary_accepts_expected_bithumb_signal_adapter_parameter_blocker(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 80.0,
                        "dominant_blocking_dimensions": ["paper_cycles"],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "ETA_AVAILABLE",
                        "slowest_gate_dimension": "paper_cycles",
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "goal_requirement_checklist": {"status": "COMPLETE", "incomplete_count": 0},
                }
            return {}

        blocked_step = {
            "script": "build_bithumb_current_actionable_shadow_signal_adapter.py",
            "returncode": 1,
            "ok": False,
            "stdout_tail": '{"status":"BLOCKED","blockers":["OOS_PARAMETERS_NOT_FOUND_FOR_REGISTERED_CANDIDATE"]}',
            "stderr_tail": "",
        }

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([blocked_step])

        self.assertEqual(report["status"], "PASS", report["verifier_checks"])
        self.assertEqual(report["accepted_blocked_steps"][0]["script"], "build_bithumb_current_actionable_shadow_signal_adapter.py")

    def test_summary_fails_when_public_export_has_stale_warning(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "operational_warnings": ["STALE_DERIVED_REPORT:dashboard:OLDER_THAN:source"],
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "STALLED_ON_EVENT_EVIDENCE",
                        "slowest_gate_dimension": "non_flat_signals",
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            return {}

        with patch.object(refresh, "read_json", side_effect=fake_read_json):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["public_export_checks"]["stale_derived_warning_count"], 1)

    def test_summary_fails_when_public_export_has_sensitive_string(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {"paper_evidence_readiness_percent": 40.0, "dominant_blocking_dimensions": []},
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[{"path": "public_summary.json", "pattern": "broker_submit"}]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertGreater(report["public_export_checks"]["sensitive_hit_count"], 0)

    def test_summary_fails_when_completion_audit_has_stale_warning(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {"paper_evidence_readiness_percent": 40.0, "dominant_blocking_dimensions": []},
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            if str(path).endswith("goal_model_factory_completion_audit_latest.json"):
                return {
                    "checks": [
                        {
                            "requirement": "Maintain file-backed progress and checkpoint record",
                            "evidence": {
                                "operational_warnings": [
                                    "STALE_DERIVED_REPORT:paper_evidence_velocity_monitor:OLDER_THAN:paper_promotion_evidence"
                                ]
                            },
                        }
                    ]
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["completion_audit_checks"]["stale_derived_warning_count"], 1)

    def test_summary_fails_when_public_readiness_surface_is_missing(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {"paper_velocity_monitor": {"paper_evidence_readiness_percent": None}}
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["public_export_checks"]["readiness_surface_present"])

    def test_summary_fails_when_public_requirement_checklist_surface_is_missing(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    }
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["public_export_checks"]["goal_requirement_checklist_surface_present"])

    def test_summary_fails_when_public_requirement_checklist_progress_surface_lags_source(self) -> None:
        def fake_read_json(path, default):
            path_text = str(path)
            if path_text.endswith("goal_model_factory_requirement_checklist_latest.json"):
                return {
                    "items": [
                        {
                            "requirement": "Keep a file-backed progress record for each iteration",
                            "evidence": {
                                "progress_entry_count": 155,
                                "latest_iteration_number": 131,
                                "open_iteration_count": 0,
                            },
                        }
                    ]
                }
            if path_text.endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "goal_requirement_checklist": {
                        "status": "NOT_COMPLETE",
                        "incomplete_count": 2,
                        "progress": {
                            "progress_entry_count": 154,
                            "latest_iteration_number": 130,
                            "open_iteration_count": 0,
                        },
                    },
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["verifier_checks"]["public_checklist_progress_ok"])
        self.assertFalse(report["public_export_checks"]["goal_requirement_checklist_progress_surface_present"])
        self.assertEqual(report["public_export_checks"]["goal_requirement_checklist_latest_iteration_number"], 130)

    def test_summary_fails_when_operational_monitor_has_stale_warning(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "STALLED_ON_EVENT_EVIDENCE",
                        "slowest_gate_dimension": "non_flat_signals",
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            if str(path).endswith("operational_monitor_latest.json"):
                return {
                    "warnings": [
                        "STALE_DERIVED_REPORT:paper_evidence_velocity_monitor:OLDER_THAN:paper_promotion_evidence"
                    ]
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["operational_monitor"]["stale_derived_warning_count"], 1)

    def test_summary_surfaces_operational_actionable_warning_counts(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            if str(path).endswith("operational_monitor_latest.json"):
                return {
                    "status": "WARN",
                    "blockers": [],
                    "warnings": [
                        "NON_PASS_STATUS:paper_promotion_evidence:KEEP_PAPER_COLLECT_EVIDENCE",
                        "MISSING_PROCESS:run_gatekeeper_refresh_loop.py",
                    ],
                    "expected_collect_evidence_warnings": [
                        "NON_PASS_STATUS:paper_promotion_evidence:KEEP_PAPER_COLLECT_EVIDENCE"
                    ],
                    "actionable_warnings": ["MISSING_PROCESS:run_gatekeeper_refresh_loop.py"],
                }
            if str(path).endswith("stock_risk_conversion_queue_latest.json"):
                return {
                    "status": "READY_FOR_GATEKEEPER_REVIEW",
                    "target_count": 5,
                    "ready_candidate_count": 5,
                    "blocked_candidate_count": 0,
                    "queue": [{"candidate_id": "stock_aggressive__trim22"}],
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["operational_monitor"]["warning_count"], 2)
        self.assertEqual(report["operational_monitor"]["expected_collect_evidence_warning_count"], 1)
        self.assertEqual(report["operational_monitor"]["actionable_warning_count"], 1)
        self.assertFalse(report["operational_monitor"]["actionable_warnings_ok"])
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(
            report["operational_monitor"]["actionable_warnings"],
            ["MISSING_PROCESS:run_gatekeeper_refresh_loop.py"],
        )
        self.assertEqual(report["stock_risk_conversion_queue"]["ready_candidate_count"], 5)
        self.assertEqual(report["stock_risk_conversion_queue"]["top_candidate_id"], "stock_aggressive__trim22")

    def test_summary_passes_when_operational_warnings_are_expected_only(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "STALLED_ON_EVENT_EVIDENCE",
                        "slowest_gate_dimension": "non_flat_signals",
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            if str(path).endswith("operational_monitor_latest.json"):
                return {
                    "status": "WARN",
                    "blockers": [],
                    "warnings": [
                        "NON_PASS_STATUS:paper_promotion_evidence:KEEP_PAPER_COLLECT_EVIDENCE",
                    ],
                    "expected_collect_evidence_warnings": [
                        "NON_PASS_STATUS:paper_promotion_evidence:KEEP_PAPER_COLLECT_EVIDENCE"
                    ],
                    "actionable_warnings": [],
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertTrue(report["operational_monitor"]["actionable_warnings_ok"])
        self.assertEqual(report["operational_monitor"]["actionable_warning_count"], 0)
        self.assertEqual(report["status"], "PASS", report["verifier_checks"])
        self.assertTrue(report["public_export_checks"]["pace_eta_surface_present"])

    def test_summary_fails_when_public_pace_eta_surface_is_missing(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": None,
                        "slowest_gate_dimension": None,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["public_export_checks"]["pace_eta_surface_present"])

    def test_summary_fails_when_public_event_stall_surface_is_missing_for_incomplete_evidence(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "STALLED_ON_EVENT_EVIDENCE",
                        "slowest_gate_dimension": "non_flat_signals",
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            if str(path).endswith("paper_evidence_progress_delta_latest.json"):
                return {
                    "current": {
                        "paper_cycles_missing": 117,
                        "non_flat_signals_missing": 3,
                        "executable_orders_missing": 3,
                    }
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["public_export_checks"]["event_stall_surface_present"])

    def test_summary_fails_when_completion_audit_pace_surface_is_missing(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "STALLED_ON_EVENT_EVIDENCE",
                        "slowest_gate_dimension": "non_flat_signals",
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            if str(path).endswith("goal_model_factory_completion_audit_latest.json"):
                return {
                    "status": "NOT_COMPLETE",
                    "completion_blocker_summary": {
                        "paper_evidence_remaining": {"pace_summary": {}}
                    },
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["completion_audit_checks"]["pace_eta_surface_present"])

    def test_summary_fails_when_pull_through_board_pace_surface_is_missing(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "STALLED_ON_EVENT_EVIDENCE",
                        "slowest_gate_dimension": "non_flat_signals",
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            if str(path).endswith("paper_evidence_progress_delta_latest.json"):
                return {
                    "current": {
                        "paper_cycles_missing": 118,
                        "non_flat_signals_missing": 3,
                        "executable_orders_missing": 3,
                    }
                }
            if str(path).endswith("goal_model_factory_completion_audit_latest.json"):
                return {
                    "status": "NOT_COMPLETE",
                    "completion_blocker_summary": {
                        "paper_evidence_remaining": {
                            "pace_summary": {
                                "eta_status": "STALLED_ON_EVENT_EVIDENCE",
                                "slowest_gate_dimension": "non_flat_signals",
                            }
                        }
                    },
                }
            if str(path).endswith("pull_through_board_latest.json"):
                return {"gatekeeper_action_packet": {"paper_evidence_pace_summary": {}}}
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["pull_through_board_checks"]["pace_eta_surface_present"])

    def test_summary_fails_when_pull_through_board_event_stall_surface_is_missing(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "STALLED_ON_EVENT_EVIDENCE",
                        "slowest_gate_dimension": "non_flat_signals",
                        "event_stall_status": "EVENT_EVIDENCE_STALLED",
                        "non_flat_hours_since_last_increase": 2.0,
                        "executable_hours_since_last_increase": 2.0,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            if str(path).endswith("paper_evidence_progress_delta_latest.json"):
                return {
                    "current": {
                        "paper_cycles_missing": 116,
                        "non_flat_signals_missing": 3,
                        "executable_orders_missing": 3,
                    }
                }
            if str(path).endswith("paper_evidence_gap_diagnostic_latest.json"):
                return {
                    "status": "REGRESSION_AND_EVENT_STALL",
                    "gap_summary": {"non_flat_signal_count": 2, "executable_order_count": 2},
                    "why_not_ready": {"event_eta_status": "STALLED_ON_EVENT_EVIDENCE"},
                    "regression_summary": {
                        "non_flat_regressed_from_recent_max": True,
                        "executable_regressed_from_recent_max": True,
                        "max_non_flat_signal_count": 3,
                        "max_executable_order_count": 3,
                    },
                    "safety": {
                        "live_enabled": False,
                        "broker_submit_allowed": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                        "promotion_allowed": False,
                        "live_allowed": False,
                    },
                }
            if str(path).endswith("goal_model_factory_completion_audit_latest.json"):
                return {
                    "status": "NOT_COMPLETE",
                    "completion_blocker_summary": {
                        "paper_evidence_remaining": {
                            "pace_summary": {
                                "eta_status": "STALLED_ON_EVENT_EVIDENCE",
                                "slowest_gate_dimension": "non_flat_signals",
                            }
                        }
                    },
                }
            if str(path).endswith("pull_through_board_latest.json"):
                return {
                    "gatekeeper_action_packet": {
                        "paper_evidence_pace_summary": {
                            "eta_status": "STALLED_ON_EVENT_EVIDENCE",
                            "slowest_gate_dimension": "non_flat_signals",
                        },
                        "paper_evidence_event_stall_summary": {},
                    }
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["pull_through_board_checks"]["event_stall_surface_present"])

    def test_summary_fails_when_event_stall_triage_surface_is_missing_for_incomplete_evidence(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "STALLED_ON_EVENT_EVIDENCE",
                        "slowest_gate_dimension": "non_flat_signals",
                        "event_stall_status": "EVENT_EVIDENCE_STALLED",
                        "stall_severity": "WARN_STALL",
                        "non_flat_hours_since_last_increase": 2.0,
                        "executable_hours_since_last_increase": 2.0,
                    },
                    "paper_event_stall_triage": {
                        "status": "READY_FOR_STALL_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "order_submission_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                        "counts_as_extended_paper_promotion": False,
                        "counts_as_live_readiness": False,
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            if str(path).endswith("paper_evidence_progress_delta_latest.json"):
                return {
                    "current": {
                        "paper_cycles_missing": 116,
                        "non_flat_signals_missing": 3,
                        "executable_orders_missing": 3,
                    }
                }
            if str(path).endswith("paper_evidence_gap_diagnostic_latest.json"):
                return {
                    "status": "REGRESSION_AND_EVENT_STALL",
                    "gap_summary": {"non_flat_signal_count": 2, "executable_order_count": 2},
                    "why_not_ready": {"event_eta_status": "STALLED_ON_EVENT_EVIDENCE"},
                    "regression_summary": {
                        "non_flat_regressed_from_recent_max": True,
                        "executable_regressed_from_recent_max": True,
                        "max_non_flat_signal_count": 3,
                        "max_executable_order_count": 3,
                    },
                    "safety": {
                        "live_enabled": False,
                        "broker_submit_allowed": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                        "promotion_allowed": False,
                        "live_allowed": False,
                    },
                }
            if str(path).endswith("goal_model_factory_completion_audit_latest.json"):
                return {
                    "status": "NOT_COMPLETE",
                    "completion_blocker_summary": {
                        "paper_evidence_remaining": {
                            "pace_summary": {
                                "eta_status": "STALLED_ON_EVENT_EVIDENCE",
                                "slowest_gate_dimension": "non_flat_signals",
                            },
                            "event_stall_summary": {"stall_severity": "WARN_STALL"},
                        }
                    },
                }
            if str(path).endswith("pull_through_board_latest.json"):
                return {
                    "gatekeeper_action_packet": {
                        "paper_evidence_pace_summary": {
                            "eta_status": "STALLED_ON_EVENT_EVIDENCE",
                            "slowest_gate_dimension": "non_flat_signals",
                        },
                        "paper_evidence_event_stall_summary": {
                            "event_stall_status": "EVENT_EVIDENCE_STALLED",
                            "stall_severity": "WARN_STALL",
                        },
                        "paper_evidence_event_stall_triage": {
                            "status": "READY_FOR_STALL_REVIEW",
                            "review_ready": True,
                            "blocker_count": 0,
                            "path": "C:\\AI\\ops\\reports\\paper_evidence_event_stall_triage_latest.json",
                            "promotion_allowed_by_this_report": False,
                            "live_allowed_by_this_report": False,
                            "broker_submit_allowed_by_this_report": False,
                            "real_orders_allowed_by_this_report": False,
                            "counts_as_extended_paper_promotion": False,
                            "counts_as_live_readiness": False,
                        },
                    }
                }
            if str(path).endswith("paper_evidence_event_stall_triage_latest.json"):
                return {}
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["paper_evidence_event_stall_triage"]["surface_present"])

    def test_summary_passes_with_safe_event_stall_triage_surface(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "STALLED_ON_EVENT_EVIDENCE",
                        "slowest_gate_dimension": "non_flat_signals",
                        "event_stall_status": "EVENT_EVIDENCE_STALLED",
                        "stall_severity": "WARN_STALL",
                        "non_flat_hours_since_last_increase": 2.0,
                        "executable_hours_since_last_increase": 2.0,
                    },
                    "paper_event_stall_triage": {
                        "status": "READY_FOR_STALL_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "order_submission_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                        "counts_as_extended_paper_promotion": False,
                        "counts_as_live_readiness": False,
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            if str(path).endswith("paper_evidence_progress_delta_latest.json"):
                return {
                    "current": {
                        "paper_cycles_missing": 116,
                        "non_flat_signals_missing": 3,
                        "executable_orders_missing": 3,
                    }
                }
            if str(path).endswith("paper_evidence_gap_diagnostic_latest.json"):
                return {
                    "status": "REGRESSION_AND_EVENT_STALL",
                    "gap_summary": {"non_flat_signal_count": 2, "executable_order_count": 2},
                    "why_not_ready": {"event_eta_status": "STALLED_ON_EVENT_EVIDENCE"},
                    "regression_summary": {
                        "non_flat_regressed_from_recent_max": True,
                        "executable_regressed_from_recent_max": True,
                        "max_non_flat_signal_count": 3,
                        "max_executable_order_count": 3,
                    },
                    "safety": {
                        "live_enabled": False,
                        "broker_submit_allowed": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                        "promotion_allowed": False,
                        "live_allowed": False,
                    },
                }
            if str(path).endswith("goal_model_factory_completion_audit_latest.json"):
                return {
                    "status": "NOT_COMPLETE",
                    "completion_blocker_summary": {
                        "paper_evidence_remaining": {
                            "pace_summary": {
                                "eta_status": "STALLED_ON_EVENT_EVIDENCE",
                                "slowest_gate_dimension": "non_flat_signals",
                            },
                            "event_stall_summary": {"stall_severity": "WARN_STALL"},
                        }
                    },
                }
            if str(path).endswith("pull_through_board_latest.json"):
                return {
                    "gatekeeper_action_packet": {
                        "paper_evidence_pace_summary": {
                            "eta_status": "STALLED_ON_EVENT_EVIDENCE",
                            "slowest_gate_dimension": "non_flat_signals",
                        },
                        "paper_evidence_event_stall_summary": {
                            "event_stall_status": "EVENT_EVIDENCE_STALLED",
                            "stall_severity": "WARN_STALL",
                        },
                        "paper_evidence_event_stall_triage": {
                            "status": "READY_FOR_STALL_REVIEW",
                            "review_ready": True,
                            "blocker_count": 0,
                            "path": "C:\\AI\\ops\\reports\\paper_evidence_event_stall_triage_latest.json",
                            "promotion_allowed_by_this_report": False,
                            "live_allowed_by_this_report": False,
                            "broker_submit_allowed_by_this_report": False,
                            "real_orders_allowed_by_this_report": False,
                            "counts_as_extended_paper_promotion": False,
                            "counts_as_live_readiness": False,
                        },
                    }
                }
            if str(path).endswith("paper_evidence_event_stall_triage_latest.json"):
                return {
                    "status": "READY_FOR_STALL_REVIEW",
                    "review_ready": True,
                    "blockers": [],
                    "permissions": {
                        "promotion_allowed_by_this_report": False,
                        "extended_paper_promotion_allowed_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "broker_submit_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                    "safety": {"order_paths_allowed_by_triage": False},
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "PASS", report["verifier_checks"])
        self.assertTrue(report["paper_evidence_event_stall_triage"]["surface_present"])
        self.assertFalse(report["paper_evidence_event_stall_triage"]["live_allowed_by_this_report"])
        self.assertTrue(report["paper_evidence_gap_diagnostic"]["surface_present"])
        self.assertTrue(report["paper_evidence_gap_diagnostic"]["non_flat_regressed_from_recent_max"])
        self.assertFalse(report["paper_evidence_gap_diagnostic"]["broker_submit_allowed"])

    def test_summary_fails_when_public_event_stall_triage_surface_is_missing(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "STALLED_ON_EVENT_EVIDENCE",
                        "slowest_gate_dimension": "non_flat_signals",
                        "event_stall_status": "EVENT_EVIDENCE_STALLED",
                        "stall_severity": "WARN_STALL",
                        "non_flat_hours_since_last_increase": 2.0,
                        "executable_hours_since_last_increase": 2.0,
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            if str(path).endswith("paper_evidence_progress_delta_latest.json"):
                return {
                    "current": {
                        "paper_cycles_missing": 116,
                        "non_flat_signals_missing": 3,
                        "executable_orders_missing": 3,
                    }
                }
            if str(path).endswith("goal_model_factory_completion_audit_latest.json"):
                return {
                    "status": "NOT_COMPLETE",
                    "completion_blocker_summary": {
                        "paper_evidence_remaining": {
                            "pace_summary": {
                                "eta_status": "STALLED_ON_EVENT_EVIDENCE",
                                "slowest_gate_dimension": "non_flat_signals",
                            },
                            "event_stall_summary": {"stall_severity": "WARN_STALL"},
                        }
                    },
                }
            if str(path).endswith("pull_through_board_latest.json"):
                return {
                    "gatekeeper_action_packet": {
                        "paper_evidence_pace_summary": {
                            "eta_status": "STALLED_ON_EVENT_EVIDENCE",
                            "slowest_gate_dimension": "non_flat_signals",
                        },
                        "paper_evidence_event_stall_summary": {
                            "event_stall_status": "EVENT_EVIDENCE_STALLED",
                            "stall_severity": "WARN_STALL",
                        },
                    }
                }
            if str(path).endswith("paper_evidence_event_stall_triage_latest.json"):
                return {
                    "status": "READY_FOR_STALL_REVIEW",
                    "review_ready": True,
                    "blockers": [],
                    "permissions": {
                        "promotion_allowed_by_this_report": False,
                        "extended_paper_promotion_allowed_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "broker_submit_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                    "safety": {"order_paths_allowed_by_triage": False},
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["public_export_checks"]["event_stall_triage_surface_present"])

    def test_summary_recomputes_actionable_warnings_from_raw_legacy_operational_monitor(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            if str(path).endswith("operational_monitor_latest.json"):
                return {
                    "status": "WARN",
                    "blockers": [],
                    "warnings": [
                        "NON_PASS_STATUS:goal_requirement_checklist:NOT_COMPLETE",
                        "UNKNOWN_STATUS:paper_autotrade",
                    ],
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["operational_monitor"]["expected_collect_evidence_warning_count"], 1)
        self.assertEqual(report["operational_monitor"]["actionable_warning_count"], 1)
        self.assertIn("UNKNOWN_STATUS:paper_autotrade", report["operational_monitor"]["actionable_warnings"])
        self.assertEqual(report["status"], "FAIL")

    def test_markdown_includes_stock_queue_summary(self) -> None:
        report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])
        report["stock_risk_conversion_queue"] = {
            "status": "READY_FOR_GATEKEEPER_REVIEW",
            "target_count": 5,
            "ready_candidate_count": 5,
            "top_candidate_id": "stock_aggressive__trim22",
        }
        report["stock_conversion_gatekeeper_review_packet"] = {
            "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
            "surface_present": True,
            "candidate_id": "stock_aggressive__trim22",
        }

        rendered = refresh.render_markdown(report)

        self.assertIn("stock_risk_conversion_queue", rendered)
        self.assertIn("READY_FOR_GATEKEEPER_REVIEW", rendered)
        self.assertIn("stock_aggressive__trim22", rendered)
        self.assertIn("stock_conversion_gatekeeper_review_packet", rendered)

    def test_summary_fails_when_stock_conversion_packet_surface_is_missing(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "ETA_AVAILABLE",
                        "slowest_gate_dimension": "paper_cycles",
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "stock_conversion_review_packet": {
                        "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                        "candidate_id": "stock_aggressive__trim22",
                        "blocker_count": 0,
                        "top5_target_count": 5,
                        "top5_ready_candidate_count": 5,
                        "top5_covered_candidate_count": 5,
                        "top5_stress_pass_candidate_count": 3,
                        "top5_full_coverage": True,
                        "top5_all_covered_candidates_safe": True,
                        "sizing_repair_status": "SIZING_REPAIR_READY",
                        "sizing_repair_ready_count": 2,
                        "stress_pass_plus_repair_ready_count": 5,
                        "promotion_allowed_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "order_submission_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                    "goal_requirement_checklist": {"status": "COMPLETE", "incomplete_count": 0},
                }
            if str(path).endswith("stock_conversion_gatekeeper_review_packet_latest.json"):
                return {}
            if str(path).endswith("stock_risk_conversion_queue_latest.json"):
                return {"status": "READY_FOR_GATEKEEPER_REVIEW"}
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["stock_conversion_gatekeeper_review_packet"]["surface_present"])

    def test_summary_passes_with_safe_stock_conversion_packet_surface(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "ETA_AVAILABLE",
                        "slowest_gate_dimension": "paper_cycles",
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "stock_conversion_review_packet": {
                        "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                        "candidate_id": "stock_aggressive__trim22",
                        "blocker_count": 0,
                        "top5_target_count": 5,
                        "top5_ready_candidate_count": 5,
                        "top5_covered_candidate_count": 5,
                        "top5_stress_pass_candidate_count": 3,
                        "top5_full_coverage": True,
                        "top5_all_covered_candidates_safe": True,
                        "sizing_repair_status": "SIZING_REPAIR_READY",
                        "sizing_repair_ready_count": 2,
                        "stress_pass_plus_repair_ready_count": 5,
                        "promotion_allowed_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "order_submission_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                    "goal_requirement_checklist": {"status": "COMPLETE", "incomplete_count": 0},
                }
            if str(path).endswith("stock_conversion_gatekeeper_review_packet_latest.json"):
                return {
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "candidate_id": "stock_aggressive__trim22",
                    "blockers": [],
                    "no_order_assertions": {
                        "promotion_allowed_by_this_report": False,
                        "paper_enabled_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "broker_submit_allowed_by_this_report": False,
                        "private_submit_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                    "robustness_stress": {
                        "queue_coverage": {
                            "target_count": 5,
                            "ready_candidate_count": 5,
                            "covered_candidate_count": 5,
                            "stress_pass_candidate_count": 3,
                            "all_covered_candidates_safe": True,
                            "top5_full_coverage": True,
                        },
                        "candidate_results": [
                            {"candidate_id": f"stock_{index}", "queue_order_paths_safe": True}
                            for index in range(5)
                        ],
                    },
                    "sizing_repair": {
                        "status": "SIZING_REPAIR_READY",
                        "repair_ready_count": 2,
                        "promotion_allowed_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "broker_submit_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                }
            if str(path).endswith("stock_risk_conversion_queue_latest.json"):
                return {"status": "READY_FOR_GATEKEEPER_REVIEW"}
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "PASS", report["verifier_checks"])
        self.assertTrue(report["verifier_checks"]["stock_top5_conversion_coverage_ok"])
        self.assertTrue(report["verifier_checks"]["public_stock_top5_conversion_coverage_ok"])
        self.assertTrue(report["stock_conversion_gatekeeper_review_packet"]["surface_present"])
        self.assertFalse(report["stock_conversion_gatekeeper_review_packet"]["live_allowed_by_this_report"])
        self.assertEqual(report["stock_conversion_gatekeeper_review_packet"]["top5_covered_candidate_count"], 5)
        self.assertEqual(report["stock_conversion_gatekeeper_review_packet"]["top5_stress_pass_candidate_count"], 3)
        self.assertEqual(report["stock_conversion_gatekeeper_review_packet"]["top5_repair_ready_count"], 2)

    def test_summary_fails_when_public_stock_conversion_packet_surface_is_missing(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "ETA_AVAILABLE",
                        "slowest_gate_dimension": "paper_cycles",
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "goal_requirement_checklist": {"status": "COMPLETE", "incomplete_count": 0},
                }
            if str(path).endswith("stock_conversion_gatekeeper_review_packet_latest.json"):
                return {
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "candidate_id": "stock_aggressive__trim22",
                    "blockers": [],
                    "no_order_assertions": {
                        "promotion_allowed_by_this_report": False,
                        "paper_enabled_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "broker_submit_allowed_by_this_report": False,
                        "private_submit_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                    "robustness_stress": {
                        "queue_coverage": {
                            "target_count": 5,
                            "ready_candidate_count": 5,
                            "covered_candidate_count": 5,
                            "stress_pass_candidate_count": 3,
                            "all_covered_candidates_safe": True,
                            "top5_full_coverage": True,
                        },
                        "candidate_results": [
                            {"candidate_id": f"stock_{index}", "queue_order_paths_safe": True}
                            for index in range(5)
                        ],
                    },
                    "sizing_repair": {
                        "status": "SIZING_REPAIR_READY",
                        "repair_ready_count": 2,
                        "promotion_allowed_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "broker_submit_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                }
            if str(path).endswith("stock_risk_conversion_queue_latest.json"):
                return {"status": "READY_FOR_GATEKEEPER_REVIEW"}
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["public_export_checks"]["stock_conversion_packet_surface_present"])

    def test_summary_passes_with_safe_public_stock_conversion_packet_surface(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "ETA_AVAILABLE",
                        "slowest_gate_dimension": "paper_cycles",
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "stock_conversion_review_packet": {
                        "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                        "candidate_id": "stock_aggressive__trim22",
                        "blocker_count": 0,
                        "top5_target_count": 5,
                        "top5_ready_candidate_count": 5,
                        "top5_covered_candidate_count": 5,
                        "top5_stress_pass_candidate_count": 3,
                        "top5_full_coverage": True,
                        "top5_all_covered_candidates_safe": True,
                        "sizing_repair_status": "SIZING_REPAIR_READY",
                        "sizing_repair_ready_count": 2,
                        "stress_pass_plus_repair_ready_count": 5,
                        "promotion_allowed_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "order_submission_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                    "goal_requirement_checklist": {"status": "COMPLETE", "incomplete_count": 0},
                }
            if str(path).endswith("stock_conversion_gatekeeper_review_packet_latest.json"):
                return {
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "candidate_id": "stock_aggressive__trim22",
                    "blockers": [],
                    "no_order_assertions": {
                        "promotion_allowed_by_this_report": False,
                        "paper_enabled_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "broker_submit_allowed_by_this_report": False,
                        "private_submit_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                    "robustness_stress": {
                        "queue_coverage": {
                            "target_count": 5,
                            "ready_candidate_count": 5,
                            "covered_candidate_count": 5,
                            "stress_pass_candidate_count": 3,
                            "all_covered_candidates_safe": True,
                            "top5_full_coverage": True,
                        },
                        "candidate_results": [
                            {"candidate_id": f"stock_{index}", "queue_order_paths_safe": True}
                            for index in range(5)
                        ],
                    },
                    "sizing_repair": {
                        "status": "SIZING_REPAIR_READY",
                        "repair_ready_count": 2,
                        "promotion_allowed_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "broker_submit_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                }
            if str(path).endswith("stock_risk_conversion_queue_latest.json"):
                return {"status": "READY_FOR_GATEKEEPER_REVIEW"}
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "PASS", report["verifier_checks"])
        self.assertTrue(report["verifier_checks"]["stock_top5_conversion_coverage_ok"])
        self.assertTrue(report["verifier_checks"]["public_stock_top5_conversion_coverage_ok"])
        self.assertTrue(report["public_export_checks"]["stock_conversion_packet_surface_present"])
        self.assertTrue(report["public_export_checks"]["stock_conversion_top5_surface_present"])

    def test_summary_requires_public_model_factory_experiment_queue_surface_when_queue_exists(self) -> None:
        def fake_read_json(path, default):
            path_text = str(path)
            if path_text.endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 87.5,
                        "dominant_blocking_dimensions": ["paper_cycles"],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "ETA_AVAILABLE",
                        "slowest_gate_dimension": "paper_cycles",
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 2},
                }
            if path_text.endswith("model_factory_experiment_queue_latest.json"):
                return {
                    "status": "PASS",
                    "summary": {"experiment_count": 11, "ready_experiment_count": 9},
                    "unsafe_experiment_ids": [],
                    "no_order_assertions": {
                        "promotion_allowed_by_this_report": False,
                        "paper_enabled_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "broker_submit_allowed_by_this_report": False,
                        "private_submit_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                }
            if path_text.endswith("experiment_queue.json"):
                return {
                    "schema_version": "1.1",
                    "status": "PASS",
                    "summary": {"experiment_count": 11, "ready_experiment_count": 9},
                    "no_order_assertions": {
                        "promotion_allowed_by_this_report": False,
                        "paper_enabled_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "broker_submit_allowed_by_this_report": False,
                        "private_submit_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary(
                [{"script": "build_model_factory_experiment_queue.py", "returncode": 0, "ok": True}]
            )

        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["verifier_checks"]["public_experiment_queue_surface_ok"])
        self.assertFalse(report["public_export_checks"]["model_factory_experiment_queue_surface_safe"])

    def test_summary_passes_with_safe_public_model_factory_experiment_queue_surface(self) -> None:
        no_order = {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

        def fake_read_json(path, default):
            path_text = str(path)
            if path_text.endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 87.5,
                        "dominant_blocking_dimensions": ["paper_cycles"],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "ETA_AVAILABLE",
                        "slowest_gate_dimension": "paper_cycles",
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 2},
                    "model_factory_experiment_queue": {
                        "status": "PASS",
                        "experiment_count": 11,
                        "ready_experiment_count": 9,
                        "waiting_for_human_review_count": 2,
                        "top_experiment_id": "paper_smoke_evidence_review__small_account_growth_paper",
                        "order_submission_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                }
            if path_text.endswith("model_factory_experiment_queue_latest.json"):
                return {
                    "status": "PASS",
                    "summary": {
                        "experiment_count": 11,
                        "ready_experiment_count": 9,
                        "waiting_for_human_review_count": 2,
                        "top_experiment_id": "paper_smoke_evidence_review__small_account_growth_paper",
                    },
                    "unsafe_experiment_ids": [],
                    "no_order_assertions": no_order,
                }
            if path_text.endswith("experiment_queue.json"):
                return {
                    "schema_version": "1.1",
                    "status": "PASS",
                    "summary": {"experiment_count": 11, "ready_experiment_count": 9},
                    "no_order_assertions": no_order,
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary(
                [{"script": "build_model_factory_experiment_queue.py", "returncode": 0, "ok": True}]
            )

        self.assertEqual(report["status"], "PASS", report["verifier_checks"])
        self.assertTrue(report["verifier_checks"]["public_experiment_queue_surface_ok"])
        self.assertTrue(report["public_export_checks"]["model_factory_experiment_queue_surface_safe"])
        self.assertEqual(report["public_export_checks"]["model_factory_experiment_queue_experiment_count"], 11)
        self.assertEqual(report["public_export_checks"]["model_factory_experiment_queue_ready_count"], 9)

    def test_summary_requires_safe_public_gatekeeper_review_phrase_packet_surface(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 87.5,
                        "dominant_blocking_dimensions": ["paper_cycles"],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "ETA_AVAILABLE",
                        "slowest_gate_dimension": "paper_cycles",
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "gatekeeper_review_decision_phrase_packet": {
                        "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                        "ready_for_human_gatekeeper_review": True,
                        "ready_phrase_count": 1,
                        "blocked_decision_count": 0,
                        "next_exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                        "ready_phrases": [
                            {
                                "decision_id": "bithumb_current_actionable_family_parameter_repair_review",
                                "exact_phrase_to_record": "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY",
                            }
                        ],
                        "promotion_allowed_by_this_packet": False,
                        "shadow_registration_allowed_by_this_packet": False,
                        "paper_enabled_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "order_submission_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "gatekeeper_pending_decision_board": {
                        "items": [
                            {
                                "decision_id": "bithumb_current_actionable_family_parameter_repair_review",
                                "exact_phrase_to_record": "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY",
                            }
                        ]
                    },
                    "bithumb_family_parameter_repair_review": {
                        "decision_id": "bithumb_current_actionable_family_parameter_repair_review",
                        "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                        "lane": "bithumb_1d",
                        "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                        "ready_for_human_review": True,
                        "exact_phrase_to_record": "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY",
                        "market": "KRW-POLA",
                        "oos_fold_count": 3,
                        "oos_pass_fold_count": 2,
                        "oos_total_trade_count": 17,
                        "robustness_status": "ROBUSTNESS_STRESS_PASS",
                        "robustness_case_count": 7,
                        "robustness_pass_count": 4,
                        "robustness_cost_pass_count": 2,
                        "repair_oos_pass_candidate_count": 3,
                        "repair_robustness_pass_candidate_count": 1,
                        "promotion_allowed_by_this_review": False,
                        "live_allowed_by_this_review": False,
                        "order_submission_allowed_by_this_review": False,
                        "real_orders_allowed_by_this_review": False,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 2},
                }
            if str(path).endswith("gatekeeper_pending_decision_board_latest.json"):
                return {
                    "items": [
                        {
                            "decision_id": "bithumb_current_actionable_family_parameter_repair_review",
                            "exact_phrase_to_record": "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY",
                        }
                    ]
                }
            if str(path).endswith("bithumb_current_actionable_family_parameter_repair_gatekeeper_packet_latest.json"):
                return {
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                    "exact_phrase_to_record": "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY",
                    "evidence_summary": {
                        "market": "KRW-POLA",
                        "oos_fold_count": 3,
                        "oos_pass_fold_count": 2,
                        "oos_total_trade_count": 17,
                        "robustness_status": "ROBUSTNESS_STRESS_PASS",
                        "robustness_case_count": 7,
                        "robustness_pass_count": 4,
                        "robustness_cost_pass_count": 2,
                        "repair_oos_pass_candidate_count": 3,
                        "repair_robustness_pass_candidate_count": 1,
                    },
                    "no_order_assertions": {
                        "promotion_allowed_by_this_packet": False,
                        "shadow_registration_allowed_by_this_packet": False,
                        "paper_enabled_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "broker_submit_allowed_by_this_packet": False,
                        "private_submit_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                }
            if str(path).endswith("bithumb_current_actionable_family_parameter_repair_latest.json"):
                return {
                    "status": "FAMILY_PARAMETER_REPAIR_ROBUSTNESS_PASS",
                    "best_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                    "best_candidate_market": "KRW-POLA",
                    "evaluated_trial_count": 10,
                    "oos_pass_candidate_count": 3,
                    "robustness_pass_candidate_count": 1,
                    "no_order_assertions": {
                        "promotion_allowed_by_this_report": False,
                        "paper_enabled_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "broker_submit_allowed_by_this_report": False,
                        "private_submit_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                }
            if str(path).endswith("pull_through_board_latest.json"):
                return {
                    "gatekeeper_action_packet": {
                        "bithumb_current_actionable_family_parameter_repair_review": {
                            "status": "FAMILY_PARAMETER_REPAIR_ROBUSTNESS_PASS",
                            "ready_for_gatekeeper_review": True,
                            "best_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                            "best_candidate_market": "KRW-POLA",
                            "evaluated_trial_count": 10,
                            "oos_pass_candidate_count": 3,
                            "robustness_pass_candidate_count": 1,
                            "broker_submit_allowed_by_this_report": False,
                            "real_orders_allowed_by_this_report": False,
                        },
                        "bithumb_current_actionable_family_parameter_repair_gatekeeper_packet": {
                            "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                            "ready_for_human_gatekeeper_review": True,
                            "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                            "market": "KRW-POLA",
                            "oos_fold_count": 3,
                            "oos_pass_fold_count": 2,
                            "oos_total_trade_count": 17,
                            "robustness_pass_count": 4,
                            "robustness_case_count": 7,
                            "robustness_cost_pass_count": 2,
                            "shadow_registration_allowed_by_this_report": False,
                            "broker_submit_allowed_by_this_report": False,
                            "real_orders_allowed_by_this_report": False,
                        },
                    }
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "PASS", report["verifier_checks"])
        self.assertTrue(report["public_export_checks"]["gatekeeper_review_phrase_packet_surface_present"])
        self.assertTrue(report["public_export_checks"]["gatekeeper_review_phrase_packet_surface_safe"])
        self.assertEqual(
            report["public_export_checks"]["gatekeeper_review_phrase_packet_next_exact_phrase"],
            "REVIEW_PAPER_SMOKE_ONLY",
        )
        self.assertTrue(report["public_export_checks"]["family_parameter_repair_phrase_surface_safe"])
        self.assertTrue(report["verifier_checks"]["family_parameter_repair_evidence_ok"])
        self.assertTrue(report["verifier_checks"]["board_family_parameter_repair_evidence_ok"])
        self.assertTrue(report["verifier_checks"]["public_family_parameter_repair_evidence_ok"])
        self.assertTrue(report["public_export_checks"]["family_parameter_repair_evidence_surface_safe"])
        self.assertTrue(report["public_export_checks"]["family_parameter_repair_public_evidence_surface_safe"])
        self.assertTrue(report["pull_through_board_checks"]["family_parameter_repair_evidence_surface_safe"])
        self.assertEqual(
            report["public_export_checks"]["family_parameter_repair_packet_exact_phrase"],
            "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY",
        )
        self.assertEqual(
            report["bithumb_family_parameter_repair_evidence"]["candidate_id"],
            "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
        )

    def test_summary_requires_safe_public_goal_unblock_summary_surface(self) -> None:
        def fake_read_json(path, default):
            path_text = str(path)
            if path_text.endswith("paper_evidence_progress_delta_latest.json"):
                return {
                    "current": {
                        "paper_cycles_completed": 252,
                        "paper_cycles_target": 288,
                        "paper_cycles_missing": 36,
                        "non_flat_signal_count": 54,
                        "non_flat_signals_missing": 0,
                        "executable_order_count": 54,
                        "executable_orders_missing": 0,
                    }
                }
            if path_text.endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 87.5,
                        "dominant_blocking_dimensions": ["paper_cycles"],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "ETA_AVAILABLE",
                        "slowest_gate_dimension": "paper_cycles",
                        "event_stall_status": "NO_EVENT_STALL",
                        "stall_severity": "NONE",
                        "non_flat_hours_since_last_increase": 0,
                        "executable_hours_since_last_increase": 0,
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "paper_event_stall_triage": {
                        "status": "PASS",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "order_submission_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                        "counts_as_extended_paper_promotion": False,
                        "counts_as_live_readiness": False,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 2},
                    "goal_remaining_blockers": {
                        "status": "BLOCKED",
                        "blocker_count": 2,
                        "codex_unblockable_now_count": 0,
                        "approval_required_count": 1,
                        "operator_input_blocker_count": 2,
                        "blockers": [
                            {
                                "deliverable": "two_axis_model_factory_scope",
                                "codex_can_unblock_without_operator": False,
                                "required_operator_action": "Set KIS environment values outside Codex.",
                            },
                            {
                                "deliverable": "current_paper_activation_gate",
                                "codex_can_unblock_without_operator": False,
                                "approval_required_before_codex_action": True,
                                "required_operator_action": (
                                    "Either wait for already-approved paper-cycle evidence to advance, or provide approval."
                                ),
                                "codex_safe_next_action": "Keep reporting and monitoring only.",
                            },
                        ],
                    },
                    "goal_unblock_verification_packet": {
                        "status": "WAITING_FOR_BLOCKER_CLEARANCE",
                        "blocker_count": 2,
                        "unblock_summary": {
                            "kis_missing_requirements": [
                                "app_key",
                                "app_secret",
                                "account_no",
                                "account_product_code",
                            ],
                            "paper_cycles_completed": 252,
                            "paper_cycles_target": 288,
                            "paper_cycles_missing": 36,
                            "non_flat_signal_count": 54,
                            "executable_order_count": 54,
                            "historical_replay_counts_as_promotion_evidence": False,
                            "paper_cycle_source": {
                                "cycle_source": "paper_autotrade_loop_latest.cycles_completed",
                                "paper_loop_cycles_completed": 252,
                                "gatekeeper_refresh_does_not_increment_this_counter": True,
                            },
                        },
                        "verification_steps": [
                            {
                                "blocker": "two_axis_model_factory_scope",
                                "current_status": {"kis_environment_readiness_status": "BLOCKED"},
                            },
                            {
                                "blocker": "current_paper_activation_gate",
                                "current_status": {
                                    "paper_cycles_completed": 252,
                                    "paper_cycles_target": 288,
                                    "paper_cycle_source": {
                                        "cycle_source": "paper_autotrade_loop_latest.cycles_completed",
                                        "paper_loop_cycles_completed": 252,
                                    },
                                },
                            },
                        ],
                        "completion_recheck_commands": [
                            "python .\\build_goal_model_factory_requirement_checklist.py"
                        ],
                    },
                }
            if path_text.endswith("paper_evidence_gap_diagnostic_latest.json"):
                return {
                    "status": "COLLECT_EVIDENCE",
                    "gap_summary": {},
                    "why_not_ready": {},
                    "regression_summary": {},
                    "safety": {
                        "live_enabled": False,
                        "broker_submit_allowed": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                        "promotion_allowed": False,
                        "live_allowed": False,
                    },
                }
            if path_text.endswith("paper_evidence_event_stall_triage_latest.json"):
                return {
                    "status": "PASS",
                    "review_ready": True,
                    "blockers": [],
                    "permissions": {
                        "promotion_allowed_by_this_report": False,
                        "extended_paper_promotion_allowed_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "broker_submit_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                    "safety": {"order_paths_allowed_by_triage": False},
                }
            if path_text.endswith("goal_model_factory_completion_audit_latest.json"):
                return {
                    "status": "NOT_COMPLETE",
                    "completion_blocker_summary": {
                        "paper_evidence_remaining": {
                            "pace_summary": {
                                "eta_status": "ETA_AVAILABLE",
                                "slowest_gate_dimension": "paper_cycles",
                            },
                            "event_stall_summary": {"stall_severity": "NONE"},
                        }
                    },
                }
            if path_text.endswith("pull_through_board_latest.json"):
                return {
                    "gatekeeper_action_packet": {
                        "paper_evidence_pace_summary": {
                            "eta_status": "ETA_AVAILABLE",
                            "slowest_gate_dimension": "paper_cycles",
                        },
                        "paper_evidence_event_stall_summary": {
                            "event_stall_status": "NO_EVENT_STALL",
                            "stall_severity": "NONE",
                        },
                        "paper_evidence_event_stall_triage": {
                            "status": "PASS",
                            "review_ready": True,
                            "blocker_count": 0,
                            "path": "reports/model_factory/paper_evidence_event_stall_triage_latest.json",
                            "promotion_allowed_by_this_report": False,
                            "live_allowed_by_this_report": False,
                            "broker_submit_allowed_by_this_report": False,
                            "real_orders_allowed_by_this_report": False,
                            "counts_as_extended_paper_promotion": False,
                            "counts_as_live_readiness": False,
                        },
                        "goal_model_factory_unblock_verification_packet": {
                            "status": "WAITING_FOR_BLOCKER_CLEARANCE",
                            "blocker_count": 2,
                            "paper_cycles_completed": 252,
                            "paper_cycles_target": 288,
                            "paper_cycles_missing": 36,
                            "non_flat_signal_count": 54,
                            "executable_order_count": 54,
                            "historical_replay_counts_as_promotion_evidence": False,
                            "surface_safe": True,
                            "broker_submit_allowed_by_this_packet": False,
                            "private_submit_allowed_by_this_packet": False,
                            "real_orders_allowed_by_this_packet": False,
                            "real_orders": 0,
                        },
                    }
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertTrue(report["verifier_checks"]["public_unblock_summary_ok"])
        self.assertTrue(report["verifier_checks"]["public_remaining_blocker_ownership_ok"])
        self.assertTrue(report["verifier_checks"]["board_unblock_summary_ok"])
        self.assertTrue(report["public_export_checks"]["goal_unblock_summary_surface_safe"])
        self.assertTrue(report["pull_through_board_checks"]["goal_unblock_summary_surface_safe"])
        self.assertEqual(report["public_export_checks"]["goal_unblock_paper_cycles_completed"], 252)
        self.assertEqual(report["pull_through_board_checks"]["goal_unblock_paper_cycles_completed"], 252)
        self.assertEqual(report["public_export_checks"]["goal_unblock_paper_cycles_target"], 288)
        self.assertEqual(report["public_export_checks"]["goal_unblock_non_flat_signal_count"], 54)
        self.assertEqual(report["public_export_checks"]["goal_unblock_executable_order_count"], 54)
        self.assertTrue(report["public_export_checks"]["goal_unblock_verification_steps_have_current_status"])
        self.assertTrue(report["public_export_checks"]["goal_unblock_cycle_source_safe"])
        self.assertEqual(
            report["public_export_checks"]["goal_unblock_cycle_source"],
            "paper_autotrade_loop_latest.cycles_completed",
        )
        self.assertTrue(report["public_export_checks"]["goal_remaining_blocker_ownership_surface_safe"])
        self.assertEqual(report["public_export_checks"]["goal_remaining_blocker_count"], 2)
        self.assertEqual(report["public_export_checks"]["goal_remaining_codex_unblockable_now_count"], 0)
        self.assertEqual(report["public_export_checks"]["goal_remaining_approval_required_count"], 1)
        self.assertEqual(report["public_export_checks"]["goal_remaining_operator_input_blocker_count"], 2)
        self.assertFalse(
            report["public_export_checks"]["goal_unblock_historical_replay_counts_as_promotion_evidence"]
        )

    def test_summary_rejects_public_remaining_blocker_ownership_leaking_approval_phrase(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 87.5,
                        "dominant_blocking_dimensions": ["paper_cycles"],
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 2},
                    "goal_remaining_blockers": {
                        "status": "BLOCKED",
                        "blocker_count": 1,
                        "codex_unblockable_now_count": 0,
                        "approval_required_count": 0,
                        "operator_input_blocker_count": 1,
                        "blockers": [
                            {
                                "deliverable": "current_paper_activation_gate",
                                "codex_can_unblock_without_operator": False,
                                "required_operator_action": "Use PAPER APPROVE small_account_growth_paper.",
                            }
                        ],
                    },
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertFalse(report["verifier_checks"]["public_remaining_blocker_ownership_ok"])
        self.assertFalse(report["public_export_checks"]["goal_remaining_blocker_ownership_surface_safe"])

    def test_summary_rejects_public_goal_unblock_local_cycle_source_leak(self) -> None:
        def fake_read_json(path, default):
            path_text = str(path)
            if path_text.endswith("paper_evidence_progress_delta_latest.json"):
                return {
                    "current": {
                        "paper_cycles_completed": 252,
                        "paper_cycles_target": 288,
                        "paper_cycles_missing": 36,
                        "non_flat_signal_count": 54,
                        "executable_order_count": 54,
                    }
                }
            if path_text.endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 87.5,
                        "dominant_blocking_dimensions": ["paper_cycles"],
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 2},
                    "goal_unblock_verification_packet": {
                        "status": "WAITING_FOR_BLOCKER_CLEARANCE",
                        "blocker_count": 2,
                        "unblock_summary": {
                            "kis_missing_requirements": ["app_key"],
                            "paper_cycles_completed": 252,
                            "paper_cycles_target": 288,
                            "paper_cycles_missing": 36,
                            "non_flat_signal_count": 54,
                            "executable_order_count": 54,
                            "historical_replay_counts_as_promotion_evidence": False,
                            "paper_cycle_source": {
                                "source": r"C:\AI\overnight_runs\paper_autotrade_loop_latest.json",
                                "cycle_source": "paper_autotrade_loop_latest.cycles_completed",
                                "gatekeeper_refresh_does_not_increment_this_counter": True,
                            },
                        },
                        "verification_steps": [
                            {
                                "blocker": "two_axis_model_factory_scope",
                                "current_status": {"kis_environment_readiness_status": "BLOCKED"},
                            },
                            {
                                "blocker": "current_paper_activation_gate",
                                "current_status": {
                                    "paper_cycles_completed": 252,
                                    "paper_cycles_target": 288,
                                    "paper_cycle_source": {
                                        "cycle_source": "paper_autotrade_loop_latest.cycles_completed"
                                    },
                                },
                            },
                        ],
                        "completion_recheck_commands": [
                            "python .\\build_goal_model_factory_requirement_checklist.py"
                        ],
                    },
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertFalse(report["verifier_checks"]["public_unblock_summary_ok"])
        self.assertFalse(report["public_export_checks"]["goal_unblock_summary_surface_safe"])
        self.assertFalse(report["public_export_checks"]["goal_unblock_cycle_source_safe"])

    def test_summary_fails_when_checklist_has_unexpected_incomplete_requirement(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": [],
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 2},
                }
            if str(path).endswith("goal_model_factory_requirement_checklist_latest.json"):
                return {
                    "missing_or_incomplete": [
                        {"requirement": "Keep a file-backed progress record for each iteration"},
                        {"requirement": "Accumulate enough live-like paper promotion evidence before completion"},
                    ]
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["goal_requirement_checklist"]["unexpected_incomplete_count"], 1)
        self.assertIn(
            "Keep a file-backed progress record for each iteration",
            report["goal_requirement_checklist"]["unexpected_incomplete_requirements"],
        )

    def test_summary_accepts_family_phrase_surface_when_packet_is_risk_guard_blocked(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {
                        "paper_evidence_readiness_percent": 87.5,
                        "dominant_blocking_dimensions": ["paper_cycles"],
                    },
                    "paper_progress_delta": {
                        "pace_eta_status": "ETA_AVAILABLE",
                        "slowest_gate_dimension": "paper_cycles",
                    },
                    "gatekeeper_review_decision_phrase_packet": {
                        "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                        "ready_for_human_gatekeeper_review": True,
                        "ready_phrase_count": 1,
                        "blocked_decision_count": 1,
                        "next_exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                        "promotion_allowed_by_this_packet": False,
                        "shadow_registration_allowed_by_this_packet": False,
                        "paper_enabled_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "order_submission_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "gatekeeper_pending_decision_board": {
                        "items": [
                            {
                                "decision_id": "bithumb_current_actionable_family_parameter_repair_review",
                                "exact_phrase_to_record": "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY",
                            }
                        ]
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 2},
                }
            if str(path).endswith("realtime_risk_guard_latest.json"):
                return {"status": "WARN", "halt_count": 0}
            if str(path).endswith("gatekeeper_pending_decision_board_latest.json"):
                return {
                    "items": [
                        {
                            "decision_id": "bithumb_current_actionable_family_parameter_repair_review",
                            "exact_phrase_to_record": "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY",
                        }
                    ]
                }
            if str(path).endswith("bithumb_current_actionable_family_parameter_repair_gatekeeper_packet_latest.json"):
                return {
                    "status": "BLOCKED",
                    "blockers": ["risk_guard_hard_safety_pass"],
                    "exact_phrase_to_record": "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY",
                    "no_order_assertions": {
                        "broker_submit_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                }
            return {}

        with (
            patch.object(refresh, "read_json", side_effect=fake_read_json),
            patch.object(refresh, "public_sensitive_hits", return_value=[]),
        ):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertTrue(report["verifier_checks"]["family_review_phrase_surface_ok"])
        self.assertTrue(report["public_export_checks"]["family_parameter_repair_phrase_surface_safe"])

    def test_summary_handles_null_json_payloads(self) -> None:
        def fake_read_json(path, default):
            if str(path).endswith("public_summary.json"):
                return {
                    "paper_velocity_monitor": {"paper_evidence_readiness_percent": 40.0, "dominant_blocking_dimensions": []},
                    "paper_progress_delta": {
                        "pace_eta_status": "STALLED_ON_EVENT_EVIDENCE",
                        "slowest_gate_dimension": "non_flat_signals",
                    },
                    "paper_smoke_gatekeeper_review_packet": {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "review_ready": True,
                        "blocker_count": 0,
                        "promotion_allowed_by_this_packet": False,
                        "live_allowed_by_this_packet": False,
                        "real_orders_allowed_by_this_packet": False,
                    },
                    "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
                }
            return None

        with (patch.object(refresh, "read_json", side_effect=fake_read_json), patch.object(refresh, "public_sensitive_hits", return_value=[])):
            report = refresh.build_summary([{"script": "ok.py", "returncode": 0, "ok": True}])

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["public_export_checks"]["sensitive_hit_count"], 0)
        self.assertTrue(report["public_export_checks"]["readiness_surface_present"])
        self.assertTrue(report["public_export_checks"]["goal_requirement_checklist_surface_present"])
        self.assertTrue(report["public_export_checks"]["pace_eta_surface_present"])

    def test_read_json_reads_existing_file_and_falls_back_on_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            valid_path = Path(tmp) / "valid.json"
            invalid_path = Path(tmp) / "invalid.json"
            missing_path = Path(tmp) / "missing.json"

            valid_path.write_text('{"ok": true}', encoding="utf-8")
            invalid_path.write_text("{bad", encoding="utf-8")

            self.assertEqual(refresh.read_json(valid_path, {}), {"ok": True})
            self.assertEqual(refresh.read_json(invalid_path, {"fallback": True}), {"fallback": True})
            self.assertEqual(refresh.read_json(missing_path, {"missing": True}), {"missing": True})


if __name__ == "__main__":
    unittest.main()
