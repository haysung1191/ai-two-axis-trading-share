from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_paper_evidence_progress_delta.py")
SPEC = importlib.util.spec_from_file_location("build_paper_evidence_progress_delta", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
delta = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(delta)


class PaperEvidenceProgressDeltaTests(unittest.TestCase):
    def test_build_report_computes_delta_without_order_paths(self) -> None:
        report, history = delta.build_report(
            {
                "generated_at_utc": "2026-05-03T02:05:00+00:00",
                "decision": "KEEP_PAPER_COLLECT_EVIDENCE",
                "thresholds": {
                    "min_cycles_for_promotion_review": 288,
                    "min_non_flat_signals_for_promotion": 5,
                    "min_executable_orders_for_promotion": 5,
                },
                "evidence": {
                    "paper_cycles_completed": 147,
                    "combined_evidence": {
                        "combined_non_flat_signal_count": 2,
                        "combined_executable_order_evidence_count": 2,
                    },
                },
                "evidence_gaps": ["INSUFFICIENT_NON_FLAT_SIGNAL_EVIDENCE"],
            },
            [
                {
                    "observed_at_utc": "2026-05-03T01:05:00+00:00",
                    "source_generated_at_utc": "2026-05-03T01:05:00+00:00",
                    "paper_cycles_completed": 135,
                    "non_flat_signal_count": 1,
                    "executable_order_count": 1,
                }
            ],
            observed_at_utc="2026-05-03T02:05:00+00:00",
        )

        self.assertEqual(report["current"]["paper_cycles_missing"], 141)
        self.assertEqual(report["delta_from_previous"]["paper_cycles_delta"], 12)
        self.assertEqual(report["delta_from_previous"]["non_flat_delta"], 1)
        self.assertEqual(report["delta_from_previous"]["executable_delta"], 1)
        self.assertEqual(report["delta_from_previous"]["cycles_per_hour"], 12.0)
        self.assertEqual(report["pace_summary"]["cycles_per_hour"], 12.0)
        self.assertEqual(report["pace_summary"]["non_flat_events_per_hour"], 1.0)
        self.assertEqual(report["pace_summary"]["executable_events_per_hour"], 1.0)
        self.assertEqual(report["pace_summary"]["slowest_gate_dimension"], "paper_cycles")
        self.assertEqual(report["pace_summary"]["promotion_review_eta_hours"], 11.75)
        self.assertEqual(report["event_stall_summary"]["event_stall_status"], "EVENT_EVIDENCE_JUST_UPDATED")
        self.assertEqual(report["event_stall_summary"]["stall_severity"], "NO_STALL")
        self.assertEqual(report["event_stall_summary"]["non_flat_signals"]["observations_since_last_increase"], 0)
        self.assertEqual(report["event_stall_summary"]["executable_orders"]["observations_since_last_increase"], 0)
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertEqual(report["safety"]["real_orders"], 0)
        self.assertEqual(len(history), 2)

    def test_pace_summary_flags_stalled_event_evidence(self) -> None:
        report, _ = delta.build_report(
            {
                "generated_at_utc": "2026-05-03T03:00:00+00:00",
                "decision": "KEEP_PAPER_COLLECT_EVIDENCE",
                "thresholds": {
                    "min_cycles_for_promotion_review": 288,
                    "min_non_flat_signals_for_promotion": 5,
                    "min_executable_orders_for_promotion": 5,
                },
                "evidence": {
                    "paper_cycles_completed": 167,
                    "combined_evidence": {
                        "combined_non_flat_signal_count": 2,
                        "combined_executable_order_evidence_count": 2,
                    },
                },
            },
            [
                {
                    "observed_at_utc": "2026-05-03T01:00:00+00:00",
                    "source_generated_at_utc": "2026-05-03T01:00:00+00:00",
                    "paper_cycles_completed": 147,
                    "non_flat_signal_count": 2,
                    "executable_order_count": 2,
                }
            ],
            observed_at_utc="2026-05-03T03:00:00+00:00",
        )

        pace = report["pace_summary"]
        self.assertEqual(pace["cycles_per_hour"], 10.0)
        self.assertIsNone(pace["non_flat_events_per_hour"])
        self.assertIsNone(pace["executable_events_per_hour"])
        self.assertEqual(pace["estimated_hours_to_cycle_target"], 12.1)
        self.assertIsNone(pace["estimated_hours_to_non_flat_target"])
        self.assertEqual(pace["slowest_gate_dimension"], "non_flat_signals")
        self.assertEqual(pace["eta_status"], "STALLED_ON_EVENT_EVIDENCE")
        self.assertIsNone(pace["promotion_review_eta_hours"])
        stall = report["event_stall_summary"]
        self.assertEqual(stall["event_stall_status"], "EVENT_EVIDENCE_STALLED")
        self.assertEqual(stall["stall_severity"], "WARN_STALL")
        self.assertEqual(stall["max_hours_since_last_event"], 2.0)
        self.assertEqual(stall["max_paper_cycles_since_last_event"], 20)
        self.assertEqual(
            stall["safe_next_action"],
            "Continue safe paper loop, but monitor nearest flat target and stall age closely.",
        )
        self.assertEqual(stall["non_flat_signals"]["observations_since_last_increase"], 1)
        self.assertEqual(stall["non_flat_signals"]["hours_since_last_increase"], 2.0)
        self.assertEqual(stall["non_flat_signals"]["paper_cycles_since_last_increase"], 20)
        self.assertEqual(stall["executable_orders"]["observations_since_last_increase"], 1)

    def test_append_history_replaces_same_source_snapshot(self) -> None:
        history = delta.append_history(
            [
                {
                    "observed_at_utc": "2026-05-03T02:00:00+00:00",
                    "source_generated_at_utc": "same",
                    "paper_cycles_completed": 146,
                }
            ],
            {
                "observed_at_utc": "2026-05-03T02:01:00+00:00",
                "source_generated_at_utc": "same",
                "paper_cycles_completed": 147,
            },
        )

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["paper_cycles_completed"], 147)

    def test_event_stall_summary_escalates_review_after_long_stall(self) -> None:
        report, _ = delta.build_report(
            {
                "generated_at_utc": "2026-05-03T09:30:00+00:00",
                "decision": "KEEP_PAPER_COLLECT_EVIDENCE",
                "thresholds": {
                    "min_cycles_for_promotion_review": 288,
                    "min_non_flat_signals_for_promotion": 5,
                    "min_executable_orders_for_promotion": 5,
                },
                "evidence": {
                    "paper_cycles_completed": 230,
                    "combined_evidence": {
                        "combined_non_flat_signal_count": 2,
                        "combined_executable_order_evidence_count": 2,
                    },
                },
            },
            [
                {
                    "observed_at_utc": "2026-05-03T01:00:00+00:00",
                    "source_generated_at_utc": "2026-05-03T01:00:00+00:00",
                    "paper_cycles_completed": 147,
                    "non_flat_signal_count": 2,
                    "executable_order_count": 2,
                }
            ],
            observed_at_utc="2026-05-03T09:30:00+00:00",
        )

        stall = report["event_stall_summary"]
        self.assertEqual(stall["stall_severity"], "REVIEW_STALL")
        self.assertEqual(stall["max_paper_cycles_since_last_event"], 83)
        self.assertIn("Human review", stall["safe_next_action"])


if __name__ == "__main__":
    unittest.main()
