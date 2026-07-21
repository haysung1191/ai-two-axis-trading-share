from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_kis_axis_wide_source_export_inbox_status.py")
SPEC = importlib.util.spec_from_file_location("build_kis_axis_wide_source_export_inbox_status", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def write_csv(path: Path, headers: list[str], row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerow(row)


class KisAxisWideSourceExportInboxStatusTests(unittest.TestCase):
    def test_creates_standard_raw_and_exports_drop_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            manifest = export_dir / "axis_wide_source_export_manifest.csv"
            template = export_dir / "axis_wide_membership_export_normalized_template.csv"
            raw_dir = export_dir / "raw"
            exports_dir = export_dir / "exports"
            write_csv(manifest, module.intake_contract.MANIFEST_COLUMNS, {"export_id": "EXAMPLE"})
            write_csv(template, module.intake_contract.NORMALIZED_COLUMNS, {})
            with patch.object(module, "EXPORT_DIR", export_dir), patch.object(module, "RAW_DIR", raw_dir), patch.object(
                module, "NORMALIZED_EXPORT_DIR", exports_dir
            ), patch.object(module, "MANIFEST", manifest), patch.object(
                module, "NORMALIZED_TEMPLATE", template
            ), patch.object(module.intake_contract, "MANIFEST", manifest):
                report = module.build_report("2026-05-16T00:00:00+09:00")
                raw_exists = raw_dir.is_dir()
                exports_exists = exports_dir.is_dir()

        self.assertTrue(raw_exists)
        self.assertTrue(exports_exists)
        self.assertIn(str(raw_dir), report["created_dirs"])
        self.assertIn(str(exports_dir), report["created_dirs"])

    def test_blocks_when_only_contract_files_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            manifest = export_dir / "axis_wide_source_export_manifest.csv"
            template = export_dir / "axis_wide_membership_export_normalized_template.csv"
            write_csv(manifest, module.intake_contract.MANIFEST_COLUMNS, {"export_id": "EXAMPLE"})
            write_csv(template, module.intake_contract.NORMALIZED_COLUMNS, {})
            with patch.object(module, "EXPORT_DIR", export_dir), patch.object(module, "MANIFEST", manifest), patch.object(
                module, "NORMALIZED_TEMPLATE", template
            ), patch.object(module.intake_contract, "MANIFEST", manifest):
                report = module.build_report("2026-05-16T00:00:00+09:00")

        self.assertEqual(report["status"], "BLOCK_NO_SOURCE_EXPORT_FILES_IN_INBOX")
        self.assertEqual(report["actionable_file_count"], 0)
        self.assertFalse(report["safety"]["live_enabled"])

    def test_detects_unreferenced_normalized_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            manifest = export_dir / "axis_wide_source_export_manifest.csv"
            template = export_dir / "axis_wide_membership_export_normalized_template.csv"
            normalized = export_dir / "exports" / "krx.csv"
            write_csv(manifest, module.intake_contract.MANIFEST_COLUMNS, {"export_id": "EXAMPLE"})
            write_csv(template, module.intake_contract.NORMALIZED_COLUMNS, {})
            write_csv(
                normalized,
                module.intake_contract.NORMALIZED_COLUMNS,
                {
                    "axis": "kis_korea_stocks",
                    "symbol": "000020",
                    "asset_type": "korea_stock",
                    "active_from": "1976-06-30",
                    "source": "KRX Data Marketplace",
                    "snapshot_id": "krx_export_20260516",
                    "evidence_quality": "exchange_official",
                    "source_artifact_path": str(normalized),
                    "license_scope": "reviewed_internal_research",
                },
            )
            with patch.object(module, "EXPORT_DIR", export_dir), patch.object(module, "MANIFEST", manifest), patch.object(
                module, "NORMALIZED_TEMPLATE", template
            ), patch.object(module.intake_contract, "MANIFEST", manifest):
                report = module.build_report("2026-05-16T00:00:00+09:00")

        self.assertEqual(report["status"], "READY_UNREFERENCED_NORMALIZED_EXPORTS_FOUND")
        self.assertEqual(report["unreferenced_normalized_export_count"], 1)
        self.assertEqual(report["actionable_file_count"], 1)

    def test_detects_unreferenced_raw_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            manifest = export_dir / "axis_wide_source_export_manifest.csv"
            template = export_dir / "axis_wide_membership_export_normalized_template.csv"
            raw = export_dir / "raw" / "krx_raw.csv"
            write_csv(manifest, module.intake_contract.MANIFEST_COLUMNS, {"export_id": "EXAMPLE"})
            write_csv(template, module.intake_contract.NORMALIZED_COLUMNS, {})
            write_csv(raw, ["code", "listed"], {"code": "000020", "listed": "1976-06-30"})
            with patch.object(module, "EXPORT_DIR", export_dir), patch.object(module, "MANIFEST", manifest), patch.object(
                module, "NORMALIZED_TEMPLATE", template
            ), patch.object(module.intake_contract, "MANIFEST", manifest):
                report = module.build_report("2026-05-16T00:00:00+09:00")

        self.assertEqual(report["status"], "READY_UNREFERENCED_RAW_EXPORTS_FOUND")
        self.assertEqual(report["unreferenced_raw_or_unknown_export_count"], 1)
        self.assertIn("normalize_kis_axis_wide_source_export.py", report["single_next_action"])

    def test_manifest_referenced_export_is_not_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            manifest = export_dir / "axis_wide_source_export_manifest.csv"
            normalized = export_dir / "exports" / "krx.csv"
            write_csv(
                manifest,
                module.intake_contract.MANIFEST_COLUMNS,
                {"export_id": "KRX_EXPORT", "local_file": "exports\\krx.csv"},
            )
            write_csv(normalized, module.intake_contract.NORMALIZED_COLUMNS, {})
            with patch.object(module, "EXPORT_DIR", export_dir), patch.object(module, "MANIFEST", manifest), patch.object(
                module, "NORMALIZED_TEMPLATE", export_dir / "axis_wide_membership_export_normalized_template.csv"
            ), patch.object(module.intake_contract, "MANIFEST", manifest):
                report = module.build_report("2026-05-16T00:00:00+09:00")

        self.assertEqual(report["actionable_file_count"], 0)
        roles = {row["relative_path"]: row["role"] for row in report["files"]}
        self.assertEqual(roles["exports\\krx.csv"], "manifest_referenced_export")


if __name__ == "__main__":
    unittest.main()
