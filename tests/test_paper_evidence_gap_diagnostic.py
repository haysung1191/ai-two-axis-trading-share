from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_paper_evidence_gap_diagnostic.py")
SPEC = importlib.util.spec_from_file_location("build_paper_evidence_gap_diagnostic", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
diag = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(diag)


class PaperEvidenceGapDiagnosticTests(unittest.TestCase):
    def test_diagnostic_surfaces_stalled_gap_and_recent_count_regression(self) -> None:
        report = diag.build_report(
            {
                "candidate_profile": "small_account_growth_paper",
                "decision": "KEEP_PAPER_COLLECT_EVIDENCE",
                "evidence_gaps": ["INSUFFICIENT_NON_FLAT_SIGNAL_EVIDENCE"],
                "thresholds": {
                    "min_cycles_for_promotion_review": 288,
                    "min_non_flat_signals_for_promotion": 5,
                    "min_executable_orders_for_promotion": 5,
                },
                "replay_policy": {
                    "historical_replay_excluded": True,
                    "historical_replay_non_flat_count_excluded": 197,
                },
                "evidence": {
                    "paper_cycles_completed": 225,
                    "signal_evidence": {
                        "current_order_actions": ["HOLD"],
                        "current_signal_sides": ["flat"],
                    },
                    "combined_evidence": {
                        "combined_non_flat_signal_count": 2,
                        "combined_executable_order_evidence_count": 2,
                    },
                    "evidence_deficit": {
                        "paper_loop_cycles_missing": 63,
                        "non_flat_signals_missing": 3,
                        "executable_orders_missing": 3,
                    },
                },
            },
            {
                "pace_summary": {
                    "eta_status": "STALLED_ON_EVENT_EVIDENCE",
                    "slowest_gate_dimension": "non_flat_signals",
                },
                "event_stall_summary": {
                    "event_stall_status": "EVENT_EVIDENCE_STALLED",
                    "stall_severity": "WATCH_STALL",
                    "max_hours_since_last_event": 0.72,
                    "max_paper_cycles_since_last_event": 8,
                    "non_flat_signals": {"last_increase_observed_at_utc": "2026-05-03T07:46:29+00:00"},
                    "executable_orders": {"last_increase_observed_at_utc": "2026-05-03T07:46:29+00:00"},
                },
            },
            {
                "safety": {"paper_enabled": True, "historical_replay_counts_as_promotion_evidence": False},
                "summary": {
                    "eligible_live_paper_signal_count": 13,
                    "eligible_non_flat_signal_count": 2,
                    "virtual_executable_order_count": 2,
                },
                "multi_asset_1d_signals": [
                    {
                        "market": "KRW-BIO",
                        "timeframe": "1d",
                        "side": "long",
                        "target_weight": 0.02,
                        "non_flat_trigger_gap": 0.0,
                        "counts_as_live_paper_evidence": True,
                    }
                ],
                "evidence_velocity_queue": [
                    {
                        "market": "KRW-BIO",
                        "timeframe": "1d",
                        "side": "long",
                        "non_flat_trigger_gap": 0.0,
                        "counts_as_live_paper_evidence": True,
                    },
                    {
                        "market": "KRW-ETH",
                        "timeframe": "4h",
                        "side": "flat",
                        "non_flat_trigger_gap": 0.000079,
                        "volume_ok": True,
                        "counts_as_live_paper_evidence": True,
                    },
                ],
                "historical_replay": {"non_flat_count": 197},
                "signal_state_comparison": {
                    "previous_snapshot_available": True,
                    "regression_attribution_available": True,
                    "previous_non_flat_count": 3,
                    "current_non_flat_count": 2,
                    "lost_non_flat_signal_count": 1,
                    "gained_non_flat_signal_count": 0,
                    "lost_non_flat_signals": [
                        {"market": "KRW-ETH", "timeframe": "4h", "broker_submit_allowed": False}
                    ],
                    "gained_non_flat_signals": [],
                },
            },
            [
                {"observed_at_utc": "2026-05-03T07:46:29+00:00", "non_flat_signal_count": 3, "executable_order_count": 3},
                {"observed_at_utc": "2026-05-03T08:29:47+00:00", "non_flat_signal_count": 2, "executable_order_count": 2},
            ],
        )

        self.assertEqual(report["status"], "REGRESSION_AND_EVENT_STALL")
        self.assertEqual(report["gap_summary"]["non_flat_signal_count"], 2)
        self.assertEqual(report["gap_summary"]["executable_order_count"], 2)
        self.assertTrue(report["regression_summary"]["non_flat_regressed_from_recent_max"])
        self.assertEqual(report["regression_summary"]["max_non_flat_signal_count"], 3)
        self.assertTrue(report["signal_snapshot_regression_attribution"]["regression_attribution_available"])
        self.assertTrue(report["signal_snapshot_regression_attribution"]["explains_recent_max_regression"])
        self.assertEqual(report["signal_snapshot_regression_attribution"]["lost_non_flat_signal_count"], 1)
        self.assertEqual(report["signal_snapshot_regression_attribution"]["lost_non_flat_signals"][0]["market"], "KRW-ETH")
        self.assertEqual(report["target_context"]["included_non_flat_targets"][0]["market"], "KRW-BIO")
        self.assertEqual(report["target_context"]["nearest_flat_watch_targets"][0]["market"], "KRW-ETH")
        self.assertFalse(report["target_context"]["nearest_flat_watch_targets"][0]["broker_submit_allowed"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertFalse(report["safety"]["promotion_allowed"])
        self.assertFalse(report["safety"]["live_enabled"])
        self.assertEqual(report["safety"]["real_orders"], 0)
        self.assertTrue(report["why_not_ready"]["historical_replay_excluded_from_promotion"])

    def test_no_regression_when_current_matches_history_max(self) -> None:
        report = diag.build_report(
            {
                "thresholds": {"min_non_flat_signals_for_promotion": 5, "min_executable_orders_for_promotion": 5},
                "evidence": {
                    "combined_evidence": {
                        "combined_non_flat_signal_count": 3,
                        "combined_executable_order_evidence_count": 3,
                    }
                },
            },
            {"pace_summary": {"eta_status": "STALLED_ON_EVENT_EVIDENCE"}},
            {},
            [{"non_flat_signal_count": 2, "executable_order_count": 2}],
        )

        self.assertEqual(report["status"], "EVENT_STALL")
        self.assertFalse(report["regression_summary"]["non_flat_regressed_from_recent_max"])
        self.assertEqual(report["regression_summary"]["non_flat_regression_delta"], 0)

    def test_render_markdown_includes_safety_and_watch_targets(self) -> None:
        report = diag.build_report(
            {
                "decision": "KEEP_PAPER_COLLECT_EVIDENCE",
                "thresholds": {"min_non_flat_signals_for_promotion": 5, "min_executable_orders_for_promotion": 5},
                "evidence": {
                    "combined_evidence": {
                        "combined_non_flat_signal_count": 2,
                        "combined_executable_order_evidence_count": 2,
                    }
                },
            },
            {"pace_summary": {"eta_status": "STALLED_ON_EVENT_EVIDENCE"}},
            {
                "evidence_velocity_queue": [
                    {
                        "market": "KRW-ETH",
                        "timeframe": "4h",
                        "side": "flat",
                        "non_flat_trigger_gap": 0.000079,
                        "counts_as_live_paper_evidence": True,
                    }
                ]
            },
            [],
        )

        rendered = diag.render_markdown(report)

        self.assertIn("Paper Evidence Gap Diagnostic", rendered)
        self.assertIn("signal_snapshot_attribution_available", rendered)
        self.assertIn("broker_submit_allowed: `False`", rendered)
        self.assertIn("promotion_allowed: `False`", rendered)
        self.assertIn("KRW-ETH", rendered)


if __name__ == "__main__":
    unittest.main()
