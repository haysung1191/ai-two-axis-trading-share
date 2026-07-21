from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_paper_evidence_velocity_monitor.py")
SPEC = importlib.util.spec_from_file_location("build_paper_evidence_velocity_monitor", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
monitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(monitor)


class PaperEvidenceVelocityMonitorTests(unittest.TestCase):
    def test_monitor_joins_gaps_and_velocity_targets_without_orders(self) -> None:
        report = monitor.build_monitor(
            {
                "decision": "KEEP_PAPER_COLLECT_EVIDENCE",
                "thresholds": {
                    "min_cycles_for_promotion_review": 288,
                    "min_non_flat_signals_for_promotion": 5,
                    "min_executable_orders_for_promotion": 5,
                },
                "evidence": {
                    "paper_cycles_completed": 145,
                    "combined_evidence": {
                        "combined_non_flat_signal_count": 2,
                        "combined_executable_order_evidence_count": 2,
                    },
                },
                "replay_policy": {"historical_replay_counts_as_promotion_evidence": False},
            },
            {
                "summary": {
                    "eligible_live_paper_signal_count": 13,
                    "eligible_non_flat_signal_count": 2,
                    "virtual_executable_order_count": 2,
                    "new_signal_count_this_run": 0,
                },
                "safety": {"historical_replay_counts_as_promotion_evidence": False},
                "evidence_velocity_queue": [
                    {
                        "market": "KRW-BIO",
                        "timeframe": "1d",
                        "side": "long",
                        "velocity_rank_reason": "already_non_flat",
                        "non_flat_trigger_gap": 0.0,
                        "counts_as_live_paper_evidence": True,
                        "broker_submit_allowed": True,
                    },
                    {
                        "market": "KRW-ETH",
                        "timeframe": "1h",
                        "side": "flat",
                        "velocity_rank_reason": "nearest_to_non_flat_trigger",
                        "non_flat_trigger_gap": 0.0015,
                        "counts_as_live_paper_evidence": True,
                        "broker_submit_allowed": True,
                    }
                ],
            },
        )

        self.assertEqual(report["gap_summary"]["paper_cycles_missing"], 143)
        self.assertEqual(report["gap_summary"]["non_flat_signals_missing"], 3)
        self.assertEqual(report["gap_summary"]["executable_orders_missing"], 3)
        self.assertEqual(report["status"], "COLLECT_EVENT_EVIDENCE")
        self.assertEqual(report["blocking_mode"], "event_evidence")
        self.assertIn("non-flat and executable evidence reach 5/5", report["next_action"])
        self.assertEqual(report["readiness_summary"]["paper_evidence_readiness_percent"], 40.0)
        self.assertEqual(
            report["readiness_summary"]["dominant_blocking_dimensions"],
            ["non_flat_signals", "executable_orders"],
        )
        self.assertFalse(report["readiness_summary"]["promotion_review_ready"])
        self.assertEqual(report["top_velocity_targets"][0]["market"], "KRW-BIO")
        self.assertEqual(report["velocity_proximity_summary"]["already_non_flat_target_count"], 1)
        self.assertEqual(
            report["velocity_proximity_summary"]["nearest_flat_target"]["market"],
            "KRW-ETH",
        )
        self.assertEqual(
            report["velocity_proximity_summary"]["nearest_flat_target"]["non_flat_trigger_gap"],
            0.0015,
        )
        self.assertFalse(report["velocity_proximity_summary"]["nearest_flat_target"]["broker_submit_allowed"])
        self.assertFalse(report["top_velocity_targets"][0]["broker_submit_allowed"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertFalse(report["safety"]["historical_replay_counts_as_promotion_evidence"])
        self.assertTrue(report["safety"]["historical_replay_excluded"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_monitor_reports_cycle_only_wait_after_event_evidence_clears(self) -> None:
        report = monitor.build_monitor(
            {
                "decision": "KEEP_PAPER_COLLECT_EVIDENCE",
                "thresholds": {
                    "min_cycles_for_promotion_review": 288,
                    "min_non_flat_signals_for_promotion": 5,
                    "min_executable_orders_for_promotion": 5,
                },
                "evidence": {
                    "paper_cycles_completed": 232,
                    "combined_evidence": {
                        "combined_non_flat_signal_count": 6,
                        "combined_executable_order_evidence_count": 6,
                    },
                },
                "replay_policy": {"historical_replay_counts_as_promotion_evidence": False},
            },
            {
                "summary": {
                    "eligible_live_paper_signal_count": 53,
                    "eligible_non_flat_signal_count": 6,
                    "virtual_executable_order_count": 6,
                    "new_signal_count_this_run": 43,
                },
                "safety": {"historical_replay_counts_as_promotion_evidence": False},
                "evidence_velocity_queue": [],
            },
        )

        self.assertEqual(report["status"], "CYCLE_ONLY_WAIT")
        self.assertEqual(report["blocking_mode"], "paper_cycles_only")
        self.assertEqual(report["gap_summary"]["paper_cycles_missing"], 56)
        self.assertEqual(report["gap_summary"]["non_flat_signals_missing"], 0)
        self.assertEqual(report["gap_summary"]["executable_orders_missing"], 0)
        self.assertEqual(report["readiness_summary"]["dominant_blocking_dimensions"], ["paper_cycles"])
        self.assertIn("event evidence already clears 5/5", report["next_action"])


if __name__ == "__main__":
    unittest.main()
