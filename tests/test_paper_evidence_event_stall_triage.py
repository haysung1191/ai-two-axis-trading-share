from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_paper_evidence_event_stall_triage.py")
SPEC = importlib.util.spec_from_file_location("build_paper_evidence_event_stall_triage", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
triage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(triage)


class PaperEvidenceEventStallTriageTests(unittest.TestCase):
    def test_stalled_evidence_builds_review_ready_packet_without_order_permissions(self) -> None:
        report = triage.build_report(
            {
                "current": {
                    "paper_cycles_completed": 178,
                    "paper_cycles_missing": 110,
                    "non_flat_signal_count": 2,
                    "non_flat_signals_missing": 3,
                    "executable_order_count": 2,
                    "executable_orders_missing": 3,
                },
                "pace_summary": {
                    "eta_status": "STALLED_ON_EVENT_EVIDENCE",
                    "slowest_gate_dimension": "non_flat_signals",
                    "promotion_review_eta_hours": None,
                },
                "event_stall_summary": {
                    "event_stall_status": "EVENT_EVIDENCE_STALLED",
                    "stall_severity": "WARN_STALL",
                    "max_hours_since_last_event": 2.5,
                    "max_paper_cycles_since_last_event": 31,
                },
            },
            {
                "gap_summary": {},
                "velocity_proximity_summary": {
                    "live_like_target_count": 8,
                    "already_non_flat_target_count": 2,
                    "operator_focus": "watch_nearest_flat_target_for_next_non_flat_evidence",
                },
                "top_velocity_targets": [
                    {
                        "market": "KRW-BIO",
                        "timeframe": "1d",
                        "side": "long",
                        "rank_reason": "already_non_flat",
                        "non_flat_trigger_gap": 0.0,
                        "counts_as_live_paper_evidence": True,
                        "broker_submit_allowed": True,
                    },
                    {
                        "market": "KRW-BTC",
                        "timeframe": "1h",
                        "side": "flat",
                        "rank_reason": "nearest_to_non_flat_trigger",
                        "non_flat_trigger_gap": 0.0025,
                        "counts_as_live_paper_evidence": True,
                        "broker_submit_allowed": True,
                    },
                ],
            },
            {
                "safety": {
                    "live_enabled": False,
                    "private_submit_used": False,
                    "real_orders": 0,
                    "historical_replay_counts_as_promotion_evidence": False,
                },
                "historical_replay": {
                    "counts_as_live_paper_evidence": False,
                    "signal_count": 100,
                    "non_flat_count": 20,
                },
            },
            {
                "status": "PASS",
                "checks": [
                    {
                        "name": "broker_submit_scope",
                        "observed": {"broker_submit_allowed": True, "broker_submit_scope": "paper_only"},
                    }
                ],
            },
        )

        self.assertEqual(report["status"], "READY_FOR_STALL_REVIEW")
        self.assertTrue(report["review_ready"])
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["stall_summary"]["slowest_gate_dimension"], "non_flat_signals")
        self.assertEqual(report["velocity_context"]["top_targets"][0]["triage_role"], "already_non_flat_observe_for_distinct_paper_event")
        self.assertEqual(report["velocity_context"]["top_targets"][1]["triage_role"], "nearest_flat_watch_for_transition")
        self.assertFalse(report["velocity_context"]["top_targets"][0]["broker_submit_allowed"])
        self.assertFalse(report["permissions"]["promotion_allowed_by_this_report"])
        self.assertFalse(report["permissions"]["live_allowed_by_this_report"])
        self.assertFalse(report["permissions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["permissions"]["real_orders_allowed_by_this_report"])
        self.assertFalse(report["replay_policy"]["counts_as_extended_paper_promotion"])
        self.assertFalse(report["replay_policy"]["counts_as_live_readiness"])

    def test_blocks_when_risk_guard_or_live_state_is_unsafe(self) -> None:
        report = triage.build_report(
            {"event_stall_summary": {"event_stall_status": "EVENT_EVIDENCE_STALLED"}},
            {
                "top_velocity_targets": [
                    {
                        "market": "KRW-BTC",
                        "timeframe": "1h",
                        "side": "flat",
                        "non_flat_trigger_gap": 0.003,
                        "counts_as_live_paper_evidence": True,
                    }
                ]
            },
            {
                "safety": {
                    "live_enabled": True,
                    "private_submit_used": True,
                    "real_orders": 1,
                    "historical_replay_counts_as_promotion_evidence": False,
                },
                "historical_replay": {"counts_as_live_paper_evidence": False},
            },
            {"status": "WARN"},
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("RISK_GUARD_NOT_PASS", report["blockers"])
        self.assertIn("LIVE_ENABLED", report["blockers"])
        self.assertIn("PRIVATE_SUBMIT_USED", report["blockers"])
        self.assertIn("REAL_ORDERS_NONZERO", report["blockers"])
        self.assertFalse(report["permissions"]["live_allowed_by_this_report"])
        self.assertFalse(report["permissions"]["broker_submit_allowed_by_this_report"])

    def test_risk_guard_warn_with_clean_hard_safety_does_not_block_stall_review(self) -> None:
        report = triage.build_report(
            {
                "current": {
                    "paper_cycles_completed": 252,
                    "paper_cycles_missing": 36,
                    "non_flat_signal_count": 53,
                    "non_flat_signals_missing": 0,
                    "executable_order_count": 53,
                    "executable_orders_missing": 0,
                },
                "pace_summary": {
                    "eta_status": "ETA_AVAILABLE",
                    "slowest_gate_dimension": "paper_cycles",
                    "promotion_review_eta_hours": 4.9,
                },
                "event_stall_summary": {
                    "event_stall_status": "EVENT_EVIDENCE_STALLED",
                    "stall_severity": "WATCH_STALL",
                    "max_hours_since_last_event": 1.4,
                    "max_paper_cycles_since_last_event": 0,
                },
            },
            {
                "velocity_proximity_summary": {
                    "live_like_target_count": 8,
                    "already_non_flat_target_count": 8,
                    "operator_focus": "wait_for_new_live_like_targets",
                },
                "top_velocity_targets": [
                    {
                        "market": "KRW-ETH",
                        "timeframe": "4h",
                        "side": "long",
                        "rank_reason": "already_non_flat",
                        "non_flat_trigger_gap": 0.0,
                        "counts_as_live_paper_evidence": True,
                        "broker_submit_allowed": True,
                    }
                ],
            },
            {
                "safety": {
                    "live_enabled": False,
                    "private_submit_used": False,
                    "real_orders": 0,
                    "historical_replay_counts_as_promotion_evidence": False,
                },
                "historical_replay": {"counts_as_live_paper_evidence": False},
            },
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

        self.assertEqual(report["status"], "READY_FOR_STALL_REVIEW")
        self.assertTrue(report["review_ready"])
        self.assertEqual(report["blockers"], [])
        self.assertTrue(report["safety"]["risk_guard_hard_safety_ok"])
        self.assertFalse(report["permissions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["permissions"]["real_orders_allowed_by_this_report"])

    def test_render_markdown_surfaces_replay_and_permission_guards(self) -> None:
        report = triage.build_report(
            {"event_stall_summary": {"event_stall_status": "EVENT_EVIDENCE_STALLED"}},
            {
                "top_velocity_targets": [
                    {
                        "market": "KRW-ETH",
                        "timeframe": "4h",
                        "side": "flat",
                        "non_flat_trigger_gap": 0.006,
                        "counts_as_live_paper_evidence": True,
                    }
                ]
            },
            {
                "safety": {"historical_replay_counts_as_promotion_evidence": False},
                "historical_replay": {"counts_as_live_paper_evidence": False, "non_flat_count": 9},
            },
            {"status": "PASS"},
        )

        rendered = triage.render_markdown(report)

        self.assertIn("Paper Evidence Event Stall Triage", rendered)
        self.assertIn("counts_as_extended_paper_promotion: `False`", rendered)
        self.assertIn("counts_as_live_readiness: `False`", rendered)
        self.assertIn("broker_submit_allowed_by_this_report: `False`", rendered)


if __name__ == "__main__":
    unittest.main()
