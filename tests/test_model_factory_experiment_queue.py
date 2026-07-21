from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_model_factory_experiment_queue.py")
SPEC = importlib.util.spec_from_file_location("build_model_factory_experiment_queue", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
queue = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(queue)


class ModelFactoryExperimentQueueTests(unittest.TestCase):
    def test_builds_frozen_scope_queue_from_ready_decisions_and_stock_children(self) -> None:
        priority = {
            "ready_decisions": [
                {
                    "decision_id": "paper_smoke_review",
                    "candidate_id": "small_account_growth_paper",
                    "status": "READY_FOR_GATEKEEPER_REVIEW",
                    "ready_for_human_review": True,
                    "priority_score": 100,
                    "exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                    "review_only_effect": "review only",
                    "blockers": [],
                    "evidence_summary": {"paper_cycles_completed": 252},
                },
                {
                    "decision_id": "stock_conversion_review",
                    "candidate_id": "stock_aggressive__a",
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "ready_for_human_review": True,
                    "priority_score": 80,
                    "exact_phrase_to_record": "REVIEW_CONVERSION_EVIDENCE_ONLY",
                    "review_only_effect": "review only",
                    "blockers": [],
                    "evidence_summary": {"estimated_cagr": 0.45},
                },
                {
                    "decision_id": "stock_portfolio_sleeve_review",
                    "candidate_id": "stock_etf_top5_equal_weight_sleeve",
                    "status": "PORTFOLIO_SLEEVE_REVIEW_READY",
                    "ready_for_human_review": True,
                    "priority_score": 82,
                    "exact_phrase_to_record": "REVIEW_STOCK_PORTFOLIO_SLEEVE_EVIDENCE_ONLY",
                    "review_only_effect": "review only",
                    "blockers": [],
                    "evidence_summary": {"component_count": 5},
                },
                {
                    "decision_id": "bithumb_non_orca_entry_source_rebuild_review",
                    "candidate_id": "pola_entrysource_029",
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "ready_for_human_review": True,
                    "priority_score": 84,
                    "exact_phrase_to_record": "REVIEW_NON_ORCA_ENTRY_SOURCE_REBUILD_EVIDENCE_ONLY",
                    "review_only_effect": "review only",
                    "blockers": [],
                    "evidence_summary": {
                        "estimated_cagr": 1.79,
                        "estimated_mdd": -0.199,
                        "oos_pass_fold_count": 3,
                        "robustness_pass_count": 7,
                        "counts_as_paper_or_live_evidence": False,
                    },
                },
                {
                    "decision_id": "bithumb_non_orca_entry_source_alternate_child_review",
                    "candidate_id": "pola_entrysource_032",
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "ready_for_human_review": True,
                    "priority_score": 83,
                    "exact_phrase_to_record": "REVIEW_NON_ORCA_ENTRY_SOURCE_ALTERNATE_CHILDREN_ONLY",
                    "review_only_effect": "review only",
                    "blockers": [],
                    "evidence_summary": {
                        "primary_child_candidate_id": "pola_entrysource_029",
                        "top_alternate_candidate_id": "pola_entrysource_032",
                        "alternate_pass_child_count": 14,
                        "counts_as_paper_or_live_evidence": False,
                    },
                },
                {
                    "decision_id": "btc_eth_intraday_robustness_repair_alternate_child_review",
                    "candidate_id": "repair_441",
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "ready_for_human_review": True,
                    "priority_score": 89,
                    "exact_phrase_to_record": "REVIEW_BTC_ETH_INTRADAY_ALTERNATE_REPAIR_CHILDREN_ONLY",
                    "review_only_effect": "review only",
                    "blockers": [],
                    "evidence_summary": {
                        "alternate_pass_child_count": 41,
                        "counts_as_paper_or_live_evidence": False,
                    },
                },
                {
                    "decision_id": "bithumb_current_actionable_dependency_relief_review",
                    "candidate_id": "pola_sweep1355",
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "ready_for_human_review": True,
                    "priority_score": 82,
                    "exact_phrase_to_record": "REVIEW_DEPENDENCY_RELIEF_EVIDENCE_ONLY",
                    "review_only_effect": "review only",
                    "blockers": [],
                    "evidence_summary": {"sweep1354_dependency_reduced_by_review_evidence": True},
                },
                {
                    "decision_id": "btc_eth_intraday_low_turnover_signal_rebuild_review",
                    "candidate_id": "btc_eth_low_turnover_sweep080",
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "ready_for_human_review": True,
                    "priority_score": 77,
                    "exact_phrase_to_record": "REVIEW_BTC_ETH_INTRADAY_LOW_TURNOVER_REBUILD_ONLY",
                    "review_only_effect": "review only",
                    "blockers": [],
                    "evidence_summary": {
                        "best_cost_pass_count": 2,
                        "counts_as_paper_or_live_evidence": False,
                        "followup_support": {
                            "followup_status": "LOW_TURNOVER_FOLLOWUP_SWEEP_PASS",
                            "followup_safe": True,
                            "followup_sibling_pass_count": 5,
                            "followup_best_candidate_id": "btc_eth_low_turnover_sweep080_followup159",
                            "followup_counts_as_paper_or_live_evidence": False,
                        },
                    },
                },
                {
                    "decision_id": "btc_eth_intraday_low_turnover_followup_review",
                    "candidate_id": "btc_eth_low_turnover_sweep080_followup159",
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "ready_for_human_review": True,
                    "priority_score": 86,
                    "exact_phrase_to_record": "REVIEW_BTC_ETH_INTRADAY_LOW_TURNOVER_FOLLOWUP_ONLY",
                    "review_only_effect": "review only",
                    "blockers": [],
                    "evidence_summary": {
                        "sibling_pass_count": 5,
                        "best_cost_pass_count": 2,
                        "counts_as_paper_or_live_evidence": False,
                    },
                },
                {
                    "decision_id": "bithumb_current_actionable_orca_oos_family_review",
                    "candidate_id": "orca_sweep1507",
                    "status": "ORCA_OOS_FAMILY_REVIEW_READY",
                    "ready_for_human_review": True,
                    "priority_score": 83,
                    "exact_phrase_to_record": "REVIEW_ORCA_OOS_FAMILY_EVIDENCE_ONLY",
                    "review_only_effect": "review only",
                    "blockers": [],
                    "evidence_summary": {"oos_pass_candidate_count": 6},
                },
                {
                    "decision_id": "bithumb_research_hold_triage_review",
                    "candidate_id": "bithumb_research_hold_backtest_under_bar_batch",
                    "status": "BITHUMB_RESEARCH_HOLD_TRIAGE_REVIEW_READY",
                    "ready_for_human_review": True,
                    "priority_score": 70,
                    "exact_phrase_to_record": "REVIEW_BITHUMB_RESEARCH_HOLD_TRIAGE_ONLY",
                    "review_only_effect": "review only",
                    "blockers": [],
                    "evidence_summary": {
                        "research_hold_count": 3,
                        "recommended_action": "ARCHIVE_OR_REQUIRE_STRONGER_FROZEN_HYPOTHESIS",
                        "counts_as_paper_or_live_evidence": False,
                    },
                },
                {
                    "decision_id": "bithumb_non_orca_widened_repair_stop_condition_review",
                    "candidate_id": "bio_widenedrepair_070",
                    "status": "NON_ORCA_WIDENED_REPAIR_STOP_CONDITION_READY",
                    "ready_for_human_review": True,
                    "priority_score": 65,
                    "exact_phrase_to_record": "REVIEW_NON_ORCA_WIDENED_STOP_CONDITION_ONLY",
                    "review_only_effect": "review only",
                    "blockers": [],
                    "evidence_summary": {"recommended_next_research_action": "REBUILD_NON_ORCA_ENTRY_FAMILY_OR_SOURCE_DATA_EVIDENCE"},
                },
                {
                    "decision_id": "bithumb_current_actionable_shadow_review",
                    "candidate_id": "orca_sweep1507",
                    "status": "INVALID_HUMAN_GATEKEEPER_DECISION",
                    "ready_for_human_review": True,
                    "priority_score": 60,
                    "exact_phrase_to_record": "APPROVE_SHADOW_REVIEW_ONLY",
                    "review_only_effect": "review only",
                    "blockers": ["HUMAN_GATEKEEPER_DECISION_CANDIDATE_MISMATCH"],
                    "evidence_summary": {"estimated_cagr": 1.39},
                },
                {
                    "decision_id": "stock_portfolio_sleeve_sensitivity_review",
                    "candidate_id": "stock_etf_top5_sleeve_sensitivity",
                    "status": "PORTFOLIO_SLEEVE_SENSITIVITY_REVIEW_READY",
                    "ready_for_human_review": True,
                    "priority_score": 75,
                    "exact_phrase_to_record": "REVIEW_STOCK_PORTFOLIO_SLEEVE_SENSITIVITY_EVIDENCE_ONLY",
                    "review_only_effect": "review only",
                    "blockers": [],
                    "evidence_summary": {"scenario_count": 5, "viable_scenario_count": 4},
                },
            ]
        }
        stock = {
            "status": "READY_FOR_GATEKEEPER_REVIEW",
            "no_order_assertions": dict(queue.NO_ORDER_ASSERTIONS),
            "queue": [
                {
                    "candidate_id": "stock_aggressive__a",
                    "safe_experiment_scope": "risk_conversion_only_no_order_paths",
                    "order_paths_allowed": False,
                    "broker_submit_allowed": False,
                    "live_enabled": False,
                    "private_submit_allowed": False,
                    "real_orders_allowed": False,
                    "proposed_conversion": {"fixed_exposure_cap": 0.65},
                    "before": {"cagr": 0.7},
                }
            ],
        }
        pull = {
            "status": "PASS",
            "model_factory_metrics": {"promotion_pull_through_rate": 0.5},
            "gatekeeper_action_packet": {
                "bithumb_current_actionable_orca_repair_seed_packet": {
                    "status": "ORCA_REPAIR_SEED_PACKET_READY",
                    "ready_for_research_sweep": True,
                    "base_candidate_id": "orca_sweep1507",
                    "market": "KRW-ORCA",
                    "near_miss_candidate_count": 12,
                    "proposed_seed_count": 3,
                    "top_near_miss_candidate_id": "orca_child",
                    "top_seed_id": "orca_mdd_compression_stop04_hold2_tp12",
                    "counts_as_paper_or_live_evidence": False,
                },
                "bithumb_current_actionable_family_diversity_failure_review": {
                    "status": "FAMILY_DIVERSITY_FAILURE_REVIEW_READY",
                    "ready_for_gatekeeper_review": True,
                    "family_diversity_status": "FAMILY_DIVERSITY_ITERATE",
                    "current_oos_candidate_id": "orca_sweep1507",
                    "current_oos_market": "KRW-ORCA",
                    "evaluated_candidate_count": 2,
                    "failure_candidate_count": 2,
                    "dominant_failure_dimension": "enough_pass_folds",
                    "failure_dimension_counts": {"enough_pass_folds": 2},
                    "recommended_research_action": "REPAIR_NON_ORCA_PASS_FOLD_COVERAGE",
                    "counts_as_paper_or_live_evidence": False,
                    "promotion_allowed_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                }
            },
        }
        report = queue.build_report(priority, stock, pull)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["summary"]["experiment_count"], 17)
        self.assertEqual(report["summary"]["ready_experiment_count"], 16)
        self.assertEqual(report["queue"][0]["candidate_id"], "small_account_growth_paper")
        self.assertTrue(all(row["requires_frozen_scope"] for row in report["queue"]))
        self.assertTrue(all(row["no_order_assertions"] == queue.NO_ORDER_ASSERTIONS for row in report["queue"]))
        self.assertEqual(report["summary"]["lane_counts"]["conversion"], 8)
        self.assertEqual(report["summary"]["lane_counts"]["validation"], 5)
        self.assertEqual(report["summary"]["lane_counts"]["shadow"], 1)
        entry_source = next(
            row for row in report["queue"] if row["source_decision_id"] == "bithumb_non_orca_entry_source_rebuild_review"
        )
        self.assertEqual(entry_source["experiment_type"], "bithumb_non_orca_entry_source_rebuild_review")
        self.assertEqual(entry_source["candidate_id"], "pola_entrysource_029")
        self.assertEqual(entry_source["priority"], "P0")
        self.assertEqual(
            entry_source["frozen_scope"]["scope"],
            "entry_source_rebuild_evidence_review_only_no_order_paths",
        )
        self.assertFalse(entry_source["evidence_summary"]["counts_as_paper_or_live_evidence"])
        entry_source_alternate = next(
            row
            for row in report["queue"]
            if row["source_decision_id"] == "bithumb_non_orca_entry_source_alternate_child_review"
        )
        self.assertEqual(
            entry_source_alternate["experiment_type"],
            "bithumb_non_orca_entry_source_alternate_child_review",
        )
        self.assertEqual(entry_source_alternate["candidate_id"], "pola_entrysource_032")
        self.assertEqual(
            entry_source_alternate["frozen_scope"]["scope"],
            "entry_source_alternate_child_evidence_review_only_no_order_paths",
        )
        self.assertFalse(entry_source_alternate["evidence_summary"]["counts_as_paper_or_live_evidence"])
        alternate = next(
            row
            for row in report["queue"]
            if row["source_decision_id"] == "btc_eth_intraday_robustness_repair_alternate_child_review"
        )
        self.assertEqual(alternate["experiment_type"], "btc_eth_intraday_robustness_repair_alternate_child_review")
        self.assertEqual(alternate["candidate_id"], "repair_441")
        self.assertEqual(alternate["lane"], "validation")
        self.assertEqual(
            alternate["frozen_scope"]["scope"],
            "alternate_repair_child_evidence_review_only_no_order_paths",
        )
        self.assertFalse(alternate["evidence_summary"]["counts_as_paper_or_live_evidence"])
        low_turnover = next(
            row
            for row in report["queue"]
            if row["source_decision_id"] == "btc_eth_intraday_low_turnover_signal_rebuild_review"
        )
        self.assertEqual(low_turnover["experiment_type"], "btc_eth_intraday_low_turnover_signal_rebuild_review")
        self.assertEqual(low_turnover["candidate_id"], "btc_eth_low_turnover_sweep080")
        self.assertEqual(low_turnover["lane"], "validation")
        self.assertEqual(low_turnover["priority"], "P0")
        self.assertEqual(
            low_turnover["frozen_scope"]["scope"],
            "btc_eth_intraday_low_turnover_signal_rebuild_review_only_no_order_paths",
        )
        self.assertFalse(low_turnover["evidence_summary"]["counts_as_paper_or_live_evidence"])
        self.assertEqual(low_turnover["evidence_summary"]["followup_support"]["followup_sibling_pass_count"], 5)
        self.assertEqual(
            low_turnover["evidence_summary"]["followup_support"]["followup_best_candidate_id"],
            "btc_eth_low_turnover_sweep080_followup159",
        )
        self.assertFalse(
            low_turnover["evidence_summary"]["followup_support"]["followup_counts_as_paper_or_live_evidence"]
        )
        low_turnover_followup = next(
            row
            for row in report["queue"]
            if row["source_decision_id"] == "btc_eth_intraday_low_turnover_followup_review"
        )
        self.assertEqual(low_turnover_followup["experiment_type"], "btc_eth_intraday_low_turnover_followup_review")
        self.assertEqual(low_turnover_followup["candidate_id"], "btc_eth_low_turnover_sweep080_followup159")
        self.assertEqual(low_turnover_followup["lane"], "validation")
        self.assertEqual(low_turnover_followup["priority"], "P0")
        self.assertEqual(
            low_turnover_followup["frozen_scope"]["scope"],
            "btc_eth_intraday_low_turnover_followup_review_only_no_order_paths",
        )
        self.assertEqual(low_turnover_followup["evidence_summary"]["sibling_pass_count"], 5)
        self.assertFalse(low_turnover_followup["evidence_summary"]["counts_as_paper_or_live_evidence"])
        plateau = queue.experiment_from_decision(
            {
                "decision_id": "btc_eth_intraday_oos_stability_plateau_review",
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "ready_for_human_review": True,
                "exact_phrase_to_record": "REVIEW_BTC_ETH_INTRADAY_OOS_STABILITY_PLATEAU_ONLY",
                "evidence_summary": {"stability_pass_count": 3, "best_improves_current": False},
            },
            1,
        )
        self.assertIsNotNone(plateau)
        assert plateau is not None
        self.assertEqual(plateau["experiment_type"], "btc_eth_intraday_oos_stability_plateau_review")
        self.assertEqual(plateau["lane"], "validation")
        self.assertEqual(plateau["frozen_scope"]["scope"], "oos_stability_plateau_review_only_no_order_paths")
        self.assertEqual(plateau["evidence_summary"]["stability_pass_count"], 3)
        friction = queue.experiment_from_decision(
            {
                "decision_id": "btc_eth_intraday_cost_friction_review",
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "ready_for_human_review": True,
                "exact_phrase_to_record": "REVIEW_BTC_ETH_INTRADAY_COST_FRICTION_ONLY",
                "evidence_summary": {"cost_pass_count": 0},
            },
            1,
        )
        self.assertIsNotNone(friction)
        assert friction is not None
        self.assertEqual(friction["experiment_type"], "btc_eth_intraday_cost_friction_review")
        self.assertEqual(friction["lane"], "validation")
        self.assertEqual(friction["frozen_scope"]["scope"], "btc_eth_intraday_cost_friction_review_only_no_order_paths")
        dependency_relief = next(
            row for row in report["queue"] if row["source_decision_id"] == "bithumb_current_actionable_dependency_relief_review"
        )
        self.assertEqual(dependency_relief["experiment_type"], "bithumb_dependency_relief_review")
        self.assertEqual(
            dependency_relief["frozen_scope"]["scope"],
            "dependency_relief_evidence_review_only_no_order_paths",
        )
        orca_family = next(
            row for row in report["queue"] if row["source_decision_id"] == "bithumb_current_actionable_orca_oos_family_review"
        )
        self.assertEqual(orca_family["experiment_type"], "bithumb_orca_oos_family_review")
        self.assertEqual(orca_family["lane"], "validation")
        orca_stop = queue.experiment_from_decision(
            {
                "decision_id": "bithumb_current_actionable_orca_repair_stop_condition_review",
                "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                "ready_for_human_review": True,
                "exact_phrase_to_record": "REVIEW_ORCA_REPAIR_STOP_CONDITION_ONLY",
                "evidence_summary": {"recommended_branch_action": "STOP_ORCA_REPAIR_BRANCH_AUTOMATION"},
            },
            1,
        )
        self.assertIsNotNone(orca_stop)
        assert orca_stop is not None
        self.assertEqual(orca_stop["experiment_type"], "bithumb_orca_repair_stop_condition_review")
        self.assertEqual(orca_stop["lane"], "validation")
        self.assertEqual(orca_stop["frozen_scope"]["scope"], "orca_repair_stop_condition_review_only_no_order_paths")
        blocker_triage = queue.experiment_from_decision(
            {
                "decision_id": "bithumb_current_actionable_gatekeeper_blocker_triage_review",
                "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                "ready_for_human_review": True,
                "exact_phrase_to_record": "REVIEW_BITHUMB_GATEKEEPER_BLOCKER_TRIAGE_ONLY",
                "evidence_summary": {"robustness_pass_count": 0},
            },
            1,
        )
        self.assertIsNotNone(blocker_triage)
        assert blocker_triage is not None
        self.assertEqual(blocker_triage["experiment_type"], "bithumb_gatekeeper_blocker_triage_review")
        self.assertEqual(blocker_triage["frozen_scope"]["scope"], "gatekeeper_blocker_triage_review_only_no_order_paths")
        alternate_failure = queue.experiment_from_decision(
            {
                "decision_id": "bithumb_current_actionable_alternate_robustness_failure_review",
                "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                "ready_for_human_review": True,
                "exact_phrase_to_record": "REVIEW_BITHUMB_ALTERNATE_ROBUSTNESS_FAILURE_ONLY",
                "evidence_summary": {
                    "evaluated_oos_pass_candidate_count": 6,
                    "robustness_pass_candidate_count": 0,
                    "counts_as_paper_or_live_evidence": False,
                },
            },
            1,
        )
        self.assertIsNotNone(alternate_failure)
        assert alternate_failure is not None
        self.assertEqual(alternate_failure["experiment_type"], "bithumb_alternate_robustness_failure_review")
        self.assertEqual(
            alternate_failure["frozen_scope"]["scope"],
            "alternate_robustness_failure_review_only_no_order_paths",
        )
        self.assertFalse(alternate_failure["evidence_summary"]["counts_as_paper_or_live_evidence"])
        research_hold = next(
            row for row in report["queue"] if row["source_decision_id"] == "bithumb_research_hold_triage_review"
        )
        self.assertEqual(research_hold["experiment_type"], "bithumb_research_hold_triage_review")
        self.assertEqual(research_hold["lane"], "validation")
        self.assertEqual(
            research_hold["frozen_scope"]["scope"],
            "research_hold_triage_review_only_no_order_paths",
        )
        self.assertFalse(research_hold["evidence_summary"]["counts_as_paper_or_live_evidence"])
        widened_stop = next(
            row
            for row in report["queue"]
            if row["source_decision_id"] == "bithumb_non_orca_widened_repair_stop_condition_review"
        )
        self.assertEqual(widened_stop["frozen_scope"]["scope"], "widened_repair_stop_condition_review_only_no_order_paths")
        shadow = next(
            row for row in report["queue"] if row["source_decision_id"] == "bithumb_current_actionable_shadow_review"
        )
        self.assertEqual(shadow["status"], "WAITING_FOR_HUMAN_REVIEW")
        self.assertEqual(shadow["frozen_scope"]["scope"], "human_decision_prep_only_no_shadow_registration_no_order_paths")
        sleeve = next(row for row in report["queue"] if row["source_decision_id"] == "stock_portfolio_sleeve_review")
        self.assertEqual(sleeve["experiment_type"], "stock_etf_portfolio_sleeve_review")
        self.assertEqual(sleeve["lane"], "portfolio")
        self.assertEqual(sleeve["frozen_scope"]["scope"], "portfolio_sleeve_review_only_no_order_paths")
        stock_child = next(
            row
            for row in report["queue"]
            if row["experiment_id"] == "stock_etf_fixed_exposure_child__stock_aggressive__a"
        )
        self.assertEqual(stock_child["evidence_summary"]["fixed_exposure_cap"], 0.65)
        self.assertEqual(stock_child["evidence_summary"]["before_cagr"], 0.7)
        self.assertFalse(stock_child["evidence_summary"]["order_paths_allowed"])
        self.assertFalse(stock_child["evidence_summary"]["counts_as_paper_or_live_evidence"])
        sensitivity = next(
            row for row in report["queue"] if row["source_decision_id"] == "stock_portfolio_sleeve_sensitivity_review"
        )
        self.assertEqual(sensitivity["experiment_type"], "stock_etf_portfolio_sleeve_sensitivity_review")
        self.assertEqual(sensitivity["candidate_id"], "stock_etf_top5_sleeve_sensitivity")
        self.assertEqual(sensitivity["lane"], "portfolio")
        self.assertEqual(
            sensitivity["frozen_scope"]["scope"],
            "portfolio_sleeve_sensitivity_review_only_no_order_paths",
        )
        orca_seed = next(
            row for row in report["queue"] if row["source_decision_id"] == "bithumb_current_actionable_orca_repair_seed_packet"
        )
        self.assertEqual(orca_seed["experiment_type"], "bithumb_orca_repair_seed_sweep")
        self.assertEqual(orca_seed["frozen_scope"]["scope"], "orca_repair_seed_research_only_no_order_paths")
        self.assertFalse(orca_seed["evidence_summary"]["counts_as_paper_or_live_evidence"])
        family_repair = next(
            row
            for row in report["queue"]
            if row["source_decision_id"] == "bithumb_current_actionable_family_diversity_failure_review"
        )
        self.assertEqual(family_repair["experiment_type"], "bithumb_non_orca_family_pass_fold_repair")
        self.assertEqual(
            family_repair["frozen_scope"]["scope"],
            "non_orca_family_pass_fold_repair_research_only_no_order_paths",
        )
        self.assertEqual(
            family_repair["evidence_summary"]["recommended_research_action"],
            "REPAIR_NON_ORCA_PASS_FOLD_COVERAGE",
        )
        self.assertFalse(family_repair["evidence_summary"]["counts_as_paper_or_live_evidence"])

    def test_blocked_when_no_queue_items_can_be_built(self) -> None:
        report = queue.build_report({}, {}, {})

        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["summary"]["experiment_count"], 0)

    def test_stock_children_are_skipped_when_any_order_path_is_allowed(self) -> None:
        priority = {"ready_decisions": []}
        stock = {
            "status": "READY_FOR_GATEKEEPER_REVIEW",
            "no_order_assertions": dict(queue.NO_ORDER_ASSERTIONS),
            "queue": [
                {
                    "candidate_id": "unsafe",
                    "order_paths_allowed": True,
                    "broker_submit_allowed": False,
                    "live_enabled": False,
                    "private_submit_allowed": False,
                    "real_orders_allowed": False,
                }
            ],
        }
        report = queue.build_report(priority, stock, {})

        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["summary"]["experiment_count"], 0)

    def test_state_payload_preserves_legacy_queue_key(self) -> None:
        report = queue.build_report(
            {
                "ready_decisions": [
                    {
                        "decision_id": "btc_eth_intraday_robustness_repair_review",
                        "candidate_id": "btc_eth_child",
                        "status": "ROBUSTNESS_REPAIR_READY",
                        "ready_for_human_review": True,
                        "priority_score": 90,
                        "blockers": [],
                    }
                ]
            },
            {},
            {},
        )
        state = queue.state_payload(report)

        self.assertEqual(state["schema_version"], "1.1")
        self.assertEqual(len(state["queue"]), 1)
        self.assertEqual(state["queue"][0]["repo"], "crypto")
        self.assertFalse(state["no_order_assertions"]["live_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
