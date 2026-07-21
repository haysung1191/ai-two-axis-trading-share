from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_gatekeeper_review_decision_phrase_packet.py")
SPEC = importlib.util.spec_from_file_location("build_gatekeeper_review_decision_phrase_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
packet_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_builder)


class GatekeeperReviewDecisionPhrasePacketTests(unittest.TestCase):
    def test_builds_exact_review_only_phrases_without_permissions(self) -> None:
        packet = packet_builder.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "next_decision": {"decision_id": "paper_smoke_review"},
                "items": [
                    {
                        "decision_id": "paper_smoke_review",
                        "decision_type": "gatekeeper_paper_smoke_review",
                        "candidate_id": "small_account_growth_paper",
                        "lane": "portfolio",
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_PAPER_SMOKE_ONLY",
                        "blockers": [],
                    },
                    {
                        "decision_id": "stock_conversion_review",
                        "decision_type": "conversion_evidence_review",
                        "candidate_id": "stock_candidate",
                        "lane": "kis_stock_etf",
                        "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_CONVERSION_EVIDENCE_ONLY",
                        "evidence_summary": {
                            "robustness_top5_target_count": 5,
                            "robustness_top5_covered_candidate_count": 5,
                            "robustness_top5_stress_pass_candidate_count": 3,
                            "sizing_repair_ready_count": 2,
                            "source_path": r"C:\AI\reports\model_factory\stock_conversion_gatekeeper_review_packet_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                            "private_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    },
                    {
                        "decision_id": "btc_eth_intraday_robustness_repair_review",
                        "decision_type": "btc_eth_intraday_robustness_repair_review",
                        "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001_robustrepair_445",
                        "lane": "btc_eth_intraday",
                        "status": "ROBUSTNESS_REPAIR_READY",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_BTC_ETH_INTRADAY_ROBUSTNESS_REPAIR_ONLY",
                        "evidence_summary": {
                            "best_cost_case_id": "cost_30bps",
                            "best_cost_total_return": 0.068,
                            "source_path": r"C:\AI\reports\model_factory\btc_eth_intraday_robustness_repair_review_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                            "private_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    },
                    {
                        "decision_id": "bridge_paper_safety_triage_review",
                        "decision_type": "bridge_paper_safety_triage_review",
                        "candidate_id": "bridge_28_relief",
                        "lane": "bithumb_1d",
                        "status": "BRIDGE_PAPER_SAFETY_TRIAGE_REVIEW_READY",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_BRIDGE_PAPER_SAFETY_TRIAGE_ONLY",
                        "evidence_summary": {
                            "failure_reason": "SIM_SAFETY_VIOLATION",
                            "candidate_remains_failed_for_promotion": True,
                            "source_path": r"C:\AI\reports\model_factory\bridge_paper_safety_triage_review_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    },
                    {
                        "decision_id": "bithumb_research_hold_triage_review",
                        "decision_type": "bithumb_research_hold_triage_review",
                        "candidate_id": "bithumb_research_hold_backtest_under_bar_batch",
                        "lane": "bithumb_1d",
                        "status": "BITHUMB_RESEARCH_HOLD_TRIAGE_REVIEW_READY",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_BITHUMB_RESEARCH_HOLD_TRIAGE_ONLY",
                        "evidence_summary": {
                            "research_hold_count": 3,
                            "recommended_action": "ARCHIVE_OR_REQUIRE_STRONGER_FROZEN_HYPOTHESIS",
                            "mutation_allowed_by_this_report": False,
                            "counts_as_paper_or_live_evidence": False,
                            "source_path": r"C:\AI\reports\model_factory\bithumb_research_hold_triage_review_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    },
                    {
                        "decision_id": "bithumb_current_actionable_dependency_relief_review",
                        "decision_type": "dependency_relief_evidence_review",
                        "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                        "lane": "bithumb_1d",
                        "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_DEPENDENCY_RELIEF_EVIDENCE_ONLY",
                        "evidence_summary": {
                            "registered_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354",
                            "relief_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                            "sweep1354_dependency_reduced_by_review_evidence": True,
                            "source_path": r"C:\AI\reports\model_factory\bithumb_current_actionable_dependency_relief_packet_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    },
                    {
                        "decision_id": "bithumb_current_actionable_orca_oos_family_review",
                        "decision_type": "orca_oos_family_evidence_review",
                        "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                        "lane": "bithumb_1d",
                        "status": "ORCA_OOS_FAMILY_REVIEW_READY",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_ORCA_OOS_FAMILY_EVIDENCE_ONLY",
                        "evidence_summary": {
                            "oos_pass_candidate_count": 6,
                            "distinct_parameter_count": 6,
                            "reduces_single_registered_candidate_dependency": True,
                            "source_path": r"C:\AI\reports\model_factory\bithumb_current_actionable_orca_oos_family_review_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    },
                    {
                        "decision_id": "stock_portfolio_sleeve_sensitivity_review",
                        "decision_type": "stock_portfolio_sleeve_sensitivity_review",
                        "candidate_id": "stock_etf_top5_sleeve_sensitivity",
                        "lane": "portfolio",
                        "status": "PORTFOLIO_SLEEVE_SENSITIVITY_REVIEW_READY",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_STOCK_PORTFOLIO_SLEEVE_SENSITIVITY_EVIDENCE_ONLY",
                        "evidence_summary": {
                            "scenario_count": 5,
                            "viable_scenario_count": 4,
                            "best_scenario_id": "etf_tilt_60_40",
                            "source_path": r"C:\AI\reports\model_factory\stock_portfolio_sleeve_sensitivity_review_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    },
                    {
                        "decision_id": "stock_portfolio_sleeve_resilience_review",
                        "decision_type": "stock_portfolio_sleeve_resilience_review",
                        "candidate_id": "stock_etf_top5_sleeve_leave_one_out_resilience",
                        "lane": "portfolio",
                        "status": "PORTFOLIO_SLEEVE_RESILIENCE_REVIEW_READY",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_STOCK_PORTFOLIO_SLEEVE_RESILIENCE_EVIDENCE_ONLY",
                        "evidence_summary": {
                            "scenario_count": 5,
                            "viable_scenario_count": 5,
                            "worst_leave_one_out_cagr": 0.435,
                            "source_path": r"C:\AI\reports\model_factory\stock_portfolio_sleeve_resilience_review_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    },
                    {
                        "decision_id": "stock_portfolio_sleeve_pairwise_resilience_review",
                        "decision_type": "stock_portfolio_sleeve_pairwise_resilience_review",
                        "candidate_id": "stock_etf_top5_sleeve_pairwise_resilience",
                        "lane": "portfolio",
                        "status": "PORTFOLIO_SLEEVE_PAIRWISE_RESILIENCE_REVIEW_READY",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_STOCK_PORTFOLIO_SLEEVE_PAIRWISE_RESILIENCE_ONLY",
                        "evidence_summary": {
                            "scenario_count": 10,
                            "viable_scenario_count": 9,
                            "fragile_scenario_count": 1,
                            "source_path": r"C:\AI\reports\model_factory\stock_portfolio_sleeve_pairwise_resilience_review_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    },
                    {
                        "decision_id": "stock_portfolio_sleeve_pairwise_fragility_repair_review",
                        "decision_type": "stock_portfolio_sleeve_pairwise_fragility_repair_review",
                        "candidate_id": "stock_etf_top5_sleeve_pairwise_fragility_repair",
                        "lane": "portfolio",
                        "status": "PORTFOLIO_SLEEVE_PAIRWISE_FRAGILITY_REPAIR_REVIEW_READY",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_STOCK_PORTFOLIO_SLEEVE_PAIRWISE_FRAGILITY_REPAIR_ONLY",
                        "evidence_summary": {
                            "scenario_count": 10,
                            "repaired_viable_scenario_count": 10,
                            "source_fragile_scenario_count": 1,
                            "source_path": r"C:\AI\reports\model_factory\stock_portfolio_sleeve_pairwise_fragility_repair_review_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    },
                    {
                        "decision_id": "bithumb_non_orca_widened_repair_stop_condition_review",
                        "decision_type": "non_orca_widened_stop_condition_review",
                        "candidate_id": "bio_widenedrepair_070",
                        "lane": "bithumb_1d",
                        "status": "NON_ORCA_WIDENED_REPAIR_STOP_CONDITION_READY",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_NON_ORCA_WIDENED_STOP_CONDITION_ONLY",
                        "evidence_summary": {
                            "trial_count": 162,
                            "oos_pass_trial_count": 0,
                            "robustness_pass_trial_count": 0,
                            "source_path": r"C:\AI\reports\model_factory\bithumb_non_orca_family_widened_repair_stop_condition_review_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    },
                    {
                        "decision_id": "bithumb_non_orca_entry_source_rebuild_review",
                        "decision_type": "non_orca_entry_source_rebuild_evidence_review",
                        "candidate_id": "pola_entrysource_029",
                        "lane": "bithumb_1d",
                        "status": "NON_ORCA_ENTRY_SOURCE_REBUILD_SWEEP_PASS",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_NON_ORCA_ENTRY_SOURCE_REBUILD_EVIDENCE_ONLY",
                        "evidence_summary": {
                            "trial_count": 162,
                            "oos_pass_trial_count": 33,
                            "robustness_pass_trial_count": 15,
                            "source_path": r"C:\AI\reports\model_factory\bithumb_non_orca_family_entry_source_rebuild_sweep_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    },
                    {
                        "decision_id": "bithumb_non_orca_entry_source_alternate_child_review",
                        "decision_type": "non_orca_entry_source_alternate_child_review",
                        "candidate_id": "pola_entrysource_032",
                        "lane": "bithumb_1d",
                        "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_NON_ORCA_ENTRY_SOURCE_ALTERNATE_CHILDREN_ONLY",
                        "evidence_summary": {
                            "primary_child_candidate_id": "pola_entrysource_029",
                            "top_alternate_candidate_id": "pola_entrysource_032",
                            "alternate_pass_child_count": 14,
                            "source_path": r"C:\AI\reports\model_factory\bithumb_non_orca_entry_source_alternate_child_packet_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    },
                    {
                        "decision_id": "btc_eth_intraday_low_turnover_followup_review",
                        "decision_type": "btc_eth_intraday_low_turnover_followup_review",
                        "candidate_id": "btc_eth_low_turnover_sweep080_followup159",
                        "lane": "btc_eth_intraday",
                        "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_BTC_ETH_INTRADAY_LOW_TURNOVER_FOLLOWUP_ONLY",
                        "evidence_summary": {
                            "sibling_pass_count": 5,
                            "best_cost_pass_count": 2,
                            "source_path": r"C:\AI\reports\model_factory\btc_eth_intraday_low_turnover_followup_gatekeeper_packet_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    },
                ],
            }
        )

        self.assertEqual(packet["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertEqual(packet["ready_phrase_count"], 15)
        self.assertEqual(packet["next_phrase"]["exact_phrase_to_record"], "REVIEW_PAPER_SMOKE_ONLY")
        self.assertFalse(packet["board_permissions"]["promotion_allowed_by_this_packet"])
        self.assertFalse(packet["board_permissions"]["shadow_registration_allowed_by_this_packet"])
        self.assertFalse(packet["board_permissions"]["paper_enabled_by_this_packet"])
        self.assertFalse(packet["board_permissions"]["live_allowed_by_this_packet"])
        self.assertFalse(packet["board_permissions"]["broker_submit_allowed_by_this_packet"])
        self.assertFalse(packet["board_permissions"]["real_orders_allowed_by_this_packet"])
        stock = next(item for item in packet["ready_phrases"] if item["decision_id"] == "stock_conversion_review")
        self.assertEqual(stock["evidence_summary"]["robustness_top5_target_count"], 5)
        self.assertEqual(stock["evidence_summary"]["robustness_top5_stress_pass_candidate_count"], 3)
        self.assertEqual(stock["evidence_summary"]["sizing_repair_ready_count"], 2)
        self.assertNotIn("source_path", stock["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", stock["evidence_summary"])
        self.assertNotIn("private_submit_allowed_by_this_report", stock["evidence_summary"])
        repair = next(
            item
            for item in packet["ready_phrases"]
            if item["decision_id"] == "btc_eth_intraday_robustness_repair_review"
        )
        self.assertEqual(repair["exact_phrase_to_record"], "REVIEW_BTC_ETH_INTRADAY_ROBUSTNESS_REPAIR_ONLY")
        self.assertEqual(repair["evidence_summary"]["best_cost_case_id"], "cost_30bps")
        self.assertNotIn("source_path", repair["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", repair["evidence_summary"])
        bridge = next(
            item
            for item in packet["ready_phrases"]
            if item["decision_id"] == "bridge_paper_safety_triage_review"
        )
        self.assertEqual(bridge["exact_phrase_to_record"], "REVIEW_BRIDGE_PAPER_SAFETY_TRIAGE_ONLY")
        self.assertTrue(bridge["evidence_summary"]["candidate_remains_failed_for_promotion"])
        self.assertNotIn("source_path", bridge["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", bridge["evidence_summary"])
        research_hold = next(
            item
            for item in packet["ready_phrases"]
            if item["decision_id"] == "bithumb_research_hold_triage_review"
        )
        self.assertEqual(research_hold["exact_phrase_to_record"], "REVIEW_BITHUMB_RESEARCH_HOLD_TRIAGE_ONLY")
        self.assertEqual(research_hold["evidence_summary"]["research_hold_count"], 3)
        self.assertEqual(
            research_hold["evidence_summary"]["recommended_action"],
            "ARCHIVE_OR_REQUIRE_STRONGER_FROZEN_HYPOTHESIS",
        )
        self.assertFalse(research_hold["evidence_summary"]["counts_as_paper_or_live_evidence"])
        self.assertNotIn("source_path", research_hold["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", research_hold["evidence_summary"])
        relief = next(
            item
            for item in packet["ready_phrases"]
            if item["decision_id"] == "bithumb_current_actionable_dependency_relief_review"
        )
        self.assertEqual(relief["exact_phrase_to_record"], "REVIEW_DEPENDENCY_RELIEF_EVIDENCE_ONLY")
        self.assertTrue(relief["evidence_summary"]["sweep1354_dependency_reduced_by_review_evidence"])
        self.assertNotIn("source_path", relief["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", relief["evidence_summary"])
        orca = next(
            item
            for item in packet["ready_phrases"]
            if item["decision_id"] == "bithumb_current_actionable_orca_oos_family_review"
        )
        self.assertEqual(orca["exact_phrase_to_record"], "REVIEW_ORCA_OOS_FAMILY_EVIDENCE_ONLY")
        self.assertEqual(orca["evidence_summary"]["oos_pass_candidate_count"], 6)
        self.assertNotIn("source_path", orca["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", orca["evidence_summary"])
        sensitivity = next(
            item
            for item in packet["ready_phrases"]
            if item["decision_id"] == "stock_portfolio_sleeve_sensitivity_review"
        )
        self.assertEqual(
            sensitivity["exact_phrase_to_record"],
            "REVIEW_STOCK_PORTFOLIO_SLEEVE_SENSITIVITY_EVIDENCE_ONLY",
        )
        self.assertEqual(sensitivity["evidence_summary"]["scenario_count"], 5)
        self.assertEqual(sensitivity["evidence_summary"]["viable_scenario_count"], 4)
        self.assertNotIn("source_path", sensitivity["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", sensitivity["evidence_summary"])
        resilience = next(
            item
            for item in packet["ready_phrases"]
            if item["decision_id"] == "stock_portfolio_sleeve_resilience_review"
        )
        self.assertEqual(
            resilience["exact_phrase_to_record"],
            "REVIEW_STOCK_PORTFOLIO_SLEEVE_RESILIENCE_EVIDENCE_ONLY",
        )
        self.assertEqual(resilience["evidence_summary"]["scenario_count"], 5)
        self.assertEqual(resilience["evidence_summary"]["viable_scenario_count"], 5)
        self.assertNotIn("source_path", resilience["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", resilience["evidence_summary"])
        pairwise = next(
            item
            for item in packet["ready_phrases"]
            if item["decision_id"] == "stock_portfolio_sleeve_pairwise_resilience_review"
        )
        self.assertEqual(
            pairwise["exact_phrase_to_record"],
            "REVIEW_STOCK_PORTFOLIO_SLEEVE_PAIRWISE_RESILIENCE_ONLY",
        )
        self.assertEqual(pairwise["evidence_summary"]["scenario_count"], 10)
        self.assertEqual(pairwise["evidence_summary"]["fragile_scenario_count"], 1)
        self.assertNotIn("source_path", pairwise["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", pairwise["evidence_summary"])
        pairwise_repair = next(
            item
            for item in packet["ready_phrases"]
            if item["decision_id"] == "stock_portfolio_sleeve_pairwise_fragility_repair_review"
        )
        self.assertEqual(
            pairwise_repair["exact_phrase_to_record"],
            "REVIEW_STOCK_PORTFOLIO_SLEEVE_PAIRWISE_FRAGILITY_REPAIR_ONLY",
        )
        self.assertEqual(pairwise_repair["evidence_summary"]["scenario_count"], 10)
        self.assertEqual(pairwise_repair["evidence_summary"]["repaired_viable_scenario_count"], 10)
        self.assertNotIn("source_path", pairwise_repair["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", pairwise_repair["evidence_summary"])
        non_orca_stop = next(
            item
            for item in packet["ready_phrases"]
            if item["decision_id"] == "bithumb_non_orca_widened_repair_stop_condition_review"
        )
        self.assertEqual(non_orca_stop["exact_phrase_to_record"], "REVIEW_NON_ORCA_WIDENED_STOP_CONDITION_ONLY")
        self.assertEqual(non_orca_stop["evidence_summary"]["trial_count"], 162)
        self.assertNotIn("source_path", non_orca_stop["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", non_orca_stop["evidence_summary"])
        non_orca_rebuild = next(
            item
            for item in packet["ready_phrases"]
            if item["decision_id"] == "bithumb_non_orca_entry_source_rebuild_review"
        )
        self.assertEqual(non_orca_rebuild["exact_phrase_to_record"], "REVIEW_NON_ORCA_ENTRY_SOURCE_REBUILD_EVIDENCE_ONLY")
        self.assertEqual(non_orca_rebuild["evidence_summary"]["robustness_pass_trial_count"], 15)
        self.assertNotIn("source_path", non_orca_rebuild["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", non_orca_rebuild["evidence_summary"])
        non_orca_alternate = next(
            item
            for item in packet["ready_phrases"]
            if item["decision_id"] == "bithumb_non_orca_entry_source_alternate_child_review"
        )
        self.assertEqual(
            non_orca_alternate["exact_phrase_to_record"],
            "REVIEW_NON_ORCA_ENTRY_SOURCE_ALTERNATE_CHILDREN_ONLY",
        )
        self.assertEqual(non_orca_alternate["evidence_summary"]["top_alternate_candidate_id"], "pola_entrysource_032")
        self.assertNotIn("source_path", non_orca_alternate["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", non_orca_alternate["evidence_summary"])
        low_turnover_followup = next(
            item
            for item in packet["ready_phrases"]
            if item["decision_id"] == "btc_eth_intraday_low_turnover_followup_review"
        )
        self.assertEqual(
            low_turnover_followup["exact_phrase_to_record"],
            "REVIEW_BTC_ETH_INTRADAY_LOW_TURNOVER_FOLLOWUP_ONLY",
        )
        self.assertEqual(low_turnover_followup["evidence_summary"]["sibling_pass_count"], 5)
        self.assertEqual(low_turnover_followup["evidence_summary"]["best_cost_pass_count"], 2)
        self.assertNotIn("source_path", low_turnover_followup["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", low_turnover_followup["evidence_summary"])

    def test_phrase_packet_allows_orca_repair_stop_condition_review_only(self) -> None:
        packet = packet_builder.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "next_decision": {"decision_id": "bithumb_current_actionable_orca_repair_stop_condition_review"},
                "items": [
                    {
                        "decision_id": "bithumb_current_actionable_orca_repair_stop_condition_review",
                        "decision_type": "orca_repair_stop_condition_review",
                        "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                        "lane": "bithumb_1d",
                        "status": "ORCA_REPAIR_STOP_CONDITION_REVIEW_READY",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_ORCA_REPAIR_STOP_CONDITION_ONLY",
                        "evidence_summary": {
                            "total_seed_count": 6,
                            "recommended_branch_action": "STOP_ORCA_REPAIR_BRANCH_AUTOMATION",
                            "source_path": r"C:\AI\reports\model_factory\bithumb_current_actionable_orca_repair_stop_condition_review_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    }
                ],
            }
        )

        self.assertEqual(packet["ready_phrase_count"], 1)
        self.assertEqual(packet["next_phrase"]["exact_phrase_to_record"], "REVIEW_ORCA_REPAIR_STOP_CONDITION_ONLY")
        self.assertNotIn("source_path", packet["next_phrase"]["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", packet["next_phrase"]["evidence_summary"])

    def test_phrase_packet_allows_bithumb_gatekeeper_blocker_triage_review_only(self) -> None:
        packet = packet_builder.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "next_decision": {"decision_id": "bithumb_current_actionable_gatekeeper_blocker_triage_review"},
                "items": [
                    {
                        "decision_id": "bithumb_current_actionable_gatekeeper_blocker_triage_review",
                        "decision_type": "bithumb_gatekeeper_blocker_triage_review",
                        "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                        "lane": "bithumb_1d",
                        "status": "BITHUMB_GATEKEEPER_BLOCKER_TRIAGE_REVIEW_READY",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_BITHUMB_GATEKEEPER_BLOCKER_TRIAGE_ONLY",
                        "evidence_summary": {
                            "robustness_pass_count": 0,
                            "source_path": r"C:\AI\reports\model_factory\bithumb_current_actionable_gatekeeper_blocker_triage_review_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    }
                ],
            }
        )

        self.assertEqual(packet["ready_phrase_count"], 1)
        self.assertEqual(
            packet["next_phrase"]["exact_phrase_to_record"],
            "REVIEW_BITHUMB_GATEKEEPER_BLOCKER_TRIAGE_ONLY",
        )
        self.assertNotIn("source_path", packet["next_phrase"]["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", packet["next_phrase"]["evidence_summary"])

    def test_phrase_packet_allows_btc_eth_oos_stability_plateau_review_only(self) -> None:
        packet = packet_builder.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "next_decision": {"decision_id": "btc_eth_intraday_oos_stability_plateau_review"},
                "items": [
                    {
                        "decision_id": "btc_eth_intraday_oos_stability_plateau_review",
                        "decision_type": "btc_eth_intraday_oos_stability_plateau_review",
                        "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                        "lane": "btc_eth_intraday",
                        "status": "BTC_ETH_INTRADAY_OOS_STABILITY_PLATEAU_REVIEW_READY",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_BTC_ETH_INTRADAY_OOS_STABILITY_PLATEAU_ONLY",
                        "evidence_summary": {
                            "stability_pass_count": 3,
                            "best_improves_current": False,
                            "source_path": r"C:\AI\reports\model_factory\btc_eth_intraday_oos_stability_plateau_review_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    }
                ],
            }
        )

        self.assertEqual(packet["ready_phrase_count"], 1)
        self.assertEqual(
            packet["next_phrase"]["exact_phrase_to_record"],
            "REVIEW_BTC_ETH_INTRADAY_OOS_STABILITY_PLATEAU_ONLY",
        )
        self.assertNotIn("source_path", packet["next_phrase"]["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", packet["next_phrase"]["evidence_summary"])

    def test_phrase_packet_allows_btc_eth_cost_friction_review_only(self) -> None:
        packet = packet_builder.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "next_decision": {"decision_id": "btc_eth_intraday_cost_friction_review"},
                "items": [
                    {
                        "decision_id": "btc_eth_intraday_cost_friction_review",
                        "decision_type": "btc_eth_intraday_cost_friction_review",
                        "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                        "lane": "btc_eth_intraday",
                        "status": "BTC_ETH_INTRADAY_COST_FRICTION_REVIEW_READY",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_BTC_ETH_INTRADAY_COST_FRICTION_ONLY",
                        "evidence_summary": {
                            "cost_pass_count": 0,
                            "source_path": r"C:\AI\reports\model_factory\btc_eth_intraday_cost_friction_review_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    }
                ],
            }
        )

        self.assertEqual(packet["ready_phrase_count"], 1)
        self.assertEqual(packet["next_phrase"]["exact_phrase_to_record"], "REVIEW_BTC_ETH_INTRADAY_COST_FRICTION_ONLY")
        self.assertNotIn("source_path", packet["next_phrase"]["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", packet["next_phrase"]["evidence_summary"])

    def test_phrase_packet_allows_bithumb_alternate_robustness_failure_review_only(self) -> None:
        packet = packet_builder.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "next_decision": {"decision_id": "bithumb_current_actionable_alternate_robustness_failure_review"},
                "items": [
                    {
                        "decision_id": "bithumb_current_actionable_alternate_robustness_failure_review",
                        "decision_type": "bithumb_alternate_robustness_failure_review",
                        "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                        "lane": "bithumb_1d",
                        "status": "BITHUMB_ALTERNATE_ROBUSTNESS_FAILURE_REVIEW_READY",
                        "ready_for_human_review": True,
                        "recommended_decision": "REVIEW_BITHUMB_ALTERNATE_ROBUSTNESS_FAILURE_ONLY",
                        "evidence_summary": {
                            "evaluated_oos_pass_candidate_count": 6,
                            "robustness_pass_candidate_count": 0,
                            "source_path": r"C:\AI\reports\model_factory\bithumb_current_actionable_alternate_robustness_failure_review_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    }
                ],
            }
        )

        self.assertEqual(packet["ready_phrase_count"], 1)
        self.assertEqual(
            packet["next_phrase"]["exact_phrase_to_record"],
            "REVIEW_BITHUMB_ALTERNATE_ROBUSTNESS_FAILURE_ONLY",
        )
        self.assertEqual(packet["next_phrase"]["evidence_summary"]["robustness_pass_candidate_count"], 0)
        self.assertNotIn("source_path", packet["next_phrase"]["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", packet["next_phrase"]["evidence_summary"])

    def test_shadow_review_phrase_is_approval_or_reject_or_defer_only(self) -> None:
        packet = packet_builder.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "next_decision": {"decision_id": "btc_eth_intraday_shadow_review"},
                "items": [
                    {
                        "decision_id": "btc_eth_intraday_shadow_review",
                        "decision_type": "shadow_registration_review",
                        "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                        "lane": "btc_eth_1h4h",
                        "status": "PENDING_HUMAN_GATEKEEPER_DECISION",
                        "ready_for_human_review": True,
                        "recommended_decision": "DEFER_OR_APPROVE_SHADOW_REVIEW_ONLY",
                        "human_decision_path": r"C:\AI\reports\model_factory\btc_eth_intraday_shadow_gatekeeper_decision.json",
                        "human_decision_present": True,
                        "human_decision_valid": False,
                        "recorded_candidate_id": "stale_candidate",
                        "decision_candidate_match": False,
                        "human_decision_draft_status": "DRAFT_READY",
                        "human_decision_draft_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                        "human_decision_draft_path": r"C:\AI\reports\model_factory\btc_eth_intraday_shadow_gatekeeper_decision_draft.json",
                        "blockers": ["HUMAN_GATEKEEPER_SHADOW_DECISION_MISSING"],
                    }
                ],
            }
        )

        self.assertEqual(packet["next_phrase"]["exact_phrase_to_record"], "APPROVE_SHADOW_REVIEW_ONLY")
        self.assertEqual(packet["next_phrase"]["alternate_allowed_phrases"], ["REJECT", "DEFER"])
        self.assertIn("does not register", packet["next_phrase"]["review_only_effect"])
        self.assertEqual(packet["next_phrase"]["human_decision_state"]["expected_candidate_id"], "btc_eth_intraday_momentum_btc_4h_sweep001")
        self.assertEqual(packet["next_phrase"]["human_decision_state"]["recorded_candidate_id"], "stale_candidate")
        self.assertFalse(packet["next_phrase"]["human_decision_state"]["human_decision_valid"])
        self.assertFalse(packet["next_phrase"]["human_decision_state"]["decision_candidate_match"])
        self.assertEqual(packet["next_phrase"]["human_decision_draft_status"], "DRAFT_READY")
        self.assertEqual(packet["next_phrase"]["human_decision_draft_candidate_id"], "btc_eth_intraday_momentum_btc_4h_sweep001")
        self.assertTrue(str(packet["next_phrase"]["human_decision_draft_path"]).endswith("btc_eth_intraday_shadow_gatekeeper_decision_draft.json"))
        self.assertFalse(packet["board_permissions"]["shadow_registration_allowed_by_this_packet"])

    def test_blocks_when_no_ready_review_only_phrases_exist(self) -> None:
        packet = packet_builder.build_packet(
            {
                "status": "BLOCKED",
                "items": [
                    {
                        "decision_id": "blocked_action",
                        "candidate_id": "candidate",
                        "status": "BLOCKED",
                        "ready_for_human_review": False,
                        "recommended_decision": "REVIEW_ACTION_PACKET_ONLY",
                        "blockers": ["missing_approval"],
                    }
                ],
            }
        )

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertEqual(packet["ready_phrase_count"], 0)
        self.assertEqual(packet["blocked_decision_count"], 1)


if __name__ == "__main__":
    unittest.main()
