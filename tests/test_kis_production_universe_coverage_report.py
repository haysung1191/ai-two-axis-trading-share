from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_kis_production_universe_coverage_report.py")
SPEC = importlib.util.spec_from_file_location("build_kis_production_universe_coverage_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
coverage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(coverage)


class KisProductionUniverseCoverageReportTests(unittest.TestCase):
    def test_manifest_summary_surfaces_local_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            coverage.write_json(
                path,
                {
                    "source_mode": "local_coverage_snapshot",
                    "asset_count": 18,
                    "row_count": 1000,
                    "missing_bars_count": 0,
                },
            )

            summary = coverage.manifest_summary("kis_us_etfs", path)

        self.assertEqual(summary["axis"], "kis_us_etfs")
        self.assertTrue(summary["local_coverage_present"])
        self.assertEqual(summary["asset_count"], 18)

    def test_build_report_blocks_on_kis_environment_not_local_coverage(self) -> None:
        def fake_local(label, source_dir, operating_dir):
            return {
                "axis": label,
                "source_mode": "local_price_files",
                "source_asset_count": 10,
                "operating_asset_count": 5,
                "local_coverage_present": True,
            }

        def fake_manifest(label, path):
            return {
                "axis": label,
                "source_mode": "local_coverage_snapshot",
                "asset_count": 10,
                "local_coverage_present": True,
            }

        with (
            patch.object(coverage, "local_market_summary", side_effect=fake_local),
            patch.object(coverage, "manifest_summary", side_effect=fake_manifest),
            patch.object(
                coverage,
                "read_json",
                return_value={"status": "BLOCKED", "missing_requirements": ["KIS_APP_KEY"]},
            ),
        ):
            report = coverage.build_report()

        self.assertEqual(report["status"], "LOCAL_COVERAGE_READY_API_ENV_BLOCKED")
        self.assertTrue(report["all_four_axes_local_coverage_present"])
        self.assertFalse(report["kis_api_environment_ready"])
        self.assertFalse(report["safety"]["does_call_kis_api"])

    def test_build_report_accepts_environment_recheck_ready_status(self) -> None:
        def fake_local(label, source_dir, operating_dir):
            return {
                "axis": label,
                "source_mode": "local_price_files",
                "source_asset_count": 10,
                "operating_asset_count": 5,
                "local_coverage_present": True,
            }

        def fake_manifest(label, path):
            return {
                "axis": label,
                "source_mode": "local_coverage_snapshot",
                "asset_count": 10,
                "local_coverage_present": True,
            }

        with (
            patch.object(coverage, "local_market_summary", side_effect=fake_local),
            patch.object(coverage, "manifest_summary", side_effect=fake_manifest),
            patch.object(
                coverage,
                "read_json",
                return_value={
                    "status": "READY_FOR_STOCK_PREFLIGHT_RECHECK",
                    "missing_requirements": [],
                },
            ),
        ):
            report = coverage.build_report()

        self.assertEqual(report["status"], "KIS_API_UNIVERSE_READY")
        self.assertTrue(report["kis_api_environment_ready"])


if __name__ == "__main__":
    unittest.main()
