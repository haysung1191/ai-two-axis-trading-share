from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_goal_model_factory_requirement_checklist.py")
SPEC = importlib.util.spec_from_file_location("build_goal_model_factory_requirement_checklist", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
checklist = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checklist)


class GoalModelFactoryRequirementChecklistTests(unittest.TestCase):
    def test_progress_summary_separates_entry_count_from_latest_iteration_number(self) -> None:
        summary = checklist.progress_iteration_summary(
            "## 2026-05-04 Iteration 130 Result\n"
            "done\n"
            "## 2026-05-03 Iteration 79 Result\n"
            "done\n"
            "## 2026-05-03 Iteration 79 Result\n"
        )

        self.assertEqual(summary["progress_entry_count"], 3)
        self.assertEqual(summary["latest_iteration_number"], 130)
        self.assertEqual(summary["latest_iteration_heading"], "## 2026-05-04 Iteration 130 Result")

    def test_checklist_remains_not_complete_until_paper_evidence_is_ready(self) -> None:
        report = checklist.build_checklist(
            progress_text="## Iteration 1\n- status: completed\n",
            paper={
                "evidence": {
                    "paper_safety": {
                        "broker_submit_allowed": True,
                        "broker_submit_scope": "paper_only",
                        "live_enabled_flag": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                    }
                }
            },
            velocity={
                "readiness_summary": {
                    "paper_evidence_readiness_percent": 40.0,
                    "promotion_review_ready": False,
                },
                "safety": {"historical_replay_counts_as_promotion_evidence": False},
            },
            refresh={
                "status": "PASS",
                "paper_progress": {
                    "paper_cycles_completed": 153,
                    "paper_cycles_missing": 135,
                    "non_flat_signal_count": 2,
                    "non_flat_signals_missing": 3,
                    "executable_order_count": 2,
                    "executable_orders_missing": 3,
                },
                "public_export_checks": {
                    "sensitive_hit_count": 0,
                    "stale_derived_warning_count": 0,
                    "readiness_surface_present": True,
                    "gatekeeper_decision_priority_surface_safe": True,
                },
                "completion_audit_checks": {"stale_derived_warning_count": 0},
            },
            audit={"status": "NOT_COMPLETE", "completion_allowed": False},
            operational={"status": "WARN", "blockers": [], "warnings": ["KEEP_PAPER_COLLECT_EVIDENCE"]},
            risk_guard={"status": "PASS"},
            stock_queue={
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "target_count": 5,
                "ready_candidate_count": 5,
                "blocked_candidate_count": 0,
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            public_summary={"status": "PASS"},
        )

        self.assertEqual(report["status"], "NOT_COMPLETE")
        self.assertFalse(report["completion_allowed"])
        self.assertEqual(report["total_count"], 8)
        self.assertEqual(report["pass_count"], 7)
        self.assertEqual(report["incomplete_count"], 1)
        self.assertEqual(report["unexpected_incomplete_count"], 1)
        progress_item = next(
            item for item in report["items"] if item["requirement"] == "Keep a file-backed progress record for each iteration"
        )
        self.assertEqual(progress_item["evidence"]["progress_entry_count"], 1)
        self.assertEqual(progress_item["evidence"]["latest_iteration_number"], 1)
        self.assertEqual(
            report["first_incomplete_requirement"],
            "Allow pipeline pull-through via paper-smoke while extended paper/live remains blocked",
        )
        self.assertEqual(len(report["missing_or_incomplete"]), 1)
        self.assertEqual(
            report["missing_or_incomplete"][0]["requirement"],
            "Allow pipeline pull-through via paper-smoke while extended paper/live remains blocked",
        )

    def test_checklist_fails_when_progress_has_open_iteration(self) -> None:
        report = checklist.build_checklist(
            progress_text=(
                "## Iteration 1\n"
                "- note: mention `status: in_progress` in prose without opening an iteration\n"
                "- status: completed\n\n"
                "## Iteration 2\n"
                "- status: in_progress\n"
            ),
            paper={
                "evidence": {
                    "paper_safety": {
                        "broker_submit_allowed": True,
                        "broker_submit_scope": "paper_only",
                        "live_enabled_flag": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                    }
                }
            },
            velocity={
                "readiness_summary": {
                    "paper_evidence_readiness_percent": 100.0,
                    "promotion_review_ready": True,
                },
                "safety": {"historical_replay_counts_as_promotion_evidence": False},
            },
            refresh={
                "status": "PASS",
                "paper_progress": {
                    "paper_cycles_completed": 288,
                    "paper_cycles_missing": 0,
                    "non_flat_signal_count": 5,
                    "non_flat_signals_missing": 0,
                    "executable_order_count": 5,
                    "executable_orders_missing": 0,
                },
                "public_export_checks": {
                    "sensitive_hit_count": 0,
                    "stale_derived_warning_count": 0,
                    "readiness_surface_present": True,
                    "gatekeeper_decision_priority_surface_safe": True,
                },
                "completion_audit_checks": {"stale_derived_warning_count": 0},
            },
            audit={"status": "COMPLETE", "completion_allowed": True},
            operational={"status": "WARN", "blockers": [], "warnings": []},
            risk_guard={"status": "PASS"},
            stock_queue={
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "target_count": 5,
                "ready_candidate_count": 5,
                "blocked_candidate_count": 0,
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            public_summary={"status": "PASS"},
        )

        first = report["items"][0]
        self.assertEqual(first["status"], "FAIL")
        self.assertEqual(first["evidence"]["open_iteration_count"], 1)

    def test_refresh_guard_uses_step_and_subcheck_evidence_not_prior_summary_status_only(self) -> None:
        report = checklist.build_checklist(
            progress_text="## Iteration 1\n- status: completed\n",
            paper={
                "evidence": {
                    "paper_safety": {
                        "broker_submit_allowed": True,
                        "broker_submit_scope": "paper_only",
                        "live_enabled_flag": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                    }
                }
            },
            velocity={
                "readiness_summary": {
                    "paper_evidence_readiness_percent": 40.0,
                    "promotion_review_ready": False,
                },
                "safety": {"historical_replay_counts_as_promotion_evidence": False},
            },
            refresh={
                "status": "FAIL",
                "steps": [{"ok": True}, {"ok": True}],
                "paper_progress": {
                    "paper_cycles_completed": 157,
                    "paper_cycles_missing": 131,
                    "non_flat_signal_count": 2,
                    "non_flat_signals_missing": 3,
                    "executable_order_count": 2,
                    "executable_orders_missing": 3,
                },
                "public_export_checks": {
                    "sensitive_hit_count": 0,
                    "stale_derived_warning_count": 0,
                    "readiness_surface_present": True,
                    "gatekeeper_decision_priority_surface_safe": True,
                },
                "completion_audit_checks": {"stale_derived_warning_count": 0},
            },
            audit={"status": "NOT_COMPLETE", "completion_allowed": False},
            operational={"status": "WARN", "blockers": [], "warnings": ["KEEP_PAPER_COLLECT_EVIDENCE"]},
            risk_guard={"status": "PASS"},
            stock_queue={
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "target_count": 5,
                "ready_candidate_count": 5,
                "blocked_candidate_count": 0,
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            public_summary={"status": "PASS"},
        )

        refresh_item = next(item for item in report["items"] if item["requirement"] == "Maintain review-stack refresh and sanitized public export guards")
        self.assertEqual(refresh_item["status"], "PASS")
        self.assertTrue(refresh_item["evidence"]["refresh_steps_ok"])

    def test_refresh_guard_accepts_expected_blocked_steps_from_refresh_report(self) -> None:
        report = checklist.build_checklist(
            progress_text="## Iteration 1\n- status: completed\n",
            paper={
                "evidence": {
                    "paper_safety": {
                        "broker_submit_allowed": True,
                        "broker_submit_scope": "paper_only",
                        "live_enabled_flag": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                    }
                }
            },
            velocity={"safety": {"historical_replay_counts_as_promotion_evidence": False}},
            refresh={
                "status": "PASS",
                "steps": [
                    {"script": "ok.py", "ok": True},
                    {"script": "register_bithumb_current_actionable_shadow_candidate.py", "ok": False},
                ],
                "accepted_blocked_steps": [
                    {"script": "register_bithumb_current_actionable_shadow_candidate.py"}
                ],
                "public_export_checks": {
                    "sensitive_hit_count": 0,
                    "stale_derived_warning_count": 0,
                    "readiness_surface_present": True,
                    "gatekeeper_decision_priority_surface_safe": True,
                },
                "completion_audit_checks": {"stale_derived_warning_count": 0},
            },
            audit={"status": "COMPLETE", "completion_allowed": True},
            operational={"status": "WARN", "blockers": [], "warnings": []},
            risk_guard={"status": "PASS"},
            stock_queue={},
            public_summary={"status": "PASS"},
        )

        refresh_item = next(item for item in report["items"] if item["requirement"] == "Maintain review-stack refresh and sanitized public export guards")
        self.assertEqual(refresh_item["status"], "PASS")
        self.assertEqual(refresh_item["evidence"]["accepted_blocked_step_count"], 1)

    def test_refresh_guard_uses_current_public_and_audit_warnings_over_stale_prior_refresh(self) -> None:
        report = checklist.build_checklist(
            progress_text="## Iteration 1\n- status: completed\n",
            paper={
                "evidence": {
                    "paper_safety": {
                        "broker_submit_allowed": True,
                        "broker_submit_scope": "paper_only",
                        "live_enabled_flag": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                    }
                }
            },
            velocity={
                "readiness_summary": {
                    "paper_evidence_readiness_percent": 40.0,
                    "promotion_review_ready": False,
                },
                "safety": {"historical_replay_counts_as_promotion_evidence": False},
            },
            refresh={
                "status": "FAIL",
                "steps": [{"ok": True}, {"ok": True}],
                "paper_progress": {
                    "paper_cycles_completed": 163,
                    "paper_cycles_missing": 125,
                    "non_flat_signal_count": 2,
                    "non_flat_signals_missing": 3,
                    "executable_order_count": 2,
                    "executable_orders_missing": 3,
                },
                "public_export_checks": {
                    "sensitive_hit_count": 0,
                    "stale_derived_warning_count": 2,
                    "readiness_surface_present": True,
                },
                "completion_audit_checks": {"stale_derived_warning_count": 2},
            },
            audit={
                "status": "NOT_COMPLETE",
                "completion_allowed": False,
                "checks": [
                    {
                        "requirement": "Maintain file-backed progress and checkpoint record",
                        "evidence": {"operational_warnings": ["NON_PASS_STATUS:goal_requirement_checklist:NOT_COMPLETE"]},
                    }
                ],
            },
            operational={"status": "WARN", "blockers": [], "warnings": ["NON_PASS_STATUS:goal_requirement_checklist:NOT_COMPLETE"]},
            risk_guard={"status": "PASS"},
            stock_queue={
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "target_count": 5,
                "ready_candidate_count": 5,
                "blocked_candidate_count": 0,
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            public_summary={
                "status": "PASS",
                "operational_warnings": ["NON_PASS_STATUS:goal_requirement_checklist:NOT_COMPLETE"],
                "paper_velocity_monitor": {
                    "paper_evidence_readiness_percent": 40.0,
                    "dominant_blocking_dimensions": ["non_flat_signals"],
                },
                "goal_requirement_checklist": {"status": "NOT_COMPLETE", "incomplete_count": 1},
            },
        )

        refresh_item = next(
            item
            for item in report["items"]
            if item["requirement"] == "Maintain review-stack refresh and sanitized public export guards"
        )
        self.assertEqual(refresh_item["status"], "PASS")
        self.assertEqual(refresh_item["evidence"]["public_export_checks"]["stale_derived_warning_count"], 0)
        self.assertEqual(refresh_item["evidence"]["completion_audit_checks"]["stale_derived_warning_count"], 0)

    def test_stock_queue_requirement_blocks_unsafe_order_assertion(self) -> None:
        report = checklist.build_checklist(
            progress_text="## Iteration 1\n- status: completed\n",
            paper={
                "evidence": {
                    "paper_safety": {
                        "broker_submit_allowed": True,
                        "broker_submit_scope": "paper_only",
                        "live_enabled_flag": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                    }
                }
            },
            velocity={
                "readiness_summary": {
                    "paper_evidence_readiness_percent": 40.0,
                    "promotion_review_ready": False,
                },
                "safety": {"historical_replay_counts_as_promotion_evidence": False},
            },
            refresh={
                "status": "PASS",
                "steps": [{"ok": True}],
                "paper_progress": {
                    "paper_cycles_completed": 164,
                    "paper_cycles_missing": 124,
                    "non_flat_signal_count": 2,
                    "non_flat_signals_missing": 3,
                    "executable_order_count": 2,
                    "executable_orders_missing": 3,
                },
                "public_export_checks": {
                    "sensitive_hit_count": 0,
                    "stale_derived_warning_count": 0,
                    "readiness_surface_present": True,
                },
                "completion_audit_checks": {"stale_derived_warning_count": 0},
            },
            audit={"status": "NOT_COMPLETE", "completion_allowed": False},
            operational={"status": "WARN", "blockers": [], "warnings": []},
            risk_guard={"status": "PASS"},
            stock_queue={
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "target_count": 5,
                "ready_candidate_count": 5,
                "blocked_candidate_count": 0,
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": True,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            public_summary={"status": "PASS"},
        )

        stock_item = next(
            item
            for item in report["items"]
            if item["requirement"] == "Maintain stock/ETF risk-conversion queue as review-only evidence"
        )
        self.assertEqual(stock_item["status"], "FAIL")
        self.assertTrue(stock_item["evidence"]["no_order_assertions"]["broker_submit_allowed_by_this_report"])

    def test_prompt_to_artifact_checklist_maps_goal_to_real_evidence(self) -> None:
        report = checklist.build_checklist(
            progress_text="## Iteration 1\n- status: completed\n",
            paper={
                "evidence": {
                    "paper_safety": {
                        "broker_submit_allowed": True,
                        "broker_submit_scope": "paper_only",
                        "live_enabled_flag": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                    }
                }
            },
            velocity={
                "readiness_summary": {
                    "paper_evidence_readiness_percent": 81.25,
                    "promotion_review_ready": False,
                },
                "safety": {"historical_replay_counts_as_promotion_evidence": False},
            },
            refresh={
                "status": "PASS",
                "steps": [{"ok": True}],
                "paper_progress": {
                    "paper_cycles_completed": 235,
                    "paper_cycles_missing": 53,
                    "non_flat_signal_count": 6,
                    "non_flat_signals_missing": 0,
                    "executable_order_count": 6,
                    "executable_orders_missing": 0,
                },
                "public_export_checks": {
                    "sensitive_hit_count": 0,
                    "stale_derived_warning_count": 0,
                    "readiness_surface_present": True,
                    "gatekeeper_decision_priority_surface_safe": True,
                },
                "completion_audit_checks": {"stale_derived_warning_count": 0},
            },
            audit={"status": "NOT_COMPLETE", "completion_allowed": False},
            taxonomy={
                "status": "PASS",
                "current_decision": {"recommended_gatekeeper_lane": "PAPER_SMOKE_REVIEW_READY"},
            },
            operational={"status": "WARN", "blockers": [], "warnings": []},
            risk_guard={"status": "PASS", "halt_count": 0, "warn_count": 0},
            stock_queue={
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "target_count": 5,
                "ready_candidate_count": 5,
                "blocked_candidate_count": 0,
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            public_summary={
                "status": "PASS",
                "paper_velocity_monitor": {
                    "paper_evidence_readiness_percent": 81.25,
                    "dominant_blocking_dimensions": ["paper_cycles"],
                },
                "gatekeeper_decision_priority": {
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "next_decision_id": "paper_smoke_review",
                    "next_exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                    "order_submission_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            gatekeeper_decision_priority={
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "ready_decision_count": 7,
                "blocked_decision_count": 1,
                "next_decision": {
                    "decision_id": "paper_smoke_review",
                    "exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                },
            },
            activation_packet={"status": "ready_for_explicit_paper_activation", "blockers": []},
            kis_production_universe_coverage={
                "status": "BLOCKED",
                "all_four_axes_local_coverage_present": False,
                "kis_api_environment_ready": False,
            },
            bithumb_candle_availability={
                "summary": {
                    "checked_market_count": 59,
                    "total_liquidity_market_count": 447,
                    "covers_full_bithumb_krw_universe": False,
                    "coverage_ratio": 0.131991,
                    "model_ready_1d_count": 49,
                }
            },
        )

        matrix = {item["deliverable"]: item for item in report["prompt_to_artifact_checklist"]}
        self.assertEqual(report["status"], "NOT_COMPLETE")
        self.assertFalse(report["completion_allowed"])
        self.assertEqual(report["incomplete_count"], len(report["missing_or_incomplete"]))
        self.assertEqual(report["total_count"], report["pass_count"] + report["incomplete_count"])
        self.assertEqual(report["first_incomplete_requirement"], report["missing_or_incomplete"][0]["requirement"])
        self.assertTrue(report["prompt_to_artifact_completion_required"])
        self.assertEqual(matrix["two_axis_model_factory_scope"]["status"], "INCOMPLETE")
        self.assertEqual(
            matrix["two_axis_model_factory_scope"]["evidence"]["bithumb_model_ready_market_count"],
            49,
        )
        self.assertIn(
            "full Bithumb production universe coverage",
            matrix["two_axis_model_factory_scope"]["uncovered_or_incomplete"],
        )
        self.assertEqual(matrix["research_conversion_operations_lanes"]["status"], "PASS")
        self.assertEqual(matrix["current_paper_activation_gate"]["status"], "INCOMPLETE")
        self.assertEqual(
            matrix["current_paper_activation_gate"]["uncovered_or_incomplete"],
            ["extended paper cycle threshold"],
        )
        self.assertEqual(matrix["hard_safety_controls"]["status"], "PASS")
        self.assertEqual(matrix["gatekeeper_priority_review_queue"]["status"], "PASS")

        rendered = checklist.render_markdown(report)
        self.assertIn("## Prompt To Artifact Checklist", rendered)
        self.assertIn("two_axis_model_factory_scope", rendered)
        self.assertIn("extended paper cycle threshold", rendered)

    def test_prompt_to_artifact_checklist_recognizes_full_bithumb_coverage(self) -> None:
        report = checklist.build_checklist(
            progress_text="## Iteration 1\n- status: completed\n",
            paper={
                "evidence": {
                    "paper_safety": {
                        "broker_submit_allowed": True,
                        "broker_submit_scope": "paper_only",
                        "live_enabled_flag": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                    }
                }
            },
            velocity={
                "readiness_summary": {
                    "paper_evidence_readiness_percent": 83.33,
                    "promotion_review_ready": False,
                },
                "safety": {"historical_replay_counts_as_promotion_evidence": False},
            },
            refresh={
                "status": "PASS",
                "steps": [{"ok": True}],
                "paper_progress": {
                    "paper_cycles_completed": 240,
                    "paper_cycles_missing": 48,
                    "non_flat_signal_count": 8,
                    "non_flat_signals_missing": 0,
                    "executable_order_count": 8,
                    "executable_orders_missing": 0,
                },
                "public_export_checks": {
                    "sensitive_hit_count": 0,
                    "stale_derived_warning_count": 0,
                    "readiness_surface_present": True,
                    "gatekeeper_decision_priority_surface_safe": True,
                },
                "completion_audit_checks": {"stale_derived_warning_count": 0},
            },
            audit={"status": "NOT_COMPLETE", "completion_allowed": False},
            taxonomy={
                "status": "PASS",
                "current_decision": {
                    "recommended_gatekeeper_lane": "PAPER_SMOKE_REVIEW_READY",
                    "live_or_real_order_allowed": False,
                },
                "taxonomy": {"paper_smoke_evidence": {"ready": True}},
            },
            operational={"status": "WARN", "blockers": [], "warnings": []},
            risk_guard={"status": "PASS", "halt_count": 0, "warn_count": 0},
            stock_queue={
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "target_count": 5,
                "ready_candidate_count": 5,
                "blocked_candidate_count": 0,
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            public_summary={
                "status": "PASS",
                "gatekeeper_decision_priority": {
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "next_decision_id": "paper_smoke_review",
                    "next_exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                    "order_submission_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            gatekeeper_decision_priority={
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "ready_decision_count": 7,
                "blocked_decision_count": 1,
                "next_decision": {
                    "decision_id": "paper_smoke_review",
                    "exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                },
            },
            activation_packet={"status": "ready_for_explicit_paper_activation", "blockers": []},
            kis_production_universe_coverage={
                "status": "LOCAL_COVERAGE_READY_API_ENV_BLOCKED",
                "all_four_axes_local_coverage_present": True,
                "kis_api_environment_ready": False,
                "missing_kis_environment_requirements": ["KIS_APP_KEY"],
            },
            kis_environment_operator_handoff={
                "status": "WAITING_FOR_OPERATOR_ENV_VALUES",
                "missing_requirements": ["app_key"],
                "verification_commands_after_operator_sets_values": [
                    "python .\\build_kis_environment_readiness_report.py"
                ],
                "safety": {
                    "secret_values_included": False,
                    "secret_values_inspected": False,
                    "secret_values_written": False,
                    "does_set_environment": False,
                    "does_call_kis_api": False,
                    "does_enable_live": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            bithumb_candle_availability={
                "summary": {
                    "checked_market_count": 447,
                    "total_liquidity_market_count": 447,
                    "covers_full_bithumb_krw_universe": True,
                    "coverage_ratio": 1.0,
                    "model_ready_1d_count": 400,
                }
            },
        )

        matrix = {item["deliverable"]: item for item in report["prompt_to_artifact_checklist"]}
        self.assertEqual(report["unexpected_incomplete_count"], 0)
        self.assertEqual(report["unexpected_incomplete_requirements"], [])
        self.assertEqual(matrix["two_axis_model_factory_scope"]["status"], "INCOMPLETE")
        self.assertNotIn(
            "full Bithumb production universe coverage",
            matrix["two_axis_model_factory_scope"]["uncovered_or_incomplete"],
        )
        self.assertNotIn("full KIS local universe coverage", matrix["two_axis_model_factory_scope"]["uncovered_or_incomplete"])
        self.assertIn("KIS API environment and live universe validation", matrix["two_axis_model_factory_scope"]["uncovered_or_incomplete"])
        self.assertTrue(matrix["two_axis_model_factory_scope"]["evidence"]["kis_operator_handoff_ready"])
        self.assertEqual(
            matrix["two_axis_model_factory_scope"]["evidence"]["kis_operator_handoff_status"],
            "WAITING_FOR_OPERATOR_ENV_VALUES",
        )


if __name__ == "__main__":
    unittest.main()
