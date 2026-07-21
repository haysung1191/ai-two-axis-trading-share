from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_axis_wide_membership_replacement_worklist.py")
SPEC = importlib.util.spec_from_file_location("build_kis_axis_wide_membership_replacement_worklist", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
worklist_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worklist_mod)


class KisAxisWideMembershipReplacementWorklistTests(unittest.TestCase):
    def write_membership(self, path: Path) -> None:
        fields = [
            "symbol",
            "asset_type",
            "axis",
            "active_from",
            "active_to",
            "listed_date",
            "delisted_date",
            "source",
            "snapshot_id",
            "evidence_quality",
            "notes",
        ]
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerow(
                {
                    "symbol": "AAA",
                    "asset_type": "STOCK",
                    "axis": "kis_us_stocks",
                    "active_from": "2026-05-13",
                    "source": "current_full_market_universe_snapshot",
                    "snapshot_id": "snap",
                    "evidence_quality": "current_snapshot_caveated",
                    "notes": "needs replacement",
                }
            )
            writer.writerow(
                {
                    "symbol": "BBB",
                    "asset_type": "STOCK",
                    "axis": "kis_us_stocks",
                    "active_from": "2000-01-01",
                    "source": "licensed_vendor_security_master:dataset",
                    "snapshot_id": "snap_ready",
                    "evidence_quality": "licensed_vendor",
                    "notes": "already ready",
                }
            )

    def test_build_report_extracts_only_caveated_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            membership = Path(tmp) / "membership.csv"
            self.write_membership(membership)
            package = {
                "status": "READY_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE",
                "request_rows": [
                    {
                        "request_id": "KIS_AXIS_001",
                        "axis": "kis_us_stocks",
                        "canonical_target_file": str(membership),
                        "current_caveated_row_count": 1,
                        "source_verified_ready_row_count": 1,
                        "source_verified_gap_after_ready_rows": 0,
                        "required_source_acquisition_row_count": 0,
                    }
                ],
                "response_shards": [
                    {
                        "request_id": "KIS_AXIS_001",
                        "axis": "kis_us_stocks",
                        "path": str(Path(tmp) / "response.csv"),
                    }
                ],
            }

            report = worklist_mod.build_report("2026-05-16T12:00:00+09:00", package=package)

        self.assertEqual(report["status"], "READY_AXIS_WIDE_REPLACEMENT_WORKLISTS")
        self.assertEqual(report["worklist_row_count"], 1)
        self.assertEqual(report["worklist_rows"][0]["symbol"], "AAA")
        self.assertEqual(report["worklist_rows"][0]["replacement_symbol"], "AAA")
        self.assertEqual(report["worklist_rows"][0]["replacement_source"], "")
        self.assertEqual(report["worklist_rows"][0]["request_source_verified_ready_row_count"], "1")
        self.assertEqual(report["worklist_rows"][0]["request_required_source_acquisition_row_count"], "0")
        self.assertEqual(report["axis_reports"][0]["source_verified_ready_row_count"], 1)
        self.assertEqual(report["axis_reports"][0]["required_source_acquisition_row_count"], 0)
        self.assertTrue(report["axis_reports"][0]["row_count_matches_required"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_count_mismatch_blocks_worklist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            membership = Path(tmp) / "membership.csv"
            self.write_membership(membership)
            package = {
                "status": "READY_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE",
                "request_rows": [
                    {
                        "request_id": "KIS_AXIS_001",
                        "axis": "kis_us_stocks",
                        "canonical_target_file": str(membership),
                        "current_caveated_row_count": 2,
                    }
                ],
                "response_shards": [{"request_id": "KIS_AXIS_001", "path": str(Path(tmp) / "response.csv")}],
            }

            report = worklist_mod.build_report("2026-05-16T12:00:00+09:00", package=package)

        self.assertEqual(report["status"], "BLOCK_AXIS_WIDE_REPLACEMENT_WORKLISTS")
        self.assertIn("worklist_count_mismatch_for_KIS_AXIS_001", report["blockers"])


if __name__ == "__main__":
    unittest.main()
