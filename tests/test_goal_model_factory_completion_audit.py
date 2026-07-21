from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_goal_model_factory_completion_audit.py")
SPEC = importlib.util.spec_from_file_location("build_goal_model_factory_completion_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_builder)


class GoalModelFactoryCompletionAuditTests(unittest.TestCase):
    def test_progress_summary_separates_entry_count_from_latest_iteration_number(self) -> None:
        summary = audit_builder.progress_iteration_summary(
            "## 2026-05-04 Iteration 130 Result\n"
            "done\n"
            "## 2026-05-03 Iteration 79 Result\n"
            "done\n"
            "## 2026-05-03 Iteration 79 Result\n"
        )

        self.assertEqual(summary["progress_entry_count"], 3)
        self.assertEqual(summary["latest_iteration_number"], 130)
        self.assertEqual(summary["latest_iteration_heading"], "## 2026-05-04 Iteration 130 Result")

    def test_audit_not_complete_when_paper_evidence_gaps_remain(self) -> None:
        audit = audit_builder.build_audit(
            {
                "decision": "KEEP_PAPER_COLLECT_EVIDENCE",
                "evidence_gaps": ["INSUFFICIENT_NON_FLAT_SIGNAL_EVIDENCE"],
                "thresholds": {
                    "min_cycles_for_promotion_review": 288,
                    "min_non_flat_signals_for_promotion": 5,
                    "min_executable_orders_for_promotion": 5,
                },
                "evidence": {
                    "paper_cycles_completed": 146,
                    "paper_safety": {
                        "broker_submit_scope": "paper_only",
                    },
                    "combined_evidence": {
                        "combined_non_flat_signal_count": 2,
                        "combined_executable_order_evidence_count": 2,
                    },
                },
            },
            {
                "gap_summary": {
                    "paper_cycles_missing": 142,
                    "non_flat_signals_missing": 3,
                    "executable_orders_missing": 3,
                },
                "readiness_summary": {
                    "paper_evidence_readiness_percent": 40.0,
                    "dominant_blocking_dimensions": ["non_flat_signals", "executable_orders"],
                    "promotion_review_ready": False,
                },
                "velocity_proximity_summary": {
                    "nearest_flat_target": {
                        "market": "KRW-ETH",
                        "timeframe": "1h",
                        "non_flat_trigger_gap": 0.0015,
                        "broker_submit_allowed": False,
                    }
                },
                "safety": {
                    "historical_replay_counts_as_promotion_evidence": False,
                    "historical_replay_excluded": True,
                },
            },
            {
                "status": "COLLECT_EVIDENCE",
                "current": {"paper_cycles_completed": 146},
                "delta_from_previous": {"paper_cycles_delta": 1, "non_flat_delta": 0, "executable_delta": 0},
                "pace_summary": {
                    "eta_status": "STALLED_ON_EVENT_EVIDENCE",
                    "slowest_gate_dimension": "non_flat_signals",
                    "estimated_hours_to_cycle_target": 9.5,
                    "promotion_review_eta_hours": None,
                },
                "event_stall_summary": {
                    "event_stall_status": "EVENT_EVIDENCE_STALLED",
                    "stall_severity": "WARN_STALL",
                    "safe_next_action": "Continue safe paper loop, but monitor nearest flat target and stall age closely.",
                    "non_flat_signals": {
                        "hours_since_last_increase": 2.0,
                        "paper_cycles_since_last_increase": 24,
                    },
                    "executable_orders": {
                        "hours_since_last_increase": 2.0,
                        "paper_cycles_since_last_increase": 24,
                    },
                },
                "history_count": 2,
            },
            {"status": "PASS", "halt_count": 0, "warn_count": 0},
            {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "blockers": [],
                "proposed_conversion": {"estimated_cagr": 0.459, "estimated_mdd": -0.199},
                "no_order_assertions": {
                    "live_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "target_count": 5,
                "ready_candidate_count": 5,
                "blocked_candidate_count": 0,
                "no_order_assertions": {
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            {
                "status": "PASS",
                "gatekeeper_action_packet": {
                    "promotion_allowed_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            {
                "status": "PASS",
                "current_decision": {
                    "recommended_gatekeeper_lane": "COLLECT_MORE_REPLAY_OR_LIVE_LIKE_BREADTH",
                    "pipeline_can_advance_without_waiting_for_5_of_5": False,
                    "live_or_real_order_allowed": False,
                },
                "taxonomy": {
                    "paper_smoke_evidence": {"ready": False, "can_advance_to": "KEEP_SMOKE_COLLECTION"},
                    "extended_paper_evidence": {"ready": False, "can_advance_to": "KEEP_EXTENDED_PAPER_COLLECTION"},
                },
            },
            {"status": "WARN", "blockers": [], "warnings": []},
            "## Iteration 1\n",
        )

        self.assertEqual(audit["status"], "NOT_COMPLETE")
        self.assertFalse(audit["completion_allowed"])
        self.assertEqual(audit["incomplete_count"], 1)
        self.assertEqual(audit["first_incomplete_requirement"], "Advance via paper-smoke evidence while extended paper evidence continues")
        self.assertEqual(audit["pass_count"], audit["total_count"] - 1)
        self.assertEqual(audit["progress_summary"]["latest_iteration_number"], 1)
        self.assertEqual(audit["progress_summary"]["latest_iteration_heading"], "## Iteration 1")
        progress_check = next(
            check for check in audit["checks"] if check["requirement"] == "Maintain file-backed progress and checkpoint record"
        )
        self.assertEqual(progress_check["evidence"]["progress_entry_count"], 1)
        self.assertEqual(progress_check["evidence"]["latest_iteration_number"], 1)
        self.assertEqual(len(audit["missing_or_incomplete"]), 1)
        self.assertEqual(
            audit["missing_or_incomplete"][0]["requirement"],
            "Advance via paper-smoke evidence while extended paper evidence continues",
        )
        blocker = audit["completion_blocker_summary"]
        self.assertEqual(blocker["status"], "BLOCKED")
        self.assertEqual(
            blocker["primary_blocker"],
            "Advance via paper-smoke evidence while extended paper evidence continues",
        )
        self.assertEqual(blocker["paper_evidence_remaining"]["paper_cycles_target"], 288)
        self.assertEqual(blocker["paper_evidence_remaining"]["paper_cycles_missing"], 142)
        self.assertEqual(blocker["paper_evidence_remaining"]["non_flat_signals_missing"], 3)
        self.assertEqual(blocker["paper_evidence_remaining"]["executable_orders_missing"], 3)
        self.assertEqual(blocker["paper_evidence_remaining"]["paper_evidence_readiness_percent"], 40.0)
        self.assertEqual(
            blocker["paper_evidence_remaining"]["dominant_blocking_dimensions"],
            ["non_flat_signals", "executable_orders"],
        )
        self.assertFalse(blocker["paper_evidence_remaining"]["promotion_review_ready"])
        self.assertEqual(
            blocker["paper_evidence_remaining"]["pace_summary"]["eta_status"],
            "STALLED_ON_EVENT_EVIDENCE",
        )
        self.assertEqual(
            blocker["paper_evidence_remaining"]["pace_summary"]["slowest_gate_dimension"],
            "non_flat_signals",
        )
        self.assertIsNone(
            blocker["paper_evidence_remaining"]["pace_summary"]["promotion_review_eta_hours"]
        )
        self.assertEqual(
            blocker["paper_evidence_remaining"]["event_stall_summary"]["event_stall_status"],
            "EVENT_EVIDENCE_STALLED",
        )
        self.assertEqual(
            blocker["paper_evidence_remaining"]["event_stall_summary"]["stall_severity"],
            "WARN_STALL",
        )
        self.assertEqual(
            blocker["paper_evidence_remaining"]["event_stall_summary"]["non_flat_signals"]["hours_since_last_increase"],
            2.0,
        )
        self.assertEqual(
            blocker["paper_evidence_remaining"]["velocity_proximity_summary"]["nearest_flat_target"]["market"],
            "KRW-ETH",
        )
        self.assertFalse(blocker["safety"]["historical_replay_counts_as_promotion_evidence"])
        self.assertEqual(blocker["safety"]["broker_submit_scope"], "paper_only")
        self.assertFalse(blocker["safety"]["broker_submit_allowed"])

        rendered = audit_builder.render_markdown(audit)
        self.assertIn("broker_submit_scope: `paper_only`", rendered)
        self.assertIn("broker_submit_allowed: `False`", rendered)
        self.assertIn("pace_eta_status: `STALLED_ON_EVENT_EVIDENCE`", rendered)
        self.assertIn("slowest_gate_dimension: `non_flat_signals`", rendered)
        self.assertIn("promotion_review_eta_hours: `None`", rendered)
        self.assertIn("event_stall_status: `EVENT_EVIDENCE_STALLED`", rendered)
        self.assertIn("stall_severity: `WARN_STALL`", rendered)
        self.assertIn("monitor nearest flat target", rendered)
        self.assertIn("non_flat_hours_since_last_increase: `2.0`", rendered)
        self.assertIn("latest_progress_iteration: `1`", rendered)

    def test_audit_requires_stock_queue_to_be_safe_and_ready(self) -> None:
        audit = audit_builder.build_audit(
            {"decision": "PROMOTION_REVIEW_READY", "evidence_gaps": [], "evidence": {"combined_evidence": {}}},
            {
                "gap_summary": {},
                "readiness_summary": {"promotion_review_ready": True},
                "safety": {
                    "historical_replay_counts_as_promotion_evidence": False,
                    "historical_replay_excluded": True,
                },
            },
            {"delta_from_previous": {}},
            {"status": "PASS", "halt_count": 0, "warn_count": 0},
            {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "blockers": [],
                "no_order_assertions": {
                    "live_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "target_count": 5,
                "ready_candidate_count": 5,
                "blocked_candidate_count": 0,
                "no_order_assertions": {
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": True,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            {
                "status": "PASS",
                "gatekeeper_action_packet": {
                    "promotion_allowed_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            {
                "status": "PASS",
                "current_decision": {
                    "recommended_gatekeeper_lane": "PAPER_SMOKE_REVIEW_READY",
                    "pipeline_can_advance_without_waiting_for_5_of_5": True,
                    "live_or_real_order_allowed": False,
                },
                "taxonomy": {
                    "paper_smoke_evidence": {"ready": True, "can_advance_to": "EXTENDED_PAPER_OBSERVATION"},
                    "extended_paper_evidence": {"ready": True, "can_advance_to": "HUMAN_PROMOTION_REVIEW"},
                },
            },
            {"status": "WARN", "blockers": [], "warnings": []},
            "## Iteration 1\n",
        )

        stock_check = next(
            check
            for check in audit["checks"]
            if check["requirement"] == "Advance stock risk conversion for MDD_TOO_HIGH candidates without order paths"
        )
        self.assertEqual(stock_check["status"], "INCOMPLETE")
        self.assertEqual(stock_check["evidence"]["stock_queue_ready_candidate_count"], 5)
        self.assertTrue(stock_check["evidence"]["stock_queue_no_order_assertions"]["broker_submit_allowed_by_this_report"])

    def test_audit_requires_prompt_to_artifact_checklist_for_root_goal_completion(self) -> None:
        audit = audit_builder.build_audit(
            {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": [], "evidence": {"combined_evidence": {}}},
            {
                "gap_summary": {},
                "readiness_summary": {"promotion_review_ready": True},
                "safety": {
                    "historical_replay_counts_as_promotion_evidence": False,
                    "historical_replay_excluded": True,
                },
            },
            {"delta_from_previous": {}},
            {"status": "PASS", "halt_count": 0, "warn_count": 0},
            {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "blockers": [],
                "no_order_assertions": {
                    "live_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "target_count": 5,
                "ready_candidate_count": 5,
                "blocked_candidate_count": 0,
                "no_order_assertions": {
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            {
                "status": "PASS",
                "gatekeeper_action_packet": {
                    "promotion_allowed_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            {
                "status": "PASS",
                "current_decision": {
                    "recommended_gatekeeper_lane": "PAPER_SMOKE_REVIEW_READY",
                    "pipeline_can_advance_without_waiting_for_5_of_5": True,
                    "live_or_real_order_allowed": False,
                },
                "taxonomy": {
                    "paper_smoke_evidence": {"ready": True, "can_advance_to": "EXTENDED_PAPER_OBSERVATION"},
                    "extended_paper_evidence": {"ready": True, "can_advance_to": "HUMAN_PROMOTION_REVIEW"},
                },
            },
            {"status": "WARN", "blockers": [], "warnings": []},
            "## Iteration 1\n",
            {
                "status": "NOT_COMPLETE",
                "completion_allowed": False,
                "missing_or_incomplete": [{"requirement": "Prompt-to-artifact deliverable: current_paper_activation_gate"}],
                "prompt_to_artifact_checklist": [
                    {
                        "deliverable": "current_paper_activation_gate",
                        "status": "INCOMPLETE",
                        "explicit_requirement": "Use paper activation-ready 100% as the next gate.",
                        "evidence": {"paper_cycles_completed": 252},
                        "source_files": [r"C:\AI\ops\reports\paper_promotion_evidence_latest.json"],
                        "uncovered_or_incomplete": ["extended paper cycle threshold"],
                    },
                    {
                        "deliverable": "two_axis_model_factory_scope",
                        "status": "PASS",
                        "explicit_requirement": "Build crypto plus KIS stock/ETF axes.",
                        "evidence": {"bithumb_coverage_ratio": 1.0},
                        "source_files": [r"C:\AI\Crypto\analysis_results\bithumb_krw_candle_availability_latest.json"],
                    },
                    {
                        "deliverable": "research_conversion_operations_lanes",
                        "status": "PASS",
                        "explicit_requirement": "Keep research, conversion, and operations lanes separate.",
                        "evidence": {"taxonomy_status": "PASS"},
                        "source_files": [r"C:\AI\reports\model_factory\gatekeeper_evidence_taxonomy_latest.json"],
                    },
                    {
                        "deliverable": "hard_safety_controls",
                        "status": "PASS",
                        "explicit_requirement": "Keep paper/live/order paths disabled without approval.",
                        "evidence": {"risk_guard_status": "PASS"},
                        "source_files": [r"C:\AI\ops\reports\realtime_risk_guard_latest.json"],
                    },
                    {
                        "deliverable": "gatekeeper_priority_review_queue",
                        "status": "PASS",
                        "explicit_requirement": "Surface Gatekeeper-ready decisions in a deterministic review-only priority queue.",
                        "evidence": {"next_decision_id": "paper_smoke_review"},
                        "source_files": [r"C:\AI\reports\model_factory\gatekeeper_decision_priority_latest.json"],
                    },
                    {
                        "deliverable": "frozen_scope_experiment_queue",
                        "status": "PASS",
                        "explicit_requirement": "Promote current evidence into bounded frozen-scope experiments before further model-factory work.",
                        "evidence": {"experiment_count": 11, "ready_experiment_count": 9},
                        "source_files": [r"C:\AI\reports\model_factory\model_factory_experiment_queue_latest.json"],
                    },
                    {
                        "deliverable": "file_backed_review_and_public_surfaces",
                        "status": "PASS",
                        "explicit_requirement": "Maintain file-backed review and public surfaces.",
                        "evidence": {"public_export_status": "PASS"},
                        "source_files": [r"C:\AI\public_dashboard_export\public_summary.json"],
                    }
                ],
            },
        )

        self.assertEqual(audit["status"], "NOT_COMPLETE")
        self.assertEqual(audit["incomplete_count"], len(audit["missing_or_incomplete"]))
        self.assertEqual(audit["first_incomplete_requirement"], audit["missing_or_incomplete"][0]["requirement"])
        root_check = next(
            check
            for check in audit["checks"]
            if check["requirement"] == "Prompt-to-artifact checklist verifies root model factory objective"
        )
        self.assertEqual(root_check["status"], "PASS")
        self.assertTrue(root_check["evidence"]["checklist_maps_required_scope"])
        self.assertTrue(root_check["evidence"]["checklist_items_have_evidence"])
        self.assertEqual(
            root_check["evidence"]["incomplete_deliverables"][0]["deliverable"],
            "current_paper_activation_gate",
        )
        deliverable_check = next(
            check
            for check in audit["checks"]
            if check["requirement"] == "Prompt-to-artifact deliverable: current_paper_activation_gate"
        )
        self.assertEqual(deliverable_check["status"], "INCOMPLETE")

    def test_audit_allows_pipeline_pullthrough_when_paper_smoke_ready_but_extended_paper_incomplete(self) -> None:
        audit = audit_builder.build_audit(
            {
                "decision": "KEEP_PAPER_COLLECT_EVIDENCE",
                "evidence_gaps": ["INSUFFICIENT_NON_FLAT_SIGNAL_EVIDENCE"],
                "thresholds": {
                    "min_cycles_for_promotion_review": 288,
                    "min_non_flat_signals_for_promotion": 5,
                    "min_executable_orders_for_promotion": 5,
                },
                "evidence": {
                    "paper_cycles_completed": 174,
                    "combined_evidence": {
                        "combined_non_flat_signal_count": 2,
                        "combined_executable_order_evidence_count": 2,
                    },
                },
            },
            {
                "gap_summary": {"paper_cycles_missing": 114, "non_flat_signals_missing": 3, "executable_orders_missing": 3},
                "readiness_summary": {"promotion_review_ready": False},
                "safety": {
                    "historical_replay_counts_as_promotion_evidence": False,
                    "historical_replay_excluded": True,
                },
            },
            {"delta_from_previous": {}, "event_stall_summary": {}},
            {"status": "PASS", "halt_count": 0, "warn_count": 0},
            {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "blockers": [],
                "no_order_assertions": {
                    "live_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "target_count": 1,
                "ready_candidate_count": 1,
                "blocked_candidate_count": 0,
                "no_order_assertions": {
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            {
                "status": "PASS",
                "gatekeeper_action_packet": {
                    "promotion_allowed_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            {
                "status": "PASS",
                "current_decision": {
                    "recommended_gatekeeper_lane": "PAPER_SMOKE_REVIEW_READY",
                    "pipeline_can_advance_without_waiting_for_5_of_5": True,
                    "live_or_real_order_allowed": False,
                },
                "taxonomy": {
                    "paper_smoke_evidence": {"ready": True, "can_advance_to": "EXTENDED_PAPER_OBSERVATION"},
                    "extended_paper_evidence": {"ready": False, "can_advance_to": "KEEP_EXTENDED_PAPER_COLLECTION"},
                },
            },
            {"status": "WARN", "blockers": [], "warnings": []},
            "## Iteration 1\n",
        )

        self.assertEqual(audit["status"], "COMPLETE")
        self.assertTrue(audit["completion_allowed"])
        self.assertEqual(audit["incomplete_count"], 0)
        self.assertIsNone(audit["first_incomplete_requirement"])
        self.assertEqual(audit["pass_count"], audit["total_count"])
        self.assertTrue(audit["pipeline_pull_through_allowed_without_live"])
        self.assertFalse(audit["extended_paper_or_live_completion_allowed"])


if __name__ == "__main__":
    unittest.main()
