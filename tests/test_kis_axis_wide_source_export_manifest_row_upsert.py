from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\upsert_kis_axis_wide_source_export_manifest_row.py")
SPEC = importlib.util.spec_from_file_location("upsert_kis_axis_wide_source_export_manifest_row", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def write_normalized_export(path: Path, *, snapshot_id: str = "krx_export_20260516") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=module.intake_contract.NORMALIZED_COLUMNS)
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
                "snapshot_id": snapshot_id,
                "evidence_quality": "exchange_official",
                "source_artifact_path": str(path),
                "license_scope": "reviewed_internal_research",
                "exchange": "KRX",
                "issuer_name": "sample",
                "security_id": "KR7000020008",
                "notes": "test",
            }
        )


def write_example_manifest(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=module.intake_contract.MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerow(
            {
                "export_id": "EXAMPLE_KRX_LISTED_DELISTED_YYYYMMDD",
                "source_family": "exchange_official",
                "source_name": "KRX Data Marketplace",
                "source_url": "https://data.krx.co.kr/",
                "local_file": "exports\\example.csv",
                "snapshot_id": "krx_export_YYYYMMDD",
                "license_scope": "reviewed_internal_research",
                "evidence_quality": "exchange_official",
                "covered_axes": "kis_korea_stocks",
                "notes": "example",
            }
        )


class KisAxisWideSourceExportManifestRowUpsertTests(unittest.TestCase):
    def test_dry_run_replaces_example_without_mutating_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            manifest = export_dir / "axis_wide_source_export_manifest.csv"
            export_file = export_dir / "exports" / "krx.csv"
            write_example_manifest(manifest)
            write_normalized_export(export_file)
            row = module.build_manifest_row(
                export_id="KRX_EXPORT_20260516",
                source_family="exchange_official",
                source_name="KRX Data Marketplace",
                source_url="https://data.krx.co.kr/",
                local_file="exports\\krx.csv",
                snapshot_id="krx_export_20260516",
                license_scope="reviewed_internal_research",
                evidence_quality="exchange_official",
                covered_axes="kis_korea_stocks",
                notes="test",
            )
            with patch.object(module, "EXPORT_DIR", export_dir), patch.object(
                module.intake_contract, "EXPORT_DIR", export_dir
            ):
                report = module.build_report(
                    "2026-05-16T00:00:00+09:00",
                    row=row,
                    write=False,
                    replace_example=True,
                    path_blockers=[],
                    manifest_path=manifest,
                )
                rows_after = module.read_manifest(manifest)

        self.assertEqual(report["status"], "DRY_RUN_READY_TO_WRITE_SOURCE_EXPORT_MANIFEST_ROW")
        self.assertEqual(report["merge_action"], "replaced_example_row")
        self.assertFalse(report["manifest_mutated"])
        self.assertEqual(rows_after[0]["export_id"], "EXAMPLE_KRX_LISTED_DELISTED_YYYYMMDD")
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_write_replaces_example_row_when_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            manifest = export_dir / "axis_wide_source_export_manifest.csv"
            export_file = export_dir / "exports" / "krx.csv"
            write_example_manifest(manifest)
            write_normalized_export(export_file)
            row = module.build_manifest_row(
                export_id="KRX_EXPORT_20260516",
                source_family="exchange_official",
                source_name="KRX Data Marketplace",
                source_url="https://data.krx.co.kr/",
                local_file="exports\\krx.csv",
                snapshot_id="krx_export_20260516",
                license_scope="reviewed_internal_research",
                evidence_quality="exchange_official",
                covered_axes="kis_korea_stocks",
                notes="test",
            )
            with patch.object(module, "EXPORT_DIR", export_dir), patch.object(
                module.intake_contract, "EXPORT_DIR", export_dir
            ):
                report = module.build_report(
                    "2026-05-16T00:00:00+09:00",
                    row=row,
                    write=True,
                    replace_example=True,
                    path_blockers=[],
                    manifest_path=manifest,
                )
                rows_after = module.read_manifest(manifest)

        self.assertEqual(report["status"], "WROTE_SOURCE_EXPORT_MANIFEST_ROW")
        self.assertTrue(report["manifest_mutated"])
        self.assertEqual(rows_after[0]["export_id"], "KRX_EXPORT_20260516")

    def test_invalid_normalized_export_blocks_manifest_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            manifest = export_dir / "axis_wide_source_export_manifest.csv"
            export_file = export_dir / "exports" / "krx.csv"
            write_example_manifest(manifest)
            write_normalized_export(export_file, snapshot_id="wrong_snapshot")
            row = module.build_manifest_row(
                export_id="KRX_EXPORT_20260516",
                source_family="exchange_official",
                source_name="KRX Data Marketplace",
                source_url="https://data.krx.co.kr/",
                local_file="exports\\krx.csv",
                snapshot_id="krx_export_20260516",
                license_scope="reviewed_internal_research",
                evidence_quality="exchange_official",
                covered_axes="kis_korea_stocks",
                notes="test",
            )
            with patch.object(module, "EXPORT_DIR", export_dir), patch.object(
                module.intake_contract, "EXPORT_DIR", export_dir
            ):
                report = module.build_report(
                    "2026-05-16T00:00:00+09:00",
                    row=row,
                    write=True,
                    replace_example=True,
                    path_blockers=[],
                    manifest_path=manifest,
                )

        self.assertEqual(report["status"], "BLOCK_SOURCE_EXPORT_MANIFEST_ROW_UPSERT")
        self.assertFalse(report["manifest_mutated"])
        self.assertIn("normalized_export_rows_not_ready", report["blockers"])

    def test_resolve_export_relative_path_blocks_outside_landing_zone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(module, "EXPORT_DIR", Path(tmp) / "exports"):
                _, _, blockers = module.resolve_export_relative_path(str(Path(tmp) / "outside.csv"))

        self.assertIn("local_file_outside_export_dir", blockers)

    def test_status_report_audits_current_manifest_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            manifest = export_dir / "axis_wide_source_export_manifest.csv"
            write_example_manifest(manifest)
            with patch.object(module, "EXPORT_DIR", export_dir), patch.object(
                module.intake_contract, "EXPORT_DIR", export_dir
            ):
                report = module.build_status_report(
                    "2026-05-16T00:00:00+09:00",
                    manifest_path=manifest,
                )
                rows_after = module.read_manifest(manifest)

        self.assertEqual(report["status"], "BLOCK_SOURCE_EXPORT_MANIFEST_ROW_UPSERT")
        self.assertTrue(report["status_only"])
        self.assertFalse(report["manifest_mutated"])
        self.assertEqual(report["merge_action"], "status_only_current_manifest_audit")
        self.assertIn("export_id_missing_or_example", report["blockers"])
        self.assertEqual(rows_after[0]["export_id"], "EXAMPLE_KRX_LISTED_DELISTED_YYYYMMDD")

    def test_status_report_passes_when_current_manifest_has_valid_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            manifest = export_dir / "axis_wide_source_export_manifest.csv"
            export_file = export_dir / "exports" / "krx.csv"
            write_normalized_export(export_file)
            with manifest.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=module.intake_contract.MANIFEST_COLUMNS)
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
            with patch.object(module, "EXPORT_DIR", export_dir), patch.object(
                module.intake_contract, "EXPORT_DIR", export_dir
            ):
                report = module.build_status_report(
                    "2026-05-16T00:00:00+09:00",
                    manifest_path=manifest,
                )

        self.assertEqual(report["status"], "READY_MANIFEST_HAS_VALID_SOURCE_EXPORT_ROWS")
        self.assertEqual(report["valid_manifest_row_count"], 1)
        self.assertEqual(report["blocked_manifest_row_count"], 0)


if __name__ == "__main__":
    unittest.main()
