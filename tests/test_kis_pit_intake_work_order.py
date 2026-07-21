from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_pit_intake_work_order.py")
SPEC = importlib.util.spec_from_file_location("build_kis_pit_intake_work_order", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
work_mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = work_mod
SPEC.loader.exec_module(work_mod)


class KisPitIntakeWorkOrderTests(unittest.TestCase):
    def test_work_order_maps_queue_to_blocked_intake_rows(self) -> None:
        queue_report = {
            "queue": [
                {
                    "queue_id": "KIS_SRC_001",
                    "lane": "minimal_cand022_unblock",
                    "evidence_type": "membership_interval",
                    "symbol": "MU",
                    "axis": "kis_us_stocks",
                    "rebalance_date_to_cover": "2026-04-30",
                    "target_file": "membership.csv",
                    "required_source_quality": "authoritative|exchange_official|licensed_vendor",
                },
                {
                    "queue_id": "KIS_SRC_002",
                    "lane": "minimal_cand022_unblock",
                    "evidence_type": "event_or_no_event_coverage",
                    "symbol": "MU",
                    "axis": "kis_us_stocks",
                    "target_file": "event.csv",
                    "required_source_quality": "authoritative|exchange_official|licensed_vendor",
                },
                {
                    "queue_id": "KIS_SRC_003",
                    "lane": "minimal_cand022_unblock",
                    "evidence_type": "delisting_replay_case",
                    "symbol": "",
                    "axis": "policy",
                    "target_file": "replay.csv",
                    "required_source_quality": "authoritative|exchange_official|licensed_vendor|replay_test_authoritative",
                },
            ]
        }
        preflight = {
            "blocked_rows": [
                {
                    "row_number": 2,
                    "kind": "membership",
                    "symbol": "MU",
                    "axis": "kis_us_stocks",
                    "missing_fields": ["active_from", "source"],
                    "blockers": ["required_fields_missing"],
                },
                {
                    "row_number": 2,
                    "kind": "event_or_no_event",
                    "symbol": "MU",
                    "axis": "kis_us_stocks",
                    "missing_fields": ["coverage_status"],
                    "blockers": ["required_fields_missing"],
                },
                {
                    "row_number": 2,
                    "kind": "replay",
                    "symbol": "",
                    "axis": "",
                    "missing_fields": ["symbol", "event_date"],
                    "blockers": ["required_fields_missing", "evidence_quality_not_operation_ready"],
                },
            ]
        }

        report = work_mod.build_work_order(
            "2026-05-16T09:00:00+09:00",
            queue_report=queue_report,
            preflight=preflight,
            pit_verifier={},
        )

        self.assertEqual(report["status"], "BLOCK_INTAKE_WORK_ORDER_OPEN")
        self.assertEqual(report["minimal_cand022_task_count"], 3)
        self.assertEqual(report["minimal_cand022_blocked_task_count"], 3)
        self.assertFalse(report["safety"]["order_intent_created"])
        first = report["tasks"][0]
        self.assertEqual(first["queue_id"], "KIS_SRC_001")
        self.assertEqual(first["intake_row_numbers"], [2])
        self.assertIn("active_from", first["missing_fields"])
        replay = report["tasks"][2]
        self.assertIn("replay_test_authoritative", replay["accepted_evidence_quality"])
        self.assertIn("evidence_quality_not_operation_ready", replay["blockers"])

    def test_ready_tasks_shift_to_prefight_recheck(self) -> None:
        report = work_mod.build_work_order(
            "2026-05-16T09:00:00+09:00",
            queue_report={
                "queue": [
                    {
                        "queue_id": "KIS_SRC_001",
                        "lane": "minimal_cand022_unblock",
                        "evidence_type": "membership_interval",
                        "symbol": "MU",
                        "axis": "kis_us_stocks",
                        "required_source_quality": "authoritative",
                    }
                ]
            },
            preflight={"blocked_rows": []},
            pit_verifier={},
        )

        self.assertEqual(report["status"], "READY_FOR_PREFLIGHT_RECHECK")
        self.assertEqual(report["minimal_cand022_ready_task_count"], 1)
        self.assertEqual(report["minimal_cand022_blocked_task_count"], 0)

    def test_axis_wide_tasks_are_blocked_by_pit_verifier_gap(self) -> None:
        report = work_mod.build_work_order(
            "2026-05-16T09:00:00+09:00",
            queue_report={
                "queue": [
                    {
                        "queue_id": "KIS_SRC_001",
                        "lane": "axis_wide_operation_ready",
                        "evidence_type": "axis_membership_history",
                        "symbol": "*",
                        "axis": "kis_us_stocks",
                        "required_source_quality": "authoritative|exchange_official|licensed_vendor",
                    },
                    {
                        "queue_id": "KIS_SRC_002",
                        "lane": "axis_wide_operation_ready",
                        "evidence_type": "axis_membership_history",
                        "symbol": "*",
                        "axis": "kis_us_etfs",
                        "required_source_quality": "authoritative|exchange_official|licensed_vendor",
                    },
                ]
            },
            preflight={"blocked_rows": []},
            pit_verifier={
                "single_next_action": "Replace 7387 still-uncovered membership rows for kis_us_stocks first.",
                "next_evidence_acquisition_targets": [
                    {
                        "rank": 1,
                        "axis": "kis_us_stocks",
                        "missing_membership_rows": 7387,
                        "source_verified_membership_ready_rows": 5,
                        "ready_coverage_of_remaining": 0.00067,
                        "recommended_source_class": "exchange_official_or_licensed_vendor_pit_membership_history",
                    },
                    {
                        "rank": 2,
                        "axis": "kis_us_etfs",
                        "missing_membership_rows": 5195,
                        "source_verified_membership_ready_rows": 0,
                        "ready_coverage_of_remaining": 0.0,
                        "recommended_source_class": "exchange_official_or_licensed_vendor_pit_membership_history",
                    },
                ],
            },
        )

        self.assertEqual(report["status"], "BLOCK_AXIS_WIDE_SOURCE_ACQUISITION_REQUIRED")
        self.assertEqual(report["axis_wide_task_count"], 2)
        self.assertEqual(report["axis_wide_blocked_task_count"], 2)
        self.assertEqual(report["axis_wide_next_target"]["axis"], "kis_us_stocks")
        self.assertEqual(report["axis_wide_next_target"]["pit_missing_membership_rows"], 7387)
        self.assertIn("axis_wide_pit_membership_history_missing", report["axis_wide_next_target"]["blockers"])
        self.assertEqual(
            report["single_next_action"],
            "Replace 7387 still-uncovered membership rows for kis_us_stocks first.",
        )


if __name__ == "__main__":
    unittest.main()
