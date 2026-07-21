from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_axis_wide_membership_worklist_fill_progress.py")
SPEC = importlib.util.spec_from_file_location("build_kis_axis_wide_membership_worklist_fill_progress", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
progress_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(progress_mod)


class KisAxisWideMembershipWorklistFillProgressTests(unittest.TestCase):
    def complete_row(self) -> dict[str, str]:
        return {
            "request_id": "KIS_AXIS_001",
            "axis": "kis_us_stocks",
            "symbol": "AAA",
            "asset_type": "STOCK",
            "target_response_shard": "response.csv",
            "request_source_verified_ready_row_count": "5",
            "request_source_verified_gap_after_ready_rows": "7",
            "request_required_source_acquisition_row_count": "7",
            "replacement_symbol": "AAA",
            "replacement_asset_type": "STOCK",
            "replacement_active_from": "2000-01-01",
            "replacement_source": "licensed_vendor_security_master:dataset",
            "replacement_snapshot_id": "snap",
            "replacement_evidence_quality": "licensed_vendor",
        }

    def test_complete_rows_are_ready_for_dry_run(self) -> None:
        report = progress_mod.build_report("2026-05-16T14:00:00+09:00", rows=[self.complete_row()])

        self.assertEqual(report["status"], "READY_WORKLIST_FILLED_FOR_SHARD_DRY_RUN")
        self.assertEqual(report["complete_row_count"], 1)
        self.assertEqual(report["blocked_row_count"], 0)
        self.assertEqual(report["completion_ratio"], 1.0)
        self.assertEqual(report["source_acquisition_required_row_count"], 7)
        self.assertEqual(report["source_acquisition_complete_row_count"], 1)
        self.assertEqual(report["source_acquisition_remaining_row_count"], 6)
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_missing_replacement_fields_are_counted_by_axis(self) -> None:
        row = self.complete_row()
        row["replacement_source"] = ""
        row["replacement_evidence_quality"] = ""
        report = progress_mod.build_report("2026-05-16T14:00:00+09:00", rows=[row])

        self.assertEqual(report["status"], "BLOCK_WORKLIST_FILL_PROGRESS")
        self.assertEqual(report["complete_row_count"], 0)
        self.assertEqual(report["blocked_row_count"], 1)
        axis = report["axis_reports"][0]
        self.assertEqual(axis["source_verified_ready_row_count"], 5)
        self.assertEqual(axis["required_source_acquisition_row_count"], 7)
        self.assertEqual(axis["remaining_source_acquisition_row_count"], 7)
        self.assertEqual(axis["missing_field_counts"]["replacement_source"], 1)
        self.assertEqual(axis["missing_field_counts"]["replacement_evidence_quality"], 1)
        self.assertEqual(axis["blocked_samples"][0]["symbol"], "AAA")

    def test_invalid_evidence_quality_is_counted(self) -> None:
        row = self.complete_row()
        row["replacement_evidence_quality"] = "current_snapshot_caveated"
        report = progress_mod.build_report("2026-05-16T14:00:00+09:00", rows=[row])

        axis = report["axis_reports"][0]
        self.assertIn("replacement_evidence_quality_not_operation_ready", axis["missing_field_counts"])


if __name__ == "__main__":
    unittest.main()
