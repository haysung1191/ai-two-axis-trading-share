from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_gatekeeper_decision_priority_report.py")
SPEC = importlib.util.spec_from_file_location("build_gatekeeper_decision_priority_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
priority = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(priority)


class GatekeeperDecisionPriorityReportTests(unittest.TestCase):
    def test_prioritizes_ready_review_only_decisions_without_permissions(self) -> None:
        board = {
            "items": [
                {
                    "decision_id": "stock_conversion_review",
                    "decision_type": "conversion_evidence_review",
                    "candidate_id": "stock_candidate",
                    "lane": "kis_stock_etf",
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "ready_for_human_review": True,
                    "exact_phrase_to_record": "REVIEW_CONVERSION_EVIDENCE_ONLY",
                    "evidence_summary": {
                        "estimated_cagr": 0.45,
                        "source_path": r"C:\AI\reports\model_factory\stock.json",
                        "broker_submit_allowed_by_this_report": False,
                    },
                    "blockers": [],
                },
                {
                    "decision_id": "bithumb_non_orca_entry_source_rebuild_review",
                    "decision_type": "non_orca_entry_source_rebuild_evidence_review",
                    "candidate_id": "pola_entrysource_029",
                    "lane": "bithumb_1d",
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "ready_for_human_review": True,
                    "exact_phrase_to_record": "REVIEW_NON_ORCA_ENTRY_SOURCE_REBUILD_EVIDENCE_ONLY",
                    "evidence_summary": {
                        "estimated_cagr": 1.79,
                        "source_path": r"C:\AI\reports\model_factory\bithumb_non_orca_entry_source.json",
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
                    "exact_phrase_to_record": "REVIEW_NON_ORCA_ENTRY_SOURCE_ALTERNATE_CHILDREN_ONLY",
                    "evidence_summary": {
                        "alternate_pass_child_count": 14,
                        "source_path": r"C:\AI\reports\model_factory\bithumb_non_orca_alternate.json",
                        "broker_submit_allowed_by_this_report": False,
                    },
                    "blockers": [],
                },
                {
                    "decision_id": "btc_eth_intraday_robustness_repair_alternate_child_review",
                    "decision_type": "btc_eth_intraday_robustness_repair_alternate_child_review",
                    "candidate_id": "repair_441",
                    "lane": "btc_eth_intraday",
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "ready_for_human_review": True,
                    "exact_phrase_to_record": "REVIEW_BTC_ETH_INTRADAY_ALTERNATE_REPAIR_CHILDREN_ONLY",
                    "evidence_summary": {
                        "alternate_pass_child_count": 41,
                        "source_path": r"C:\AI\reports\model_factory\btc_eth_alternates.json",
                    },
                    "blockers": [],
                },
                {
                    "decision_id": "bithumb_current_actionable_dependency_relief_review",
                    "decision_type": "dependency_relief_evidence_review",
                    "candidate_id": "pola_sweep1355",
                    "lane": "bithumb_1d",
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "ready_for_human_review": True,
                    "exact_phrase_to_record": "REVIEW_DEPENDENCY_RELIEF_EVIDENCE_ONLY",
                    "evidence_summary": {"sweep1354_dependency_reduced_by_review_evidence": True},
                    "blockers": [],
                },
                {
                    "decision_id": "stock_portfolio_sleeve_review",
                    "decision_type": "stock_portfolio_sleeve_review",
                    "candidate_id": "stock_etf_top5_equal_weight_sleeve",
                    "lane": "portfolio",
                    "status": "PORTFOLIO_SLEEVE_REVIEW_READY",
                    "ready_for_human_review": True,
                    "exact_phrase_to_record": "REVIEW_STOCK_PORTFOLIO_SLEEVE_EVIDENCE_ONLY",
                    "evidence_summary": {"component_count": 5},
                    "blockers": [],
                },
                {
                    "decision_id": "stock_portfolio_sleeve_sensitivity_review",
                    "decision_type": "stock_portfolio_sleeve_sensitivity_review",
                    "candidate_id": "stock_etf_top5_sleeve_sensitivity",
                    "lane": "portfolio",
                    "status": "PORTFOLIO_SLEEVE_SENSITIVITY_REVIEW_READY",
                    "ready_for_human_review": True,
                    "exact_phrase_to_record": "REVIEW_STOCK_PORTFOLIO_SLEEVE_SENSITIVITY_EVIDENCE_ONLY",
                    "evidence_summary": {
                        "scenario_count": 5,
                        "source_path": r"C:\AI\reports\model_factory\stock_portfolio_sleeve_sensitivity.json",
                        "broker_submit_allowed_by_this_report": False,
                    },
                    "blockers": [],
                },
                {
                    "decision_id": "paper_smoke_review",
                    "decision_type": "gatekeeper_paper_smoke_review",
                    "candidate_id": "small_account_growth_paper",
                    "lane": "portfolio",
                    "status": "READY_FOR_GATEKEEPER_REVIEW",
                    "ready_for_human_review": True,
                    "exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                    "evidence_summary": {"paper_cycles_completed": 252},
                    "blockers": [],
                },
                {
                    "decision_id": "blocked_action",
                    "decision_type": "shadow_registration_action_review",
                    "candidate_id": "candidate",
                    "status": "BLOCKED",
                    "ready_for_human_review": False,
                    "blockers": ["missing_decision"],
                },
            ]
        }
        phrase_packet = {
            "ready_phrases": [
                {
                    "decision_id": "paper_smoke_review",
                    "exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                    "review_only_effect": "Records evidence review only.",
                },
                {
                    "decision_id": "stock_conversion_review",
                    "exact_phrase_to_record": "REVIEW_CONVERSION_EVIDENCE_ONLY",
                    "review_only_effect": "Records evidence review only.",
                },
                {
                    "decision_id": "bithumb_non_orca_entry_source_rebuild_review",
                    "exact_phrase_to_record": "REVIEW_NON_ORCA_ENTRY_SOURCE_REBUILD_EVIDENCE_ONLY",
                    "review_only_effect": "Records evidence review only.",
                },
                {
                    "decision_id": "btc_eth_intraday_robustness_repair_alternate_child_review",
                    "exact_phrase_to_record": "REVIEW_BTC_ETH_INTRADAY_ALTERNATE_REPAIR_CHILDREN_ONLY",
                    "review_only_effect": "Records evidence review only.",
                },
                {
                    "decision_id": "bithumb_current_actionable_dependency_relief_review",
                    "exact_phrase_to_record": "REVIEW_DEPENDENCY_RELIEF_EVIDENCE_ONLY",
                    "review_only_effect": "Records evidence review only.",
                },
                {
                    "decision_id": "stock_portfolio_sleeve_review",
                    "exact_phrase_to_record": "REVIEW_STOCK_PORTFOLIO_SLEEVE_EVIDENCE_ONLY",
                    "review_only_effect": "Records evidence review only.",
                },
                {
                    "decision_id": "stock_portfolio_sleeve_sensitivity_review",
                    "exact_phrase_to_record": "REVIEW_STOCK_PORTFOLIO_SLEEVE_SENSITIVITY_EVIDENCE_ONLY",
                    "review_only_effect": "Records evidence review only.",
                },
            ]
        }

        report = priority.build_report(board, phrase_packet)

        self.assertEqual(report["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertEqual(report["ready_decision_count"], 8)
        self.assertEqual(report["blocked_decision_count"], 1)
        self.assertEqual(report["next_decision"]["decision_id"], "paper_smoke_review")
        self.assertEqual(report["next_decision"]["exact_phrase_to_record"], "REVIEW_PAPER_SMOKE_ONLY")
        stock = next(row for row in report["ready_decisions"] if row["decision_id"] == "stock_conversion_review")
        self.assertEqual(stock["evidence_summary"]["estimated_cagr"], 0.45)
        self.assertNotIn("source_path", stock["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", stock["evidence_summary"])
        entry_source = next(
            row for row in report["ready_decisions"] if row["decision_id"] == "bithumb_non_orca_entry_source_rebuild_review"
        )
        self.assertEqual(entry_source["priority_score"], 84)
        self.assertEqual(
            entry_source["exact_phrase_to_record"],
            "REVIEW_NON_ORCA_ENTRY_SOURCE_REBUILD_EVIDENCE_ONLY",
        )
        self.assertIn("entry/source rebuild", entry_source["priority_reason"])
        self.assertNotIn("source_path", entry_source["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", entry_source["evidence_summary"])
        entry_source_alternate = next(
            row
            for row in report["ready_decisions"]
            if row["decision_id"] == "bithumb_non_orca_entry_source_alternate_child_review"
        )
        self.assertEqual(entry_source_alternate["priority_score"], 83)
        self.assertEqual(
            entry_source_alternate["exact_phrase_to_record"],
            "REVIEW_NON_ORCA_ENTRY_SOURCE_ALTERNATE_CHILDREN_ONLY",
        )
        self.assertIn("alternate robustness-passing children", entry_source_alternate["priority_reason"])
        self.assertNotIn("source_path", entry_source_alternate["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", entry_source_alternate["evidence_summary"])
        alternate = next(
            row
            for row in report["ready_decisions"]
            if row["decision_id"] == "btc_eth_intraday_robustness_repair_alternate_child_review"
        )
        self.assertEqual(alternate["priority_score"], 89)
        self.assertEqual(
            alternate["exact_phrase_to_record"],
            "REVIEW_BTC_ETH_INTRADAY_ALTERNATE_REPAIR_CHILDREN_ONLY",
        )
        self.assertIn("reliance", alternate["priority_reason"])
        self.assertNotIn("source_path", alternate["evidence_summary"])
        relief = next(
            row for row in report["ready_decisions"] if row["decision_id"] == "bithumb_current_actionable_dependency_relief_review"
        )
        self.assertEqual(relief["priority_score"], 82)
        self.assertEqual(relief["exact_phrase_to_record"], "REVIEW_DEPENDENCY_RELIEF_EVIDENCE_ONLY")
        sleeve = next(row for row in report["ready_decisions"] if row["decision_id"] == "stock_portfolio_sleeve_review")
        self.assertEqual(sleeve["priority_score"], 76)
        self.assertEqual(sleeve["evidence_summary"]["component_count"], 5)
        sensitivity = next(
            row for row in report["ready_decisions"] if row["decision_id"] == "stock_portfolio_sleeve_sensitivity_review"
        )
        self.assertEqual(
            sensitivity["exact_phrase_to_record"],
            "REVIEW_STOCK_PORTFOLIO_SLEEVE_SENSITIVITY_EVIDENCE_ONLY",
        )
        self.assertEqual(sensitivity["priority_score"], 75)
        self.assertEqual(sensitivity["evidence_summary"]["scenario_count"], 5)
        self.assertNotIn("source_path", sensitivity["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", sensitivity["evidence_summary"])
        self.assertFalse(report["board_permissions"]["promotion_allowed_by_this_report"])
        self.assertFalse(report["board_permissions"]["shadow_registration_allowed_by_this_report"])
        self.assertFalse(report["board_permissions"]["paper_enabled_by_this_report"])
        self.assertFalse(report["board_permissions"]["live_allowed_by_this_report"])
        self.assertFalse(report["board_permissions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["board_permissions"]["real_orders_allowed_by_this_report"])

    def test_blocks_when_no_ready_decisions_exist(self) -> None:
        report = priority.build_report(
            {
                "items": [
                    {
                        "decision_id": "blocked_action",
                        "status": "BLOCKED",
                        "ready_for_human_review": False,
                        "blockers": ["missing_decision"],
                    }
                ]
            },
            {"ready_phrases": []},
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["ready_decision_count"], 0)
        self.assertEqual(report["blocked_decision_count"], 1)
        self.assertIsNone(report["next_decision"])


if __name__ == "__main__":
    unittest.main()
