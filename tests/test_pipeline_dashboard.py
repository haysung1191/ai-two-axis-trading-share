from __future__ import annotations

import unittest
from unittest.mock import patch

import build_pipeline_dashboard as dashboard


class PipelineDashboardGoalChecklistTests(unittest.TestCase):
    def test_small_account_paper_policy_removes_mdd_bottleneck_from_reporting(self) -> None:
        rows = dashboard.pipeline_achievement_rows(
            [
                {
                    "lane": "kis_etfs",
                    "generated": 3,
                    "gatekeeper_intake": 3,
                    "shadow": 3,
                    "paper_evidence": 0,
                    "main_bottleneck": "MDD_TOO_HIGH",
                },
                {
                    "lane": "kis_stocks",
                    "generated": 3,
                    "gatekeeper_intake": 3,
                    "shadow": 2,
                    "paper_evidence": 1,
                    "main_bottleneck": "MDD_TOO_HIGH",
                },
            ],
            ignore_mdd=True,
        )

        self.assertEqual(rows[0]["bottleneck"], "PAPER_EVIDENCE_NEEDED_MDD_ACCEPTED")
        self.assertEqual(rows[1]["bottleneck"], "MDD_ACCEPTED_SMALL_ACCOUNT_PAPER")

    def test_paper_growth_mdd_policy_requires_paper_only_safety(self) -> None:
        self.assertTrue(
            dashboard.paper_growth_mdd_policy_active(
                {
                    "paper_enabled": True,
                    "broker_submit_allowed": True,
                    "broker_submit_scope": "paper_only",
                    "live_enabled": False,
                    "real_orders": 0,
                    "private_submit_used": False,
                }
            )
        )
        self.assertFalse(
            dashboard.paper_growth_mdd_policy_active(
                {
                    "paper_enabled": True,
                    "broker_submit_allowed": True,
                    "broker_submit_scope": "paper_only",
                    "live_enabled": True,
                    "real_orders": 0,
                    "private_submit_used": False,
                }
            )
        )

    def test_completion_override_sets_current_stage_to_100_only_when_clear(self) -> None:
        performance = {
            "current_stage_goal_pct": 88,
            "raw_current_stage_goal_pct": 88,
            "model_factory_pct": 57,
            "safety_pct": 100,
            "paper_evidence_pct": 100,
            "small_account_paper_mdd_policy": "ignored_for_paper_growth_reporting",
        }

        out = dashboard.apply_completion_override(
            performance,
            goal_completion_audit={"status": "COMPLETE", "completion_allowed": True, "incomplete_count": 0},
            goal_remaining_blockers={"status": "CLEAR", "blocker_count": 0},
            operational={"blockers": [], "actionable_warnings": []},
        )

        self.assertEqual(out["current_stage_goal_pct"], 100)
        self.assertEqual(out["raw_current_stage_goal_pct"], 88)
        self.assertEqual(out["model_factory_pct"], 100)
        self.assertEqual(out["completion_override"], "goal_completion_audit_clear_small_account_paper")

    def test_completion_override_does_not_mask_actionable_warnings(self) -> None:
        performance = {
            "current_stage_goal_pct": 88,
            "raw_current_stage_goal_pct": 88,
            "model_factory_pct": 57,
            "safety_pct": 100,
            "paper_evidence_pct": 100,
            "small_account_paper_mdd_policy": "ignored_for_paper_growth_reporting",
        }

        out = dashboard.apply_completion_override(
            performance,
            goal_completion_audit={"status": "COMPLETE", "completion_allowed": True, "incomplete_count": 0},
            goal_remaining_blockers={"status": "CLEAR", "blocker_count": 0},
            operational={"blockers": [], "actionable_warnings": ["STALE_DERIVED_REPORT"]},
        )

        self.assertEqual(out["current_stage_goal_pct"], 88)
        self.assertEqual(out["completion_override"], "none")

    def test_bithumb_family_diversity_failure_review_surfaces(self) -> None:
        def fake_read_json(path, default):
            text = str(path)
            if text.endswith("pull_through_board_latest.json"):
                return {
                    "status": "PASS",
                    "gatekeeper_action_packet": {
                        "bithumb_current_actionable_family_diversity_failure_review": {
                            "status": "FAMILY_DIVERSITY_FAILURE_REVIEW_READY",
                            "failure_candidate_count": 2,
                            "dominant_failure_dimension": "enough_pass_folds",
                            "recommended_research_action": "REPAIR_NON_ORCA_PASS_FOLD_COVERAGE",
                            "counts_as_paper_or_live_evidence": False,
                            "broker_submit_allowed_by_this_report": False,
                            "real_orders_allowed_by_this_report": False,
                        }
                    },
                }
            return default

        with patch.object(dashboard, "read_json", side_effect=fake_read_json):
            report = dashboard.build_report()

        failure = report["bithumb_family_diversity_failure_review"]
        self.assertEqual(failure["status"], "FAMILY_DIVERSITY_FAILURE_REVIEW_READY")
        self.assertEqual(failure["failure_candidate_count"], 2)
        self.assertEqual(failure["recommended_research_action"], "REPAIR_NON_ORCA_PASS_FOLD_COVERAGE")
        self.assertFalse(failure["counts_as_paper_or_live_evidence"])
        self.assertFalse(failure["broker_submit_allowed_by_this_report"])
        self.assertFalse(failure["real_orders_allowed_by_this_report"])

    def test_bithumb_non_orca_family_pass_fold_repair_spec_surfaces(self) -> None:
        def fake_read_json(path, default):
            text = str(path)
            if text.endswith("pull_through_board_latest.json"):
                return {
                    "status": "PASS",
                    "gatekeeper_action_packet": {
                        "bithumb_non_orca_family_pass_fold_repair_spec": {
                            "status": "READY_FOR_RESEARCH_SPEC_REVIEW",
                            "ready_for_research_spec_review": True,
                            "experiment_id": "bithumb_non_orca_family_pass_fold_repair__orca",
                            "repair_target_count": 2,
                            "recommended_research_action": "REPAIR_NON_ORCA_PASS_FOLD_COVERAGE",
                            "counts_as_paper_or_live_evidence": False,
                            "broker_submit_allowed_by_this_report": False,
                            "real_orders_allowed_by_this_report": False,
                        }
                    },
                }
            return default

        with patch.object(dashboard, "read_json", side_effect=fake_read_json):
            report = dashboard.build_report()

        repair_spec = report["bithumb_non_orca_family_pass_fold_repair_spec"]
        self.assertEqual(repair_spec["status"], "READY_FOR_RESEARCH_SPEC_REVIEW")
        self.assertEqual(repair_spec["repair_target_count"], 2)
        self.assertFalse(repair_spec["counts_as_paper_or_live_evidence"])
        self.assertFalse(repair_spec["broker_submit_allowed_by_this_report"])
        self.assertFalse(repair_spec["real_orders_allowed_by_this_report"])

    def test_stock_portfolio_sleeve_review_surfaces_without_order_paths(self) -> None:
        def fake_read_json(path, default):
            text = str(path)
            if text.endswith("stock_portfolio_sleeve_review_latest.json"):
                return {
                    "status": "PORTFOLIO_SLEEVE_REVIEW_READY",
                    "ready_for_gatekeeper_review": True,
                    "sleeve_policy": {"component_count": 5, "target_component_count": 5},
                    "sleeve_metrics": {"estimated_sleeve_cagr": 0.44},
                    "components": [{"candidate_id": f"stock_{i}"} for i in range(5)],
                    "counts_as_paper_or_live_evidence": False,
                    "no_order_assertions": {
                        "promotion_allowed_by_this_report": False,
                        "paper_enabled_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "broker_submit_allowed_by_this_report": False,
                        "private_submit_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                    "next_action": "review only",
                }
            return default

        with patch.object(dashboard, "read_json", side_effect=fake_read_json):
            report = dashboard.build_report()

        sleeve = report["stock_portfolio_sleeve_review"]
        self.assertEqual(sleeve["status"], "PORTFOLIO_SLEEVE_REVIEW_READY")
        self.assertTrue(sleeve["ready_for_gatekeeper_review"])
        self.assertEqual(sleeve["component_count"], 5)
        self.assertFalse(sleeve["counts_as_paper_or_live_evidence"])
        self.assertFalse(sleeve["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertIn("stock_portfolio_sleeve_review", report["links"])

    def test_model_factory_queue_coverage_audit_surfaces(self) -> None:
        def fake_read_json(path, default):
            text = str(path)
            if text.endswith("model_factory_queue_coverage_audit_latest.json"):
                return {
                    "status": "PASS",
                    "scope": "ready_decision_to_frozen_queue_coverage_no_state_promotion_no_order_paths",
                    "summary": {
                        "ready_decision_count": 13,
                        "queue_item_count": 20,
                        "covered_ready_decision_count": 13,
                        "missing_ready_decision_count": 0,
                        "unsafe_queue_item_count": 0,
                        "unexpected_duplicate_source_decision_count": 0,
                    },
                    "missing_ready_decision_ids": [],
                    "unsafe_queue_experiment_ids": [],
                    "coverage_rows": [
                        {
                            "decision_id": "bithumb_non_orca_entry_source_rebuild_review",
                            "candidate_id": "entrysource_029",
                            "priority_score": 84,
                            "covered": True,
                            "queue_item_count": 1,
                            "queue_scopes": ["entry_source_rebuild_evidence_review_only_no_order_paths"],
                        }
                    ],
                    "no_order_assertions": {
                        "promotion_allowed_by_this_report": False,
                        "paper_enabled_by_this_report": False,
                        "live_allowed_by_this_report": False,
                        "broker_submit_allowed_by_this_report": False,
                        "private_submit_allowed_by_this_report": False,
                        "real_orders_allowed_by_this_report": False,
                    },
                    "next_action": "coverage complete",
                }
            return default

        with patch.object(dashboard, "read_json", side_effect=fake_read_json):
            report = dashboard.build_report()

        audit = report["model_factory_queue_coverage_audit"]
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["summary"]["ready_decision_count"], 13)
        self.assertEqual(audit["summary"]["missing_ready_decision_count"], 0)
        self.assertEqual(audit["coverage_rows"][0]["decision_id"], "bithumb_non_orca_entry_source_rebuild_review")
        self.assertFalse(audit["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(audit["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_model_factory_experiment_queue_top_queue_preserves_evidence_summary(self) -> None:
        def fake_read_json(path, default):
            text = str(path)
            if text.endswith("model_factory_experiment_queue_latest.json"):
                return {
                    "status": "PASS",
                    "scope": "frozen_scope_queue",
                    "summary": {"experiment_count": 1, "ready_experiment_count": 1},
                    "queue": [
                        {
                            "experiment_id": "stock_child",
                            "source_decision_id": "stock_conversion_review",
                            "candidate_id": "stock_a",
                            "repo": "momentum",
                            "lane": "conversion",
                            "experiment_type": "stock_etf_fixed_exposure_child_review",
                            "priority": "P0",
                            "priority_score": 80,
                            "queue_rank": 1,
                            "status": "READY",
                            "frozen_scope": {"scope": "risk_conversion_only_no_order_paths"},
                            "gatekeeper_review": {"blockers": []},
                            "evidence_summary": {
                                "before_cagr": 0.7,
                                "estimated_mdd": -0.199,
                                "order_paths_allowed": False,
                            },
                            "no_order_assertions": {"live_allowed_by_this_report": False},
                        }
                    ],
                }
            return default

        with patch.object(dashboard, "read_json", side_effect=fake_read_json):
            report = dashboard.build_report()

        row = report["model_factory_experiment_queue"]["top_queue"][0]
        self.assertEqual(row["evidence_summary"]["before_cagr"], 0.7)
        self.assertEqual(row["evidence_summary"]["estimated_mdd"], -0.199)
        self.assertFalse(row["evidence_summary"]["order_paths_allowed"])

    def test_btc_eth_intraday_alternate_repair_child_surfaces(self) -> None:
        def fake_read_json(path, default):
            text = str(path)
            if text.endswith("pull_through_board_latest.json"):
                return {
                    "status": "PASS",
                    "gatekeeper_action_packet": {
                        "btc_eth_intraday_robustness_repair_alternate_child_packet": {
                            "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                            "ready_for_gatekeeper_review": True,
                            "base_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                            "primary_child_candidate_id": "robustrepair_445",
                            "top_alternate_candidate_id": "robustrepair_441",
                            "alternate_pass_child_count": 11,
                            "top_alternate_child_count": 5,
                            "repair_pass_count": 42,
                            "exact_phrase_to_record": "REVIEW_BTC_ETH_INTRADAY_ALTERNATE_REPAIR_CHILDREN_ONLY",
                            "counts_as_paper_or_live_evidence": False,
                            "promotion_allowed_by_this_report": False,
                            "live_allowed_by_this_report": False,
                            "broker_submit_allowed_by_this_report": False,
                            "real_orders_allowed_by_this_report": False,
                        }
                    },
                }
            return default

        with patch.object(dashboard, "read_json", side_effect=fake_read_json):
            report = dashboard.build_report()

        alternate = report["btc_eth_intraday_robustness_repair_alternate_child"]
        self.assertEqual(alternate["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertEqual(alternate["top_alternate_candidate_id"], "robustrepair_441")
        self.assertEqual(alternate["alternate_pass_child_count"], 11)
        self.assertFalse(alternate["counts_as_paper_or_live_evidence"])
        self.assertFalse(alternate["broker_submit_allowed_by_this_report"])
        self.assertFalse(alternate["real_orders_allowed_by_this_report"])

    def test_goal_requirement_checklist_preserves_source_count_semantics(self) -> None:
        def fake_read_json(path, default):
            text = str(path)
            if text.endswith("goal_model_factory_requirement_checklist_latest.json"):
                return {
                    "status": "NOT_COMPLETE",
                    "completion_allowed": False,
                    "total_count": 9,
                    "pass_count": 7,
                    "incomplete_count": 2,
                    "unexpected_incomplete_count": 0,
                    "unexpected_incomplete_requirements": [],
                    "items": [
                        {
                            "requirement": "Keep a file-backed progress record for each iteration",
                            "status": "PASS",
                            "evidence": {
                                "progress_entry_count": 155,
                                "latest_iteration_number": 131,
                                "latest_iteration_heading": "## 2026-05-04 Iteration 131 Result",
                                "open_iteration_count": 0,
                            },
                        }
                    ],
                    "missing_or_incomplete": [
                        {"requirement": "Prompt-to-artifact deliverable: two_axis_model_factory_scope"},
                        {"requirement": "Prompt-to-artifact deliverable: current_paper_activation_gate"},
                    ],
                }
            if text.endswith("goal_model_factory_remaining_blockers_latest.json"):
                return {"status": "BLOCKED", "blocker_count": 2}
            return default

        with patch.object(dashboard, "read_json", side_effect=fake_read_json):
            report = dashboard.build_report()

        checklist = report["goal_requirement_checklist"]
        self.assertEqual(checklist["total_count"], 9)
        self.assertEqual(checklist["pass_count"], 7)
        self.assertEqual(checklist["incomplete_count"], 2)
        self.assertEqual(checklist["unexpected_incomplete_count"], 0)
        self.assertEqual(checklist["unexpected_incomplete_requirements"], [])
        self.assertEqual(checklist["progress"]["progress_entry_count"], 155)
        self.assertEqual(checklist["progress"]["latest_iteration_number"], 131)
        self.assertEqual(checklist["progress"]["open_iteration_count"], 0)


if __name__ == "__main__":
    unittest.main()
