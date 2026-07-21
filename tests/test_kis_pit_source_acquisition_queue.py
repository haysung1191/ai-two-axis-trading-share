from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_pit_source_acquisition_queue.py")
SPEC = importlib.util.spec_from_file_location("build_kis_pit_source_acquisition_queue", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
queue_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(queue_mod)


class KisPitSourceAcquisitionQueueTests(unittest.TestCase):
    def test_build_queue_splits_minimal_and_axis_wide_lanes(self) -> None:
        report = queue_mod.build_queue(
            "2026-05-16T09:10:00+09:00",
            requirements={
                "membership_requirements": [
                    {
                        "symbol": "MU",
                        "axis": "kis_us_stocks",
                        "target_file": "membership.csv",
                        "rebalance_date_to_cover": "2026-04-30",
                        "current_blockers": ["membership_rows_are_caveated_not_operation_ready"],
                    }
                ],
                "delisting_event_requirements": {
                    "target_file": "events.csv",
                    "current_blockers": ["event_missing"],
                },
                "delisting_replay_requirements": {
                    "target_file": "replay.csv",
                    "current_blockers": ["replay_missing"],
                    "required_scenarios": ["ticker_change", "unknown_treatment_block"],
                },
            },
            gap_matrix={
                "status": "BLOCK_HISTORICAL_PIT_SURVIVORSHIP_GAPS",
                "gate_summary": {"first_blocked_gate_id": "G1_MEMBERSHIP_INTERVALS_OPERATION_READY"},
                "axis_membership_gap_matrix": [
                    {
                        "axis": "kis_us_stocks",
                        "blockers": ["operation_ready_quality_rows_missing"],
                    }
                ],
            },
            local_source_audit={
                "audits": {
                    "membership": [
                        {
                            "symbol": "MU",
                            "local_evidence_qualities": ["current_snapshot_caveated"],
                        }
                    ]
                }
            },
            public_probe={
                "accepted_for_operation_ready_intake_count": 0,
                "probes": [{"symbols": ["MU"], "decision": "REJECT_FOR_KIS_PIT_OPERATION_READY_INTAKE"}],
            },
        )

        self.assertEqual(report["status"], "BLOCK_SOURCE_ACQUISITION_REQUIRED")
        self.assertEqual(report["generated_at"], "2026-05-16T09:10:00+09:00")
        self.assertEqual(report["generated_at_utc"], "2026-05-16T00:10:00+00:00")
        self.assertEqual(report["queue_counts"]["minimal_cand022_unblock"], 4)
        self.assertEqual(report["queue_counts"]["axis_wide_operation_ready"], 1)
        self.assertEqual(report["first_queue_item"]["symbol"], "MU")
        self.assertTrue(report["first_queue_item"]["public_probe_rejected"])
        self.assertFalse(report["safety"]["live_enabled"])

    def test_empty_inputs_are_safe_and_no_trading_enabled(self) -> None:
        report = queue_mod.build_queue(
            "2026-05-16T09:10:00+09:00",
            requirements={},
            gap_matrix={},
            local_source_audit={},
            public_probe={},
        )

        self.assertEqual(report["queue_counts"]["total"], 0)
        self.assertIsNone(report["first_queue_item"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_completed_minimal_intake_leaves_only_axis_wide_queue(self) -> None:
        report = queue_mod.build_queue(
            "2026-05-16T09:10:00+09:00",
            requirements={
                "membership_requirements": [
                    {
                        "symbol": "MU",
                        "axis": "kis_us_stocks",
                        "target_file": "membership.csv",
                        "rebalance_date_to_cover": "2026-04-30",
                        "current_blockers": [],
                    }
                ],
                "delisting_event_requirements": {"target_file": "events.csv", "current_blockers": []},
                "delisting_replay_requirements": {
                    "target_file": "replay.csv",
                    "current_blockers": [],
                    "required_scenarios": ["ticker_change"],
                },
            },
            gap_matrix={
                "status": "BLOCK_HISTORICAL_PIT_SURVIVORSHIP_GAPS",
                "gate_summary": {"first_blocked_gate_id": "G1_MEMBERSHIP_INTERVALS_OPERATION_READY"},
                "axis_membership_gap_matrix": [
                    {"axis": "kis_us_stocks", "blockers": ["operation_ready_quality_incomplete"]},
                    {"axis": "kis_us_etfs", "blockers": ["operation_ready_quality_rows_missing"]},
                ],
            },
            local_source_audit={},
            public_probe={},
            intake_work_order={
                "minimal_cand022_task_count": 3,
                "minimal_cand022_blocked_task_count": 0,
            },
            intake_preflight={
                "ready_row_count": 3,
                "blocked_row_count": 0,
            },
        )

        self.assertEqual(report["status"], "BLOCK_AXIS_WIDE_SOURCE_ACQUISITION_REQUIRED")
        self.assertTrue(report["minimal_cand022_intake_complete"])
        self.assertEqual(report["queue_counts"]["minimal_cand022_unblock"], 0)
        self.assertEqual(report["queue_counts"]["axis_wide_operation_ready"], 2)
        self.assertEqual(report["first_queue_item"]["lane"], "axis_wide_operation_ready")
        self.assertIn("all four KIS axes", report["single_next_action"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])


if __name__ == "__main__":
    unittest.main()
