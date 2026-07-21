from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_axis_wide_source_export_next_command.py")
SPEC = importlib.util.spec_from_file_location("build_kis_axis_wide_source_export_next_command", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class KisAxisWideSourceExportNextCommandTests(unittest.TestCase):
    def test_blocks_when_inbox_has_no_actionable_files(self) -> None:
        report = module.build_report(
            "2026-05-16T00:00:00+09:00",
            inbox_status={"status": "BLOCK_NO_SOURCE_EXPORT_FILES_IN_INBOX", "files": []},
        )

        self.assertEqual(report["status"], "BLOCK_NO_ACTIONABLE_SOURCE_EXPORT_FILE")
        self.assertEqual(report["command_kind"], "none")
        self.assertEqual(report["next_command"], "")
        self.assertIn("no_unreferenced_source_export_file", report["blockers"])
        self.assertFalse(report["safety"]["live_enabled"])

    def test_builds_manifest_upsert_command_for_normalized_export(self) -> None:
        report = module.build_report(
            "2026-05-16T00:00:00+09:00",
            inbox_status={
                "status": "READY_UNREFERENCED_NORMALIZED_EXPORTS_FOUND",
                "files": [
                    {
                        "role": "unreferenced_normalized_export",
                        "relative_path": "exports\\krx.csv",
                    }
                ],
            },
        )

        self.assertEqual(report["status"], "READY_NEXT_COMMAND_FOR_NORMALIZED_EXPORT")
        self.assertEqual(report["command_kind"], "manifest_upsert_dry_run")
        self.assertIn("upsert_kis_axis_wide_source_export_manifest_row.py", report["next_command"])
        self.assertIn('"exports\\krx.csv"', report["next_command"])
        self.assertNotIn("--write", report["next_command"])

    def test_builds_normalizer_command_for_raw_export(self) -> None:
        report = module.build_report(
            "2026-05-16T00:00:00+09:00",
            inbox_status={
                "status": "READY_UNREFERENCED_RAW_EXPORTS_FOUND",
                "files": [
                    {
                        "role": "unreferenced_raw_or_unknown_export",
                        "relative_path": "raw\\vendor_raw.csv",
                    }
                ],
            },
        )

        self.assertEqual(report["status"], "READY_NEXT_COMMAND_FOR_RAW_EXPORT")
        self.assertEqual(report["command_kind"], "normalizer_dry_run")
        self.assertIn("normalize_kis_axis_wide_source_export.py", report["next_command"])
        self.assertIn('"raw\\vendor_raw.csv"', report["next_command"])
        self.assertIn('"exports\\NORMALIZED_FROM_vendor_raw.csv"', report["next_command"])
        self.assertNotIn("--write", report["next_command"])


if __name__ == "__main__":
    unittest.main()
