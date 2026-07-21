from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_gatekeeper_pending_decision_board.py")
SPEC = importlib.util.spec_from_file_location("build_gatekeeper_pending_decision_board", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
board_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(board_builder)


class GatekeeperPendingDecisionBoardTests(unittest.TestCase):
    def test_board_collects_ready_decisions_without_permissions(self) -> None:
        board = board_builder.build_board(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "review_ready": True,
                "blockers": [],
                "evidence_summary": {
                    "paper_cycles_completed": 202,
                    "combined_non_flat_signal_count": 2,
                    "combined_executable_order_evidence_count": 2,
                    "extended_paper_ready": False,
                    "historical_replay_non_flat_excluded": 197,
                },
            },
            {
                "status": "PENDING_HUMAN_GATEKEEPER_DECISION",
                "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
                "human_decision": {"path": "decision.json", "present": False},
                "evidence_summary": {"estimated_cagr": 0.21, "estimated_mdd": -0.2},
                "blockers": ["HUMAN_GATEKEEPER_SHADOW_DECISION_MISSING"],
            },
            {
                "status": "PENDING_HUMAN_GATEKEEPER_DECISION",
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "human_decision": {"path": "decision.json", "present": False},
                "evidence_summary": {"estimated_average_fold_cagr": 0.02, "estimated_worst_fold_mdd": -0.12},
                "blockers": ["HUMAN_GATEKEEPER_SHADOW_DECISION_MISSING"],
            },
            {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "candidate_id": "stock_candidate",
                "proposed_conversion": {
                    "overlay": "fixed_exposure_065",
                    "estimated_cagr": 0.45,
                    "estimated_mdd": -0.199,
                },
                "sizing_repair": {
                    "status": "SIZING_REPAIR_READY",
                    "repair_ready_count": 2,
                },
                "robustness_stress": {
                    "queue_coverage": {
                        "target_count": 5,
                        "ready_candidate_count": 5,
                        "covered_candidate_count": 5,
                        "stress_pass_candidate_count": 3,
                        "top5_full_coverage": True,
                        "all_covered_candidates_safe": True,
                    }
                },
                "repaired_robustness": {
                    "status": "REPAIRED_ROBUSTNESS_STRESS_PASS",
                    "queue_coverage": {
                        "covered_candidate_count": 5,
                        "stress_pass_candidate_count": 5,
                        "repaired_candidate_count": 2,
                        "top5_full_coverage": True,
                        "all_covered_candidates_safe": True,
                    },
                },
                "blockers": [],
            },
            {"status": "PASS"},
            bithumb_actionable_dependency_relief={
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "exact_phrase_to_record": "REVIEW_DEPENDENCY_RELIEF_EVIDENCE_ONLY",
                "dependency_relief_candidate": {
                    "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                    "estimated_cagr": 0.88,
                    "estimated_mdd": -0.2,
                    "robustness_status": "ROBUSTNESS_STRESS_PASS",
                    "robustness_pass_count": 4,
                    "robustness_case_count": 7,
                },
                "dependency_relief_summary": {
                    "registered_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354",
                    "latest_oos_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                    "relief_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                    "sweep1354_dependency_reduced_by_review_evidence": True,
                    "relief_candidate_is_registered_candidate": False,
                    "relief_candidate_is_latest_oos_candidate": False,
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
            },
            btc_eth_intraday_human_decision_draft={
                "status": "DRAFT_READY",
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "draft_path": r"C:\AI\reports\model_factory\btc_eth_intraday_shadow_gatekeeper_decision_draft.json",
            },
            bridge_paper_safety_triage={
                "status": "BRIDGE_PAPER_SAFETY_TRIAGE_REVIEW_READY",
                "candidate_id": "bridge_28_relief",
                "repair_queue_evidence": {
                    "status": "LOCAL_SIM_PAPER_FAILED",
                    "failure_reason": "SIM_SAFETY_VIOLATION",
                },
                "paper_autotrade_evidence": {
                    "simulated_order_action": "HOLD",
                    "simulated_delta_weight": 0.0,
                },
                "firewall_evidence": {
                    "reject_count": 9,
                    "allow_paper_only_count": 1,
                },
                "review_conclusion": {
                    "candidate_remains_failed_for_promotion": True,
                    "paper_loop_hard_safety_clean": True,
                    "current_bridge_order_is_hold_zero_delta": True,
                },
                "counts_as_paper_or_live_evidence": False,
                "blockers": [],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            bithumb_research_hold_triage={
                "status": "BITHUMB_RESEARCH_HOLD_TRIAGE_REVIEW_READY",
                "research_hold_count": 3,
                "family_counts": {"btc_1d_impulse_flag_breakout": 1, "btc_1d_narrow_range_expansion": 2},
                "triage_summary": {
                    "dominant_failure_reason": "BACKTEST_BELOW_VALIDATION_INTAKE_BAR",
                    "recommended_action": "ARCHIVE_OR_REQUIRE_STRONGER_FROZEN_HYPOTHESIS",
                    "mutation_allowed_by_this_report": False,
                },
                "counts_as_paper_or_live_evidence": False,
                "blockers": [],
                "no_order_assertions": {
                    "mutation_allowed_by_this_report": False,
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            stock_portfolio_sleeve_sensitivity={
                "status": "PORTFOLIO_SLEEVE_SENSITIVITY_REVIEW_READY",
                "scenario_count": 5,
                "viable_scenario_count": 4,
                "best_scenario_id": "etf_tilt_60_40",
                "best_estimated_sleeve_cagr": 0.446,
                "worst_weighted_mdd_proxy": -0.195,
                "counts_as_paper_or_live_evidence": False,
                "blockers": [],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            stock_portfolio_sleeve_resilience={
                "status": "PORTFOLIO_SLEEVE_RESILIENCE_REVIEW_READY",
                "scenario_count": 5,
                "viable_scenario_count": 5,
                "worst_leave_one_out_cagr": 0.435,
                "worst_leave_one_out_mdd_proxy": -0.195,
                "max_cagr_drop_vs_base": -0.012,
                "counts_as_paper_or_live_evidence": False,
                "blockers": [],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        )

        self.assertEqual(board["status"], "READY_FOR_GATEKEEPER_REVIEW")
        self.assertEqual(board["decision_count"], 9)
        self.assertEqual(board["ready_decision_count"], 9)
        self.assertFalse(board["board_permissions"]["promotion_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["shadow_registration_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["live_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])
        self.assertFalse(board["safety"]["does_register_shadow_candidate"])
        self.assertFalse(board["safety"]["does_start_shadow_loop"])
        stock = next(item for item in board["items"] if item["decision_id"] == "stock_conversion_review")
        self.assertEqual(stock["evidence_summary"]["robustness_top5_target_count"], 5)
        self.assertEqual(stock["evidence_summary"]["robustness_top5_ready_candidate_count"], 5)
        self.assertEqual(stock["evidence_summary"]["robustness_top5_covered_candidate_count"], 5)
        self.assertEqual(stock["evidence_summary"]["robustness_top5_stress_pass_candidate_count"], 3)
        self.assertTrue(stock["evidence_summary"]["robustness_top5_full_coverage"])
        self.assertTrue(stock["evidence_summary"]["robustness_top5_all_safe"])
        self.assertEqual(stock["evidence_summary"]["sizing_repair_ready_count"], 2)
        self.assertEqual(stock["evidence_summary"]["stress_pass_plus_repair_ready_count"], 5)
        self.assertEqual(stock["evidence_summary"]["repaired_robustness_status"], "REPAIRED_ROBUSTNESS_STRESS_PASS")
        self.assertEqual(stock["evidence_summary"]["repaired_robustness_top5_stress_pass_candidate_count"], 5)
        self.assertEqual(stock["evidence_summary"]["repaired_robustness_repaired_candidate_count"], 2)
        self.assertTrue(stock["evidence_summary"]["repaired_robustness_top5_all_safe"])
        self.assertEqual(stock["exact_phrase_to_record"], "REVIEW_CONVERSION_EVIDENCE_ONLY")
        self.assertIn("does not approve promotion", stock["review_only_effect"])
        sensitivity = next(
            item for item in board["items"] if item["decision_id"] == "stock_portfolio_sleeve_sensitivity_review"
        )
        self.assertTrue(sensitivity["ready_for_human_review"])
        self.assertEqual(
            sensitivity["exact_phrase_to_record"],
            "REVIEW_STOCK_PORTFOLIO_SLEEVE_SENSITIVITY_EVIDENCE_ONLY",
        )
        self.assertEqual(sensitivity["evidence_summary"]["scenario_count"], 5)
        self.assertEqual(sensitivity["evidence_summary"]["viable_scenario_count"], 4)
        self.assertFalse(sensitivity["evidence_summary"]["counts_as_paper_or_live_evidence"])
        self.assertIn("does not approve promotion", sensitivity["review_only_effect"])
        resilience = next(
            item for item in board["items"] if item["decision_id"] == "stock_portfolio_sleeve_resilience_review"
        )
        self.assertTrue(resilience["ready_for_human_review"])
        self.assertEqual(
            resilience["exact_phrase_to_record"],
            "REVIEW_STOCK_PORTFOLIO_SLEEVE_RESILIENCE_EVIDENCE_ONLY",
        )
        self.assertEqual(resilience["evidence_summary"]["scenario_count"], 5)
        self.assertEqual(resilience["evidence_summary"]["viable_scenario_count"], 5)
        self.assertFalse(resilience["evidence_summary"]["counts_as_paper_or_live_evidence"])
        self.assertIn("does not approve promotion", resilience["review_only_effect"])
        relief = next(item for item in board["items"] if item["decision_id"] == "bithumb_current_actionable_dependency_relief_review")
        self.assertEqual(relief["exact_phrase_to_record"], "REVIEW_DEPENDENCY_RELIEF_EVIDENCE_ONLY")
        self.assertTrue(relief["evidence_summary"]["sweep1354_dependency_reduced_by_review_evidence"])
        self.assertFalse(relief["evidence_summary"]["relief_candidate_is_registered_candidate"])
        self.assertIn("does not approve promotion", relief["review_only_effect"])
        intraday = next(item for item in board["items"] if item["decision_id"] == "btc_eth_intraday_shadow_review")
        self.assertEqual(intraday["human_decision_draft_status"], "DRAFT_READY")
        self.assertEqual(intraday["human_decision_draft_candidate_id"], "btc_eth_intraday_momentum_btc_4h_sweep001")
        self.assertTrue(str(intraday["human_decision_draft_path"]).endswith("btc_eth_intraday_shadow_gatekeeper_decision_draft.json"))
        bridge = next(item for item in board["items"] if item["decision_id"] == "bridge_paper_safety_triage_review")
        self.assertTrue(bridge["ready_for_human_review"])
        self.assertEqual(bridge["exact_phrase_to_record"], "REVIEW_BRIDGE_PAPER_SAFETY_TRIAGE_ONLY")
        self.assertEqual(bridge["evidence_summary"]["failure_reason"], "SIM_SAFETY_VIOLATION")
        self.assertTrue(bridge["evidence_summary"]["candidate_remains_failed_for_promotion"])
        self.assertFalse(bridge["evidence_summary"]["counts_as_paper_or_live_evidence"])
        research_hold = next(
            item for item in board["items"] if item["decision_id"] == "bithumb_research_hold_triage_review"
        )
        self.assertTrue(research_hold["ready_for_human_review"])
        self.assertEqual(research_hold["exact_phrase_to_record"], "REVIEW_BITHUMB_RESEARCH_HOLD_TRIAGE_ONLY")
        self.assertEqual(research_hold["evidence_summary"]["research_hold_count"], 3)
        self.assertEqual(
            research_hold["evidence_summary"]["recommended_action"],
            "ARCHIVE_OR_REQUIRE_STRONGER_FROZEN_HYPOTHESIS",
        )
        self.assertFalse(research_hold["evidence_summary"]["counts_as_paper_or_live_evidence"])

    def test_board_surfaces_paper_smoke_human_decision_draft(self) -> None:
        board = board_builder.build_board(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "review_ready": True,
                "blockers": [],
                "evidence_summary": {
                    "paper_cycles_completed": 252,
                    "combined_non_flat_signal_count": 53,
                    "combined_executable_order_evidence_count": 53,
                    "extended_paper_ready": False,
                    "historical_replay_non_flat_excluded": 7621,
                },
            },
            {},
            {},
            {},
            {"status": "PASS"},
            paper_smoke_human_decision_draft={
                "status": "DRAFT_READY",
                "draft_path": r"C:\AI\reports\model_factory\paper_smoke_gatekeeper_decision_draft.json",
            },
        )

        item = next(row for row in board["items"] if row["decision_id"] == "paper_smoke_review")
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["human_decision_draft_status"], "DRAFT_READY")
        self.assertEqual(item["exact_phrase_to_record"], "REVIEW_PAPER_SMOKE_ONLY")
        self.assertTrue(str(item["human_decision_draft_path"]).endswith("paper_smoke_gatekeeper_decision_draft.json"))
        self.assertFalse(board["board_permissions"]["paper_enabled_by_this_board"])
        self.assertFalse(board["board_permissions"]["live_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])

    def test_board_surfaces_btc_eth_alternate_repair_child_packet_without_permissions(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {"status": "PASS"},
            btc_eth_intraday_robustness_repair_alternate_child={
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "base_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "primary_child_candidate_id": "repair_445",
                "top_alternate_candidate_id": "repair_441",
                "alternate_pass_child_count": 41,
                "top_alternate_child_count": 5,
                "repair_pass_count": 42,
                "repair_trial_count": 528,
                "counts_as_paper_or_live_evidence": False,
                "exact_phrase_to_record": "REVIEW_BTC_ETH_INTRADAY_ALTERNATE_REPAIR_CHILDREN_ONLY",
                "blockers": [],
                "no_order_assertions": {
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

        item = next(
            row
            for row in board["items"]
            if row["decision_id"] == "btc_eth_intraday_robustness_repair_alternate_child_review"
        )
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["candidate_id"], "repair_441")
        self.assertEqual(
            item["exact_phrase_to_record"],
            "REVIEW_BTC_ETH_INTRADAY_ALTERNATE_REPAIR_CHILDREN_ONLY",
        )
        self.assertEqual(item["evidence_summary"]["alternate_pass_child_count"], 41)
        self.assertFalse(item["evidence_summary"]["counts_as_paper_or_live_evidence"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])

    def test_board_attaches_low_turnover_followup_support_to_existing_review(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {"status": "PASS"},
            btc_eth_intraday_low_turnover_rebuild_gatekeeper_packet={
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "recommended_decision": "REVIEW_BTC_ETH_INTRADAY_LOW_TURNOVER_REBUILD_ONLY",
                "exact_phrase_to_record": "REVIEW_BTC_ETH_INTRADAY_LOW_TURNOVER_REBUILD_ONLY",
                "candidate_id": "sweep080",
                "evidence_summary": {
                    "base_candidate_id": "base001",
                    "best_cost_pass_count": 2,
                    "counts_as_paper_or_live_evidence": False,
                },
                "blockers": [],
                "no_order_assertions": {
                    "promotion_allowed_by_this_packet": False,
                    "shadow_registration_allowed_by_this_packet": False,
                    "paper_enabled_by_this_packet": False,
                    "live_allowed_by_this_packet": False,
                    "broker_submit_allowed_by_this_packet": False,
                    "private_submit_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                },
            },
            btc_eth_intraday_low_turnover_followup_sweep={
                "status": "LOW_TURNOVER_FOLLOWUP_SWEEP_PASS",
                "trial_count": 648,
                "evaluated_oos_pass_trial_count": 240,
                "followup_pass_count": 6,
                "sibling_pass_count": 5,
                "nearby_pass_density": 0.007716,
                "best_candidate_id": "sweep080_followup159",
                "best_cost_pass_count": 2,
                "counts_as_paper_or_live_evidence": False,
                "mutation_allowed_by_this_report": False,
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        )

        item = next(
            row
            for row in board["items"]
            if row["decision_id"] == "btc_eth_intraday_low_turnover_signal_rebuild_review"
        )
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["candidate_id"], "sweep080")
        self.assertEqual(item["exact_phrase_to_record"], "REVIEW_BTC_ETH_INTRADAY_LOW_TURNOVER_REBUILD_ONLY")
        support = item["evidence_summary"]["followup_support"]
        self.assertTrue(support["followup_safe"])
        self.assertEqual(support["followup_trial_count"], 648)
        self.assertEqual(support["followup_sibling_pass_count"], 5)
        self.assertEqual(support["followup_best_candidate_id"], "sweep080_followup159")
        self.assertFalse(support["followup_counts_as_paper_or_live_evidence"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])

    def test_board_surfaces_family_parameter_repair_review_without_permissions(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {"status": "PASS"},
            {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                "evidence_summary": {
                    "market": "KRW-POLA",
                    "oos_pass_fold_count": 2,
                    "robustness_pass_count": 4,
                },
                "blockers": [],
                "no_order_assertions": {
                    "promotion_allowed_by_this_packet": False,
                    "shadow_registration_allowed_by_this_packet": False,
                    "paper_enabled_by_this_packet": False,
                    "live_allowed_by_this_packet": False,
                    "broker_submit_allowed_by_this_packet": False,
                    "private_submit_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                },
            },
            bithumb_actionable_family_parameter_repair={
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                "evidence_summary": {
                    "market": "KRW-POLA",
                    "oos_pass_fold_count": 2,
                    "robustness_pass_count": 4,
                },
                "blockers": [],
                "no_order_assertions": {
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

        item = next(
            row
            for row in board["items"]
            if row["decision_id"] == "bithumb_current_actionable_family_parameter_repair_review"
        )
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["decision_type"], "family_parameter_repair_review")
        self.assertEqual(item["recommended_decision"], "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY")
        self.assertEqual(item["exact_phrase_to_record"], "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY")
        self.assertIn("does not approve promotion", item["review_only_effect"])
        self.assertFalse(board["board_permissions"]["shadow_registration_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])
        rendered = board_builder.render_markdown(board)
        self.assertIn("exact phrase", rendered)
        self.assertIn("REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY", rendered)
        self.assertIn("does not approve promotion", rendered)

    def test_board_surfaces_non_orca_widened_stop_condition_review_without_permissions(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {"status": "PASS"},
            bithumb_non_orca_widened_repair_stop_condition={
                "status": "NON_ORCA_WIDENED_REPAIR_STOP_CONDITION_READY",
                "repair_target_count": 2,
                "trial_count": 162,
                "evaluated_trial_count": 162,
                "oos_pass_trial_count": 0,
                "robustness_pass_trial_count": 0,
                "best_candidate_id": "bio_widenedrepair_070",
                "recommended_branch_action": "STOP_NON_ORCA_WIDENED_REPAIR_GRID",
                "recommended_next_research_action": "REBUILD_NON_ORCA_ENTRY_FAMILY_OR_SOURCE_DATA_EVIDENCE",
                "counts_as_paper_or_live_evidence": False,
                "blockers": [],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        )

        item = next(
            row
            for row in board["items"]
            if row["decision_id"] == "bithumb_non_orca_widened_repair_stop_condition_review"
        )
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["exact_phrase_to_record"], "REVIEW_NON_ORCA_WIDENED_STOP_CONDITION_ONLY")
        self.assertEqual(item["evidence_summary"]["trial_count"], 162)
        self.assertEqual(item["evidence_summary"]["oos_pass_trial_count"], 0)
        self.assertEqual(item["evidence_summary"]["robustness_pass_trial_count"], 0)
        self.assertFalse(item["evidence_summary"]["counts_as_paper_or_live_evidence"])
        self.assertFalse(board["board_permissions"]["promotion_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["live_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])

    def test_board_surfaces_non_orca_entry_source_rebuild_review_without_permissions(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {"status": "PASS"},
            bithumb_non_orca_entry_source_rebuild_sweep={
                "status": "NON_ORCA_ENTRY_SOURCE_REBUILD_SWEEP_PASS",
                "rebuild_target_count": 2,
                "trial_count": 162,
                "evaluated_trial_count": 162,
                "oos_pass_trial_count": 33,
                "robustness_pass_trial_count": 15,
                "best_candidate_id": "pola_entrysource_029",
                "best_repair_target_id": "pola",
                "best_candidate_status": "OOS_CANDIDATE_PASS",
                "best_robustness_status": "ROBUSTNESS_STRESS_PASS",
                "counts_as_paper_or_live_evidence": False,
                "blockers": [],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        )

        item = next(
            row
            for row in board["items"]
            if row["decision_id"] == "bithumb_non_orca_entry_source_rebuild_review"
        )
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["exact_phrase_to_record"], "REVIEW_NON_ORCA_ENTRY_SOURCE_REBUILD_EVIDENCE_ONLY")
        self.assertEqual(item["evidence_summary"]["oos_pass_trial_count"], 33)
        self.assertEqual(item["evidence_summary"]["robustness_pass_trial_count"], 15)
        self.assertFalse(item["evidence_summary"]["counts_as_paper_or_live_evidence"])
        self.assertFalse(board["board_permissions"]["promotion_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["live_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])

    def test_board_prefers_non_orca_entry_source_rebuild_gatekeeper_packet_without_permissions(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {"status": "PASS"},
            bithumb_non_orca_entry_source_rebuild_sweep={
                "status": "NON_ORCA_ENTRY_SOURCE_REBUILD_SWEEP_PASS",
                "best_candidate_id": "raw_sweep_candidate",
                "counts_as_paper_or_live_evidence": False,
                "blockers": [],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            bithumb_non_orca_entry_source_rebuild_gatekeeper_packet={
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "candidate_id": "pola_entrysource_029",
                "exact_phrase_to_record": "REVIEW_NON_ORCA_ENTRY_SOURCE_REBUILD_EVIDENCE_ONLY",
                "evidence_summary": {
                    "market": "KRW-POLA",
                    "oos_pass_fold_count": 3,
                    "robustness_pass_count": 5,
                    "trial_count": 162,
                    "counts_as_paper_or_live_evidence": False,
                },
                "blockers": [],
                "no_order_assertions": {
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

        item = next(
            row
            for row in board["items"]
            if row["decision_id"] == "bithumb_non_orca_entry_source_rebuild_review"
        )
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["candidate_id"], "pola_entrysource_029")
        self.assertEqual(item["evidence_summary"]["market"], "KRW-POLA")
        self.assertEqual(item["exact_phrase_to_record"], "REVIEW_NON_ORCA_ENTRY_SOURCE_REBUILD_EVIDENCE_ONLY")
        self.assertIn("gatekeeper_packet", item["source_path"])
        self.assertIn("does not approve promotion", item["review_only_effect"])
        self.assertFalse(board["board_permissions"]["shadow_registration_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])

    def test_board_surfaces_non_orca_entry_source_alternate_child_without_permissions(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {"status": "PASS"},
            bithumb_non_orca_entry_source_alternate_child={
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "primary_child_candidate_id": "pola_entrysource_029",
                "top_alternate_candidate_id": "pola_entrysource_032",
                "alternate_pass_child_count": 14,
                "top_alternate_child_count": 3,
                "exact_phrase_to_record": "REVIEW_NON_ORCA_ENTRY_SOURCE_ALTERNATE_CHILDREN_ONLY",
                "counts_as_paper_or_live_evidence": False,
                "blockers": [],
                "no_order_assertions": {
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

        item = next(
            row
            for row in board["items"]
            if row["decision_id"] == "bithumb_non_orca_entry_source_alternate_child_review"
        )
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["candidate_id"], "pola_entrysource_032")
        self.assertEqual(item["exact_phrase_to_record"], "REVIEW_NON_ORCA_ENTRY_SOURCE_ALTERNATE_CHILDREN_ONLY")
        self.assertEqual(item["evidence_summary"]["primary_child_candidate_id"], "pola_entrysource_029")
        self.assertEqual(item["evidence_summary"]["alternate_pass_child_count"], 14)
        self.assertFalse(item["evidence_summary"]["counts_as_paper_or_live_evidence"])
        self.assertFalse(board["board_permissions"]["shadow_registration_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])

    def test_board_surfaces_orca_oos_family_review_without_permissions(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {"status": "PASS"},
            bithumb_actionable_orca_oos_family_review={
                "status": "ORCA_OOS_FAMILY_REVIEW_READY",
                "market": "KRW-ORCA",
                "family": "bithumb_current_actionable_orca_1d_long_freeze001",
                "oos_pass_candidate_count": 6,
                "distinct_parameter_count": 6,
                "top_candidate": {
                    "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                    "estimated_cagr": 1.39,
                    "estimated_mdd": -0.2,
                },
                "review_value": {
                    "reduces_single_registered_candidate_dependency": True,
                    "adds_market_family_diversity": True,
                },
                "blockers": [],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "shadow_registration_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        )

        item = next(
            row
            for row in board["items"]
            if row["decision_id"] == "bithumb_current_actionable_orca_oos_family_review"
        )
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["decision_type"], "orca_oos_family_evidence_review")
        self.assertEqual(item["recommended_decision"], "REVIEW_ORCA_OOS_FAMILY_EVIDENCE_ONLY")
        self.assertEqual(item["exact_phrase_to_record"], "REVIEW_ORCA_OOS_FAMILY_EVIDENCE_ONLY")
        self.assertEqual(item["evidence_summary"]["oos_pass_candidate_count"], 6)
        self.assertTrue(item["evidence_summary"]["reduces_single_registered_candidate_dependency"])
        self.assertIn("does not approve promotion", item["review_only_effect"])
        self.assertFalse(board["board_permissions"]["shadow_registration_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])

    def test_board_surfaces_orca_repair_stop_condition_review_without_permissions(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {"status": "PASS"},
            bithumb_actionable_orca_repair_stop_condition={
                "status": "ORCA_REPAIR_STOP_CONDITION_REVIEW_READY",
                "base_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                "market": "KRW-ORCA",
                "seed_generation_count": 2,
                "total_seed_count": 6,
                "total_evaluated_seed_count": 6,
                "first_seed_oos_pass_count": 3,
                "first_seed_robustness_pass_count": 0,
                "followup_seed_oos_pass_count": 0,
                "followup_seed_robustness_pass_count": 0,
                "best_first_seed_id": "orca_selective_volume_stop05_hold3_tp18",
                "best_followup_seed_id": "orca_followup_volume150_stop035_hold1_tp08",
                "recommended_branch_action": "STOP_ORCA_REPAIR_BRANCH_AUTOMATION",
                "counts_as_paper_or_live_evidence": False,
                "blockers": [],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        )

        item = next(
            row
            for row in board["items"]
            if row["decision_id"] == "bithumb_current_actionable_orca_repair_stop_condition_review"
        )
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["exact_phrase_to_record"], "REVIEW_ORCA_REPAIR_STOP_CONDITION_ONLY")
        self.assertEqual(item["evidence_summary"]["total_seed_count"], 6)
        self.assertEqual(item["evidence_summary"]["followup_seed_oos_pass_count"], 0)
        self.assertEqual(item["evidence_summary"]["recommended_branch_action"], "STOP_ORCA_REPAIR_BRANCH_AUTOMATION")
        self.assertFalse(item["evidence_summary"]["counts_as_paper_or_live_evidence"])
        self.assertFalse(board["board_permissions"]["promotion_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["live_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])

    def test_board_surfaces_bithumb_gatekeeper_blocker_triage_without_permissions(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {"status": "PASS"},
            bithumb_actionable_gatekeeper_blocker_triage={
                "status": "BITHUMB_GATEKEEPER_BLOCKER_TRIAGE_REVIEW_READY",
                "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                "gatekeeper_packet_status": "BLOCKED",
                "gatekeeper_blockers": ["robustness_stress_pass"],
                "oos_status": "OOS_WALKFORWARD_PASS",
                "oos_pass_fold_count": 2,
                "robustness_status": "ROBUSTNESS_STRESS_ITERATE",
                "robustness_case_count": 7,
                "robustness_pass_count": 0,
                "robustness_cost_pass_count": 0,
                "estimated_cagr": 1.39,
                "estimated_mdd": -0.2,
                "high_cagr_counts_as_promotion_evidence": False,
                "recommended_action": "KEEP_BLOCKED_REQUIRE_ROBUSTNESS_REPAIR_OR_ALTERNATE_FAMILY_BEFORE_GATEKEEPER_REVIEW",
                "counts_as_paper_or_live_evidence": False,
                "blockers": [],
                "no_order_assertions": {
                    "mutation_allowed_by_this_report": False,
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        )

        item = next(
            row
            for row in board["items"]
            if row["decision_id"] == "bithumb_current_actionable_gatekeeper_blocker_triage_review"
        )
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["exact_phrase_to_record"], "REVIEW_BITHUMB_GATEKEEPER_BLOCKER_TRIAGE_ONLY")
        self.assertEqual(item["evidence_summary"]["robustness_pass_count"], 0)
        self.assertFalse(item["evidence_summary"]["high_cagr_counts_as_promotion_evidence"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])

    def test_board_surfaces_btc_eth_robustness_repair_review_without_permissions(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {"status": "PASS"},
            btc_eth_intraday_robustness_repair={
                "status": "ROBUSTNESS_REPAIR_READY",
                "base_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "best_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001_robustrepair_445",
                "trial_count": 528,
                "evaluated_oos_pass_trial_count": 125,
                "repair_pass_count": 46,
                "best_pass_count": 7,
                "best_cost_pass_count": 2,
                "best_cost_case_id": "cost_30bps",
                "best_cost_total_return": 0.068,
                "best_cost_return_gap_to_pass": 0.0,
                "best_cost_mdd": -0.196,
                "best_cost_mdd_gap_to_pass": 0.0,
                "counts_as_paper_or_live_evidence": False,
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        )

        item = next(row for row in board["items"] if row["decision_id"] == "btc_eth_intraday_robustness_repair_review")
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["candidate_id"], "btc_eth_intraday_momentum_btc_4h_sweep001_robustrepair_445")
        self.assertEqual(item["exact_phrase_to_record"], "REVIEW_BTC_ETH_INTRADAY_ROBUSTNESS_REPAIR_ONLY")
        self.assertFalse(item["evidence_summary"]["counts_as_paper_or_live_evidence"])
        self.assertFalse(board["board_permissions"]["paper_enabled_by_this_board"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        rendered = board_builder.render_markdown(board)
        self.assertIn("REVIEW_BTC_ETH_INTRADAY_ROBUSTNESS_REPAIR_ONLY", rendered)
        self.assertIn("btc_eth_intraday_momentum_btc_4h_sweep001_robustrepair_445", rendered)

    def test_board_surfaces_btc_eth_oos_stability_plateau_review_without_permissions(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {"status": "PASS"},
            btc_eth_intraday_oos_stability_plateau={
                "status": "BTC_ETH_INTRADAY_OOS_STABILITY_PLATEAU_REVIEW_READY",
                "current_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "best_candidate_id": "btc_eth_intraday_momentum_btc_4h__stability_001",
                "evaluated_trial_count": 20,
                "stability_pass_count": 3,
                "current_worst_fold_mdd": -0.16791650341473752,
                "best_worst_fold_mdd": -0.16791650341473752,
                "current_average_fold_cagr": 0.26930593366095223,
                "best_average_fold_cagr": 0.26930593366095223,
                "best_improves_current": False,
                "recommended_action": "KEEP_CURRENT_INTRADAY_OOS_CANDIDATE_FOCUS_ROBUSTNESS_REPAIR",
                "counts_as_paper_or_live_evidence": False,
                "blockers": [],
                "no_order_assertions": {
                    "mutation_allowed_by_this_report": False,
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        )

        item = next(
            row for row in board["items"] if row["decision_id"] == "btc_eth_intraday_oos_stability_plateau_review"
        )
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["candidate_id"], "btc_eth_intraday_momentum_btc_4h_sweep001")
        self.assertEqual(item["exact_phrase_to_record"], "REVIEW_BTC_ETH_INTRADAY_OOS_STABILITY_PLATEAU_ONLY")
        self.assertEqual(item["evidence_summary"]["stability_pass_count"], 3)
        self.assertFalse(item["evidence_summary"]["best_improves_current"])
        self.assertFalse(item["evidence_summary"]["counts_as_paper_or_live_evidence"])
        self.assertFalse(board["board_permissions"]["paper_enabled_by_this_board"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])
        self.assertIn("REVIEW_BTC_ETH_INTRADAY_OOS_STABILITY_PLATEAU_ONLY", board_builder.render_markdown(board))

    def test_board_surfaces_btc_eth_cost_friction_review_without_permissions(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {"status": "PASS"},
            btc_eth_intraday_cost_friction={
                "status": "BTC_ETH_INTRADAY_COST_FRICTION_REVIEW_READY",
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "robustness_status": "ROBUSTNESS_STRESS_ITERATE",
                "case_count": 7,
                "pass_count": 4,
                "cost_pass_count": 0,
                "cost_case_count": 2,
                "recommended_action": "KEEP_RESEARCH_ONLY_REQUIRE_COST_FRICTION_REPAIR_BEFORE_SHADOW_OR_PAPER_USE",
                "counts_as_paper_or_live_evidence": False,
                "blockers": [],
                "no_order_assertions": {
                    "mutation_allowed_by_this_report": False,
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        )

        item = next(row for row in board["items"] if row["decision_id"] == "btc_eth_intraday_cost_friction_review")
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["candidate_id"], "btc_eth_intraday_momentum_btc_4h_sweep001")
        self.assertEqual(item["exact_phrase_to_record"], "REVIEW_BTC_ETH_INTRADAY_COST_FRICTION_ONLY")
        self.assertEqual(item["evidence_summary"]["cost_pass_count"], 0)
        self.assertFalse(item["evidence_summary"]["counts_as_paper_or_live_evidence"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])

    def test_board_surfaces_bithumb_alternate_robustness_failure_without_permissions(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {"status": "PASS"},
            bithumb_actionable_alternate_robustness_failure={
                "status": "BITHUMB_ALTERNATE_ROBUSTNESS_FAILURE_REVIEW_READY",
                "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                "alternate_robustness_status": "ALTERNATE_ROBUSTNESS_ITERATE",
                "evaluated_oos_pass_candidate_count": 6,
                "robustness_pass_candidate_count": 0,
                "best_alternate_candidate_id": None,
                "candidate_result_count": 6,
                "top_candidate_results": [{"candidate_id": "orca_1507", "pass_count": 0}],
                "oos_alternates_count_as_gatekeeper_relief": False,
                "recommended_action": "STOP_TREATING_OOS_ALTERNATES_AS_GATEKEEPER_RELIEF_REQUIRE_ROBUSTNESS_OR_NEW_FAMILY",
                "counts_as_paper_or_live_evidence": False,
                "blockers": [],
                "no_order_assertions": {
                    "mutation_allowed_by_this_report": False,
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        )

        item = next(
            row
            for row in board["items"]
            if row["decision_id"] == "bithumb_current_actionable_alternate_robustness_failure_review"
        )
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["exact_phrase_to_record"], "REVIEW_BITHUMB_ALTERNATE_ROBUSTNESS_FAILURE_ONLY")
        self.assertEqual(item["evidence_summary"]["evaluated_oos_pass_candidate_count"], 6)
        self.assertEqual(item["evidence_summary"]["robustness_pass_candidate_count"], 0)
        self.assertFalse(item["evidence_summary"]["oos_alternates_count_as_gatekeeper_relief"])
        self.assertFalse(item["evidence_summary"]["counts_as_paper_or_live_evidence"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])

    def test_board_blocks_when_risk_guard_is_not_pass(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {"status": "HALT"},
        )

        self.assertEqual(board["status"], "BLOCKED")
        self.assertEqual(board["risk_guard_status"], "HALT")
        self.assertFalse(board["risk_guard_hard_safety_ok"])

    def test_board_allows_warn_risk_guard_when_hard_safety_is_clean(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {},
            {},
            {},
            {
                "status": "WARN",
                "halt_count": 0,
                "checks": [
                    {"name": "live_disabled", "status": "PASS", "observed": False},
                    {"name": "private_submit_unused", "status": "PASS", "observed": False},
                    {"name": "real_orders_zero", "status": "PASS", "observed": 0},
                    {
                        "name": "broker_submit_scope",
                        "status": "PASS",
                        "observed": {"broker_submit_allowed": True, "broker_submit_scope": "paper_only"},
                    },
                    {"name": "paper_loop", "status": "WARN", "reason": "stale"},
                ],
            },
        )

        self.assertEqual(board["status"], "READY_FOR_GATEKEEPER_REVIEW")
        self.assertEqual(board["risk_guard_status"], "WARN")
        self.assertTrue(board["risk_guard_hard_safety_ok"])
        self.assertTrue(board["next_decision"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])

    def test_board_surfaces_invalid_stale_shadow_decision_for_human_review(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {
                "status": "INVALID_HUMAN_GATEKEEPER_DECISION",
                "candidate_id": "current_candidate",
                "human_decision": {
                    "path": "decision.json",
                    "present": True,
                    "valid": False,
                    "normalized": {
                        "candidate_id": "stale_candidate",
                        "decision": "APPROVE_SHADOW_REVIEW_ONLY",
                    },
                },
                "evidence_summary": {"estimated_cagr": 0.94, "estimated_mdd": -0.2},
                "blockers": ["HUMAN_GATEKEEPER_DECISION_CANDIDATE_MISMATCH"],
            },
            {},
            {},
            {"status": "PASS"},
            bithumb_actionable_human_decision_draft={
                "status": "DRAFT_READY",
                "candidate_id": "current_candidate",
                "draft_path": r"C:\AI\reports\model_factory\bithumb_current_actionable_shadow_gatekeeper_decision_draft.json",
            },
        )

        item = next(row for row in board["items"] if row["decision_id"] == "bithumb_current_actionable_shadow_review")
        self.assertTrue(item["ready_for_human_review"])
        self.assertFalse(item["human_decision_valid"])
        self.assertFalse(item["decision_candidate_match"])
        self.assertEqual(item["recorded_candidate_id"], "stale_candidate")
        self.assertEqual(item["human_decision_draft_status"], "DRAFT_READY")
        self.assertEqual(item["human_decision_draft_candidate_id"], "current_candidate")
        self.assertTrue(str(item["human_decision_draft_path"]).endswith("bithumb_current_actionable_shadow_gatekeeper_decision_draft.json"))
        self.assertEqual(item["exact_phrase_to_record"], "APPROVE_SHADOW_REVIEW_ONLY")
        self.assertEqual(item["alternate_allowed_phrases"], ["REJECT", "DEFER"])
        self.assertIn("HUMAN_GATEKEEPER_DECISION_CANDIDATE_MISMATCH", item["blockers"])
        self.assertFalse(board["board_permissions"]["shadow_registration_allowed_by_this_board"])
        self.assertFalse(board["safety"]["does_register_shadow_candidate"])

    def test_board_closes_registration_action_after_file_registration(self) -> None:
        candidate_id = "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354"
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {
                "status": "HUMAN_GATEKEEPER_SHADOW_DECISION_RECORDED",
                "candidate_id": candidate_id,
                "human_decision": {"path": "decision.json", "present": True, "valid": True},
                "blockers": [],
            },
            {},
            {},
            {"status": "PASS"},
            {
                "status": "READY_FOR_SHADOW_REGISTRATION_ACTION_REVIEW",
                "candidate_id": candidate_id,
                "planned_shadow_registration": {"candidate_id": candidate_id, "market": "KRW-POLA"},
                "blockers": [],
                "safety": {
                    "does_register_shadow_candidate": False,
                    "does_start_shadow_loop": False,
                    "does_enable_paper": False,
                    "does_enable_live": False,
                    "broker_submit_allowed_by_this_packet": False,
                    "private_submit_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                    "real_orders": 0,
                },
            },
            {
                "status": "REGISTERED",
                "candidate_id": candidate_id,
                "record": {"candidate_id": candidate_id, "market": "KRW-POLA"},
            },
        )

        item = next(row for row in board["items"] if row["decision_id"] == "bithumb_current_actionable_shadow_registration_action")
        self.assertEqual(item["status"], "SHADOW_REVIEW_REGISTERED")
        self.assertTrue(item["closed"])
        self.assertFalse(item["ready_for_human_review"])
        self.assertEqual(item["blockers"], [])
        self.assertFalse(board["board_permissions"]["shadow_registration_allowed_by_this_board"])

    def test_board_surfaces_shadow_registration_action_packet_without_permissions(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {"status": "HUMAN_GATEKEEPER_SHADOW_DECISION_RECORDED", "candidate_id": "candidate"},
            {},
            {},
            {"status": "PASS"},
            {
                "status": "READY_FOR_SHADOW_REGISTRATION_ACTION_REVIEW",
                "candidate_id": "candidate",
                "planned_shadow_registration": {
                    "candidate_id": "candidate",
                    "market": "KRW-POLA",
                    "estimated_cagr": 0.94,
                    "estimated_mdd": -0.2,
                },
                "blockers": [],
                "safety": {
                    "does_register_shadow_candidate": False,
                    "does_start_shadow_loop": False,
                    "does_enable_paper": False,
                    "does_enable_live": False,
                    "broker_submit_allowed_by_this_packet": False,
                    "private_submit_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                    "real_orders": 0,
                },
            },
        )

        action = next(
            item
            for item in board["items"]
            if item["decision_id"] == "bithumb_current_actionable_shadow_registration_action"
        )
        self.assertTrue(action["ready_for_human_review"])
        self.assertEqual(action["decision_type"], "shadow_registration_action_review")
        self.assertFalse(board["board_permissions"]["shadow_registration_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["real_orders_allowed_by_this_board"])

    def test_board_surfaces_bithumb_rollover_review_without_permissions(self) -> None:
        board = board_builder.build_board(
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "review_ready": True, "blockers": []},
            {"status": "INVALID_HUMAN_GATEKEEPER_DECISION", "candidate_id": "old"},
            {},
            {},
            {"status": "PASS"},
            {},
            {},
            {
                "status": "ROLLOVER_REVIEW_READY",
                "registered_candidate": {"candidate_id": "old"},
                "latest_oos_candidate": {"candidate_id": "new"},
                "comparison": {
                    "candidate_rollover_detected": True,
                    "registered_vs_latest_cagr_delta": 0.1,
                    "registered_vs_latest_mdd_delta": 0.0,
                    "latest_cagr_higher": True,
                    "latest_mdd_not_worse": True,
                },
                "blockers": ["FRESH_HUMAN_DECISION_REQUIRED_FOR_LATEST_OOS_CANDIDATE"],
                "safety": {
                    "does_register_shadow_candidate": False,
                    "does_start_shadow_loop": False,
                    "does_start_order_shadow_loop": False,
                    "does_emit_order_signal": False,
                    "does_write_order_intent": False,
                    "does_enable_paper": False,
                    "does_enable_live": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                    "real_orders": 0,
                },
            },
        )

        item = next(row for row in board["items"] if row["decision_id"] == "bithumb_current_actionable_shadow_rollover_review")
        self.assertTrue(item["ready_for_human_review"])
        self.assertEqual(item["candidate_id"], "new")
        self.assertEqual(item["decision_type"], "shadow_rollover_review")
        self.assertFalse(board["board_permissions"]["shadow_registration_allowed_by_this_board"])
        self.assertFalse(board["board_permissions"]["broker_submit_allowed_by_this_board"])


if __name__ == "__main__":
    unittest.main()
