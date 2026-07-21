from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\normalize_kis_axis_wide_source_export.py")
SPEC = importlib.util.spec_from_file_location("normalize_kis_axis_wide_source_export", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class KisAxisWideSourceExportNormalizerTests(unittest.TestCase):
    def test_dry_run_projects_valid_normalized_rows_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            raw_file = export_dir / "raw" / "krx_raw.csv"
            output_file = export_dir / "exports" / "krx_normalized.csv"
            raw_file.parent.mkdir(parents=True)
            with raw_file.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["code", "listed", "name"])
                writer.writeheader()
                writer.writerow({"code": "000020", "listed": "1976-06-30", "name": "sample"})

            defaults = {
                "axis": "kis_korea_stocks",
                "asset_type": "korea_stock",
                "source": "KRX Data Marketplace",
                "snapshot_id": "krx_export_20260516",
                "evidence_quality": "exchange_official",
                "source_artifact_path": str(raw_file),
                "license_scope": "reviewed_internal_research",
                "exchange": "KRX",
            }
            report = module.build_report(
                "2026-05-16T00:00:00+09:00",
                raw_file=raw_file,
                output_file=output_file,
                write=False,
                column_map={"symbol": "code", "active_from": "listed", "listed_date": "listed", "issuer_name": "name"},
                defaults=defaults,
                assignment_blockers=[],
            )

        self.assertEqual(report["status"], "DRY_RUN_READY_TO_WRITE_NORMALIZED_SOURCE_EXPORT")
        self.assertFalse(report["files_mutated"])
        self.assertEqual(report["normalized_row_count"], 1)
        self.assertEqual(report["projected_validation"]["valid_row_count"], 1)
        self.assertFalse(output_file.exists())
        self.assertFalse(report["safety"]["live_enabled"])

    def test_write_creates_normalized_file_when_projection_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            raw_file = export_dir / "raw" / "vendor_raw.csv"
            output_file = export_dir / "exports" / "vendor_normalized.csv"
            raw_file.parent.mkdir(parents=True)
            with raw_file.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["ticker", "start"])
                writer.writeheader()
                writer.writerow({"ticker": "A", "start": "1999-01-01"})

            report = module.build_report(
                "2026-05-16T00:00:00+09:00",
                raw_file=raw_file,
                output_file=output_file,
                write=True,
                column_map={"symbol": "ticker", "active_from": "start", "listed_date": "start"},
                defaults={
                    "axis": "kis_us_stocks",
                    "asset_type": "us_stock",
                    "source": "licensed vendor",
                    "snapshot_id": "vendor_20260516",
                    "evidence_quality": "licensed_vendor",
                    "source_artifact_path": str(raw_file),
                    "license_scope": "reviewed_internal_research",
                    "exchange": "NYSE",
                },
                assignment_blockers=[],
            )

            rows = list(csv.DictReader(output_file.open("r", encoding="utf-8-sig", newline="")))

        self.assertEqual(report["status"], "WROTE_NORMALIZED_SOURCE_EXPORT")
        self.assertTrue(report["files_mutated"])
        self.assertEqual(rows[0]["symbol"], "A")
        self.assertEqual(rows[0]["snapshot_id"], "vendor_20260516")

    def test_missing_raw_mapping_blocks_projection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            raw_file = export_dir / "raw.csv"
            with raw_file.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["ticker"])
                writer.writeheader()
                writer.writerow({"ticker": "A"})

            report = module.build_report(
                "2026-05-16T00:00:00+09:00",
                raw_file=raw_file,
                output_file=export_dir / "exports" / "out.csv",
                write=False,
                column_map={"symbol": "missing_col"},
                defaults={
                    "axis": "kis_us_stocks",
                    "asset_type": "us_stock",
                    "source": "licensed vendor",
                    "snapshot_id": "vendor_20260516",
                    "evidence_quality": "licensed_vendor",
                    "source_artifact_path": str(raw_file),
                    "license_scope": "reviewed_internal_research",
                    "active_from": "1999-01-01",
                },
                assignment_blockers=[],
            )

        self.assertEqual(report["status"], "BLOCK_SOURCE_EXPORT_NORMALIZATION")
        self.assertIn("mapped_raw_columns_missing", report["blockers"])

    def test_export_path_resolution_blocks_paths_outside_landing_zone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(module, "EXPORT_DIR", Path(tmp) / "exports"):
                _, blockers = module.resolve_export_path(str(Path(tmp) / "outside.csv"))

        self.assertIn("path_outside_axis_wide_source_exports", blockers)


if __name__ == "__main__":
    unittest.main()
