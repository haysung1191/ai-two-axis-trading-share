from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_pit_next_evidence_fill_card.py")
SPEC = importlib.util.spec_from_file_location("build_kis_pit_next_evidence_fill_card", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
card_mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = card_mod
SPEC.loader.exec_module(card_mod)


class KisPitNextEvidenceFillCardTests(unittest.TestCase):
    def test_card_points_to_first_blocked_minimal_membership_row(self) -> None:
        report = card_mod.build_fill_card(
            "2026-05-16T10:40:00+09:00",
            work_order={
                "tasks": [
                    {
                        "queue_id": "KIS_SRC_001",
                        "lane": "minimal_cand022_unblock",
                        "evidence_type": "membership_interval",
                        "symbol": "MU",
                        "axis": "kis_us_stocks",
                        "rebalance_date_to_cover": "2026-04-30",
                        "intake_row_numbers": [2],
                        "missing_fields": ["active_from", "source", "snapshot_id"],
                        "blockers": ["required_fields_missing"],
                        "accepted_evidence_quality": "authoritative|exchange_official|licensed_vendor",
                    }
                ]
            },
        )

        self.assertEqual(report["status"], "BLOCK_NEXT_EVIDENCE_FILL_REQUIRED")
        self.assertEqual(report["generated_at"], "2026-05-16T10:40:00+09:00")
        self.assertEqual(report["generated_at_utc"], "2026-05-16T01:40:00+00:00")
        self.assertEqual(report["queue_id"], "KIS_SRC_001")
        self.assertEqual(report["symbol"], "MU")
        self.assertIn("cand022_authoritative_membership_rows_template.csv", report["editable_intake_file"])
        self.assertIn("vendor", report["must_not_use_source_values"])
        self.assertIn("snap", report["must_not_use_snapshot_values"])
        self.assertIn("current_snapshot_caveated", report["must_not_contain_markers"])
        self.assertIn("python .\\build_kis_pit_intake_import_preflight.py", report["after_fill_commands"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_card_reports_ready_when_no_blocked_minimal_task_exists(self) -> None:
        report = card_mod.build_fill_card(
            "2026-05-16T10:40:00+09:00",
            work_order={
                "tasks": [
                    {
                        "queue_id": "KIS_SRC_019",
                        "lane": "axis_wide_operation_ready",
                        "evidence_type": "axis_membership_history",
                    }
                ]
            },
        )

        self.assertEqual(report["status"], "READY_NO_BLOCKED_MINIMAL_TASK")
        self.assertIsNone(report["queue_id"])
        self.assertFalse(report["trading_enabled"])

    def test_card_points_to_axis_wide_target_when_minimal_tasks_are_clear(self) -> None:
        report = card_mod.build_fill_card(
            "2026-05-16T10:40:00+09:00",
            work_order={
                "single_next_action": "Replace 7387 still-uncovered membership rows for kis_us_stocks first.",
                "axis_wide_next_target": {
                    "queue_id": "KIS_SRC_001",
                    "lane": "axis_wide_operation_ready",
                    "evidence_type": "axis_membership_history",
                    "symbol": "*",
                    "axis": "kis_us_stocks",
                    "rebalance_date_to_cover": "full_backtest_window",
                    "accepted_evidence_quality": "authoritative|exchange_official|licensed_vendor",
                    "blockers": ["axis_wide_pit_membership_history_missing"],
                    "pit_missing_membership_rows": 7387,
                    "pit_source_verified_membership_ready_rows": 5,
                    "pit_recommended_source_class": "exchange_official_or_licensed_vendor_pit_membership_history",
                    "pit_priority_rank": 1,
                },
                "tasks": [],
            },
        )

        self.assertEqual(report["status"], "BLOCK_AXIS_WIDE_EVIDENCE_ACQUISITION_REQUIRED")
        self.assertEqual(report["generated_at_utc"], "2026-05-16T01:40:00+00:00")
        self.assertEqual(report["queue_id"], "KIS_SRC_001")
        self.assertEqual(report["axis"], "kis_us_stocks")
        self.assertEqual(report["pit_missing_membership_rows"], 7387)
        self.assertEqual(report["pit_priority_rank"], 1)
        self.assertIn("build_kis_pit_membership_verifier.py", report["after_fill_commands"][1])
        self.assertFalse(report["trading_enabled"])


if __name__ == "__main__":
    unittest.main()
