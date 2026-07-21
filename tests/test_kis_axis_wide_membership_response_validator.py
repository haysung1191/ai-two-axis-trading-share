from __future__ import annotations

import importlib.util
import csv
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_axis_wide_membership_response_validator.py")
SPEC = importlib.util.spec_from_file_location("build_kis_axis_wide_membership_response_validator", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class KisAxisWideMembershipResponseValidatorTests(unittest.TestCase):
    def package(self) -> dict:
        return {
            "status": "READY_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE",
            "request_count": 1,
            "request_rows": [{"request_id": "KIS_AXIS_001", "axis": "kis_us_stocks"}],
        }

    def test_blank_template_blocks_import_review(self) -> None:
        rows = [{"request_id": "KIS_AXIS_001", "axis": "kis_us_stocks", "symbol": "", "asset_type": ""}]
        report = validator.build_report(
            "2026-05-16T11:00:00+09:00",
            package=self.package(),
            response_rows=rows,
            response_path=Path("response.csv"),
        )

        self.assertEqual(report["status"], "BLOCK_AXIS_WIDE_MEMBERSHIP_RESPONSE")
        self.assertIn("no_valid_axis_membership_rows", report["blockers"])
        self.assertEqual(report["blocked_row_count"], 1)
        self.assertIn("response_row_blank", report["blocked_rows"][0]["blockers"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_valid_operation_ready_row_passes_review(self) -> None:
        rows = [
            {
                "request_id": "KIS_AXIS_001",
                "axis": "kis_us_stocks",
                "symbol": "ABC",
                "asset_type": "STOCK",
                "active_from": "2000-01-01",
                "active_to": "",
                "listed_date": "2000-01-01",
                "delisted_date": "",
                "source": "licensed_vendor_security_master:dataset",
                "snapshot_id": "snap_20260516",
                "evidence_quality": "licensed_vendor",
                "notes": "reviewed source",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            response_path = Path(tmp) / "response.csv"
            response_path.write_text("placeholder", encoding="utf-8")
            report = validator.build_report(
                "2026-05-16T11:00:00+09:00",
                package=self.package(),
                response_rows=rows,
                response_path=response_path,
            )

        self.assertEqual(report["status"], "READY_AXIS_WIDE_MEMBERSHIP_IMPORT_REVIEW")
        self.assertEqual(report["valid_row_count"], 1)
        self.assertEqual(report["blocked_row_count"], 0)
        self.assertTrue(report["replacement_coverage_sufficient"])
        self.assertFalse(report["operation_ready"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_insufficient_replacement_coverage_blocks_import_review(self) -> None:
        package = {
            "status": "READY_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE",
            "request_count": 1,
            "request_rows": [
                {
                    "request_id": "KIS_AXIS_001",
                    "axis": "kis_us_stocks",
                    "current_caveated_row_count": 2,
                }
            ],
        }
        rows = [
            {
                "request_id": "KIS_AXIS_001",
                "axis": "kis_us_stocks",
                "symbol": "ABC",
                "asset_type": "STOCK",
                "active_from": "2000-01-01",
                "source": "licensed_vendor_security_master:dataset",
                "snapshot_id": "snap",
                "evidence_quality": "licensed_vendor",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            response_path = Path(tmp) / "response.csv"
            response_path.write_text("placeholder", encoding="utf-8")
            report = validator.build_report(
                "2026-05-16T11:00:00+09:00",
                package=package,
                response_rows=rows,
                response_path=response_path,
            )

        self.assertEqual(report["status"], "BLOCK_AXIS_WIDE_MEMBERSHIP_RESPONSE")
        self.assertIn("axis_replacement_coverage_insufficient", report["blockers"])
        self.assertFalse(report["replacement_coverage_sufficient"])
        self.assertEqual(report["insufficient_replacement_coverage_rows"][0]["remaining_replacement_row_count"], 1)

    def test_rejected_source_markers_block_row(self) -> None:
        rows = [
            {
                "request_id": "KIS_AXIS_001",
                "axis": "kis_us_stocks",
                "symbol": "ABC",
                "asset_type": "STOCK",
                "active_from": "2000-01-01",
                "source": "current_snapshot_caveated",
                "snapshot_id": "snap",
                "evidence_quality": "licensed_vendor",
            }
        ]
        report = validator.build_report(
            "2026-05-16T11:00:00+09:00",
            package=self.package(),
            response_rows=rows,
            response_path=Path("response.csv"),
        )

        self.assertIn("blocked_response_rows_present", report["blockers"])
        self.assertIn("rejected_source_marker_found", report["blocked_rows"][0]["blockers"])

    def test_axis_mismatch_blocks_row(self) -> None:
        rows = [
            {
                "request_id": "KIS_AXIS_001",
                "axis": "kis_us_etfs",
                "symbol": "ABC",
                "asset_type": "ETF",
                "active_from": "2000-01-01",
                "source": "licensed_vendor_security_master:dataset",
                "snapshot_id": "snap",
                "evidence_quality": "licensed_vendor",
            }
        ]
        report = validator.build_report(
            "2026-05-16T11:00:00+09:00",
            package=self.package(),
            response_rows=rows,
            response_path=Path("response.csv"),
        )

        self.assertIn("axis_does_not_match_request", report["blocked_rows"][0]["blockers"])

    def test_read_response_rows_uses_shards_and_ignores_duplicate_blank_main_seeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            main = tmp_path / "main.csv"
            shard = tmp_path / "KIS_AXIS_001_kis_us_stocks_response.csv"
            fields = [
                "request_id",
                "axis",
                "symbol",
                "asset_type",
                "active_from",
                "active_to",
                "listed_date",
                "delisted_date",
                "source",
                "snapshot_id",
                "evidence_quality",
                "notes",
            ]
            for path, symbol in [(main, ""), (shard, "ABC")]:
                with path.open("w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fields)
                    writer.writeheader()
                    writer.writerow(
                        {
                            "request_id": "KIS_AXIS_001",
                            "axis": "kis_us_stocks",
                            "symbol": symbol,
                            "asset_type": "STOCK" if symbol else "",
                            "active_from": "2000-01-01" if symbol else "",
                            "source": "licensed_vendor_security_master:dataset" if symbol else "",
                            "snapshot_id": "snap" if symbol else "",
                            "evidence_quality": "licensed_vendor" if symbol else "",
                        }
                    )

            rows = validator.read_response_rows({"response_shards": [{"path": str(shard)}]}, main)
            input_files = validator.response_input_files({"response_shards": [{"path": str(shard)}]}, main)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbol"], "ABC")
        self.assertEqual(input_files, [str(main), str(shard)])


if __name__ == "__main__":
    unittest.main()
