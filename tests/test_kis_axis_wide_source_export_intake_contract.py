from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_kis_axis_wide_source_export_intake_contract.py")
SPEC = importlib.util.spec_from_file_location("build_kis_axis_wide_source_export_intake_contract", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class KisAxisWideSourceExportIntakeContractTests(unittest.TestCase):
    def test_contract_creates_manifest_and_template_then_blocks_example_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            with patch.object(module, "EXPORT_DIR", export_dir), patch.object(
                module, "MANIFEST", export_dir / "axis_wide_source_export_manifest.csv"
            ), patch.object(
                module, "NORMALIZED_TEMPLATE", export_dir / "axis_wide_membership_export_normalized_template.csv"
            ):
                report = module.build_report("2026-05-16T00:00:00+09:00")

        self.assertEqual(report["status"], "BLOCK_SOURCE_EXPORT_INTAKE")
        self.assertEqual(report["valid_export_count"], 0)
        self.assertIn("export_id_missing_or_example", report["blockers"])
        self.assertIn("local_file_missing_on_disk", report["blockers"])
        self.assertFalse(report["safety"]["live_enabled"])

    def test_valid_normalized_export_is_accepted_for_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            data_dir = export_dir / "exports"
            data_dir.mkdir(parents=True)
            export_file = data_dir / "krx.csv"
            with export_file.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=module.NORMALIZED_COLUMNS)
                writer.writeheader()
                writer.writerow(
                    {
                        "axis": "kis_korea_stocks",
                        "symbol": "000020",
                        "asset_type": "korea_stock",
                        "active_from": "1976-06-30",
                        "active_to": "",
                        "listed_date": "1976-06-30",
                        "delisted_date": "",
                        "source": "KRX Data Marketplace",
                        "snapshot_id": "krx_export_20260516",
                        "evidence_quality": "exchange_official",
                        "source_artifact_path": str(export_file),
                        "license_scope": "reviewed_internal_research",
                        "exchange": "KRX",
                        "issuer_name": "sample",
                        "security_id": "KR7000020008",
                        "notes": "test",
                    }
                )
            manifest = export_dir / "axis_wide_source_export_manifest.csv"
            with manifest.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=module.MANIFEST_COLUMNS)
                writer.writeheader()
                writer.writerow(
                    {
                        "export_id": "KRX_EXPORT_20260516",
                        "source_family": "exchange_official",
                        "source_name": "KRX Data Marketplace",
                        "source_url": "https://data.krx.co.kr/",
                        "local_file": "exports\\krx.csv",
                        "snapshot_id": "krx_export_20260516",
                        "license_scope": "reviewed_internal_research",
                        "evidence_quality": "exchange_official",
                        "covered_axes": "kis_korea_stocks",
                        "notes": "test",
                    }
                )

            with patch.object(module, "EXPORT_DIR", export_dir), patch.object(module, "MANIFEST", manifest), patch.object(
                module, "NORMALIZED_TEMPLATE", export_dir / "axis_wide_membership_export_normalized_template.csv"
            ):
                report = module.build_report("2026-05-16T00:00:00+09:00", ensure_contract_files=False)

        self.assertEqual(report["status"], "READY_SOURCE_EXPORTS_FOR_REPLACEMENT_MAPPING")
        self.assertEqual(report["valid_export_count"], 1)
        self.assertEqual(report["export_reports"][0]["normalized_validation"]["row_count"], 1)
        self.assertEqual(report["export_reports"][0]["normalized_validation"]["valid_row_count"], 1)
        self.assertEqual(report["export_reports"][0]["normalized_validation"]["invalid_row_count"], 0)

    def test_normalized_rows_with_current_snapshot_quality_are_rejected(self) -> None:
        row = {
            "axis": "kis_us_stocks",
            "symbol": "A",
            "asset_type": "us_stock",
            "active_from": "2026-05-13",
            "source": "current snapshot",
            "snapshot_id": "snapshot",
            "evidence_quality": "current_snapshot_caveated",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=module.NORMALIZED_COLUMNS)
                writer.writeheader()
                writer.writerow(row)
            result = module.validate_normalized_rows(path, "snapshot", "licensed_vendor")

        self.assertEqual(result["sample_valid_row_count"], 0)
        self.assertIn("evidence_quality_mismatch", result["sample_blockers"][0]["blockers"])
        self.assertEqual(result["invalid_row_count"], 1)

    def test_source_artifact_path_and_license_scope_are_required_per_row(self) -> None:
        row = {
            "axis": "kis_us_stocks",
            "symbol": "A",
            "asset_type": "us_stock",
            "active_from": "1999-01-01",
            "source": "licensed vendor",
            "snapshot_id": "snapshot",
            "evidence_quality": "licensed_vendor",
            "source_artifact_path": "",
            "license_scope": "",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing_metadata.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=module.NORMALIZED_COLUMNS)
                writer.writeheader()
                writer.writerow(row)
            result = module.validate_normalized_rows(path, "snapshot", "licensed_vendor", ["kis_us_stocks"])

        self.assertEqual(result["invalid_row_count"], 1)
        self.assertIn("source_artifact_path_missing", result["blocked_rows_sample"][0]["blockers"])
        self.assertIn("license_scope_missing", result["blocked_rows_sample"][0]["blockers"])

    def test_invalid_row_after_sample_window_blocks_entire_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            data_dir = export_dir / "exports"
            data_dir.mkdir(parents=True)
            export_file = data_dir / "vendor.csv"
            good_row = {
                "axis": "kis_us_stocks",
                "symbol": "A",
                "asset_type": "us_stock",
                "active_from": "1999-01-01",
                "active_to": "",
                "listed_date": "1999-01-01",
                "delisted_date": "",
                "source": "licensed vendor",
                "snapshot_id": "vendor_20260516",
                "evidence_quality": "licensed_vendor",
                "source_artifact_path": str(export_file),
                "license_scope": "reviewed_internal_research",
                "exchange": "NYSE",
                "issuer_name": "sample",
                "security_id": "id",
                "notes": "test",
            }
            bad_row = dict(good_row)
            bad_row["symbol"] = "AA"
            bad_row["snapshot_id"] = "wrong_snapshot"
            with export_file.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=module.NORMALIZED_COLUMNS)
                writer.writeheader()
                for index in range(55):
                    row = dict(good_row)
                    row["symbol"] = f"A{index:03d}"
                    writer.writerow(row)
                writer.writerow(bad_row)
            manifest = export_dir / "axis_wide_source_export_manifest.csv"
            with manifest.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=module.MANIFEST_COLUMNS)
                writer.writeheader()
                writer.writerow(
                    {
                        "export_id": "VENDOR_EXPORT_20260516",
                        "source_family": "licensed_vendor",
                        "source_name": "licensed vendor",
                        "source_url": "",
                        "local_file": "exports\\vendor.csv",
                        "snapshot_id": "vendor_20260516",
                        "license_scope": "reviewed_internal_research",
                        "evidence_quality": "licensed_vendor",
                        "covered_axes": "kis_us_stocks",
                        "notes": "test",
                    }
                )

            with patch.object(module, "EXPORT_DIR", export_dir), patch.object(module, "MANIFEST", manifest), patch.object(
                module, "NORMALIZED_TEMPLATE", export_dir / "axis_wide_membership_export_normalized_template.csv"
            ):
                report = module.build_report("2026-05-16T00:00:00+09:00", ensure_contract_files=False)

        self.assertEqual(report["status"], "BLOCK_SOURCE_EXPORT_INTAKE")
        self.assertEqual(report["valid_export_count"], 0)
        validation = report["export_reports"][0]["normalized_validation"]
        self.assertEqual(validation["row_count"], 56)
        self.assertEqual(validation["invalid_row_count"], 1)
        self.assertIn("normalized_export_rows_not_ready", report["blockers"])

    def test_manifest_covered_axes_must_match_normalized_row_axes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            data_dir = export_dir / "exports"
            data_dir.mkdir(parents=True)
            export_file = data_dir / "vendor.csv"
            with export_file.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=module.NORMALIZED_COLUMNS)
                writer.writeheader()
                writer.writerow(
                    {
                        "axis": "kis_korea_stocks",
                        "symbol": "000020",
                        "asset_type": "korea_stock",
                        "active_from": "1976-06-30",
                        "active_to": "",
                        "listed_date": "1976-06-30",
                        "delisted_date": "",
                        "source": "licensed vendor",
                        "snapshot_id": "vendor_20260516",
                        "evidence_quality": "licensed_vendor",
                        "source_artifact_path": str(export_file),
                        "license_scope": "reviewed_internal_research",
                        "exchange": "KRX",
                        "issuer_name": "sample",
                        "security_id": "id",
                        "notes": "test",
                    }
                )
            manifest = export_dir / "axis_wide_source_export_manifest.csv"
            with manifest.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=module.MANIFEST_COLUMNS)
                writer.writeheader()
                writer.writerow(
                    {
                        "export_id": "VENDOR_EXPORT_20260516",
                        "source_family": "licensed_vendor",
                        "source_name": "licensed vendor",
                        "source_url": "",
                        "local_file": "exports\\vendor.csv",
                        "snapshot_id": "vendor_20260516",
                        "license_scope": "reviewed_internal_research",
                        "evidence_quality": "licensed_vendor",
                        "covered_axes": "kis_us_stocks",
                        "notes": "test",
                    }
                )

            with patch.object(module, "EXPORT_DIR", export_dir), patch.object(module, "MANIFEST", manifest), patch.object(
                module, "NORMALIZED_TEMPLATE", export_dir / "axis_wide_membership_export_normalized_template.csv"
            ):
                report = module.build_report("2026-05-16T00:00:00+09:00", ensure_contract_files=False)

        self.assertEqual(report["status"], "BLOCK_SOURCE_EXPORT_INTAKE")
        validation = report["export_reports"][0]["normalized_validation"]
        self.assertEqual(validation["invalid_row_count"], 1)
        self.assertIn(
            "axis_not_declared_in_manifest_covered_axes",
            validation["blocked_rows_sample"][0]["blockers"],
        )

    def test_date_format_and_interval_consistency_are_validated(self) -> None:
        row = {
            "axis": "kis_us_stocks",
            "symbol": "A",
            "asset_type": "us_stock",
            "active_from": "2026-02-31",
            "active_to": "2025-01-01",
            "listed_date": "2024-01-01",
            "delisted_date": "2023-12-31",
            "source": "licensed vendor",
            "snapshot_id": "snapshot",
            "evidence_quality": "licensed_vendor",
            "source_artifact_path": "exports/vendor.csv",
            "license_scope": "reviewed_internal_research",
            "exchange": "NYSE",
            "issuer_name": "sample",
            "security_id": "id",
            "notes": "test",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad_dates.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=module.NORMALIZED_COLUMNS)
                writer.writeheader()
                writer.writerow(row)
            result = module.validate_normalized_rows(path, "snapshot", "licensed_vendor", ["kis_us_stocks"])

        blockers = result["blocked_rows_sample"][0]["blockers"]
        self.assertEqual(result["invalid_row_count"], 1)
        self.assertIn("active_from_invalid_iso_date", blockers)
        self.assertIn("delisted_date_before_listed_date", blockers)

    def test_active_to_before_active_from_is_blocked_when_dates_are_valid(self) -> None:
        row = {
            "axis": "kis_us_stocks",
            "symbol": "A",
            "asset_type": "us_stock",
            "active_from": "2026-01-02",
            "active_to": "2026-01-01",
            "listed_date": "2024-01-01",
            "delisted_date": "",
            "source": "licensed vendor",
            "snapshot_id": "snapshot",
            "evidence_quality": "licensed_vendor",
            "source_artifact_path": "exports/vendor.csv",
            "license_scope": "reviewed_internal_research",
            "exchange": "NYSE",
            "issuer_name": "sample",
            "security_id": "id",
            "notes": "test",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad_interval.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=module.NORMALIZED_COLUMNS)
                writer.writeheader()
                writer.writerow(row)
            result = module.validate_normalized_rows(path, "snapshot", "licensed_vendor", ["kis_us_stocks"])

        self.assertEqual(result["invalid_row_count"], 1)
        self.assertIn("active_to_before_active_from", result["blocked_rows_sample"][0]["blockers"])

    def test_duplicate_axis_symbol_asset_type_is_blocked_at_intake(self) -> None:
        row = {
            "axis": "kis_us_stocks",
            "symbol": "A",
            "asset_type": "us_stock",
            "active_from": "2020-01-01",
            "active_to": "",
            "listed_date": "2020-01-01",
            "delisted_date": "",
            "source": "licensed vendor",
            "snapshot_id": "snapshot",
            "evidence_quality": "licensed_vendor",
            "source_artifact_path": "exports/vendor.csv",
            "license_scope": "reviewed_internal_research",
            "exchange": "NYSE",
            "issuer_name": "sample",
            "security_id": "id",
            "notes": "test",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicates.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=module.NORMALIZED_COLUMNS)
                writer.writeheader()
                writer.writerow(row)
                writer.writerow(row)
            result = module.validate_normalized_rows(path, "snapshot", "licensed_vendor", ["kis_us_stocks"])

        self.assertEqual(result["invalid_row_count"], 1)
        blockers = result["blocked_rows_sample"][0]["blockers"]
        self.assertIn("duplicate_axis_symbol_asset_type", blockers)
        self.assertIn("duplicate_membership_interval", blockers)

    def test_duplicate_symbol_with_different_interval_is_still_blocked(self) -> None:
        row1 = {
            "axis": "kis_us_stocks",
            "symbol": "A",
            "asset_type": "us_stock",
            "active_from": "2020-01-01",
            "active_to": "2021-01-01",
            "listed_date": "2020-01-01",
            "delisted_date": "",
            "source": "licensed vendor",
            "snapshot_id": "snapshot",
            "evidence_quality": "licensed_vendor",
            "source_artifact_path": "exports/vendor.csv",
            "license_scope": "reviewed_internal_research",
            "exchange": "NYSE",
            "issuer_name": "sample",
            "security_id": "id",
            "notes": "test",
        }
        row2 = dict(row1)
        row2["active_from"] = "2022-01-01"
        row2["active_to"] = ""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate_key.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=module.NORMALIZED_COLUMNS)
                writer.writeheader()
                writer.writerow(row1)
                writer.writerow(row2)
            result = module.validate_normalized_rows(path, "snapshot", "licensed_vendor", ["kis_us_stocks"])

        self.assertEqual(result["invalid_row_count"], 1)
        self.assertIn("duplicate_axis_symbol_asset_type", result["blocked_rows_sample"][0]["blockers"])


if __name__ == "__main__":
    unittest.main()
