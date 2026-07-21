from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_stock_data_coverage_reality_report.py")
SPEC = importlib.util.spec_from_file_location("build_stock_data_coverage_reality_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
coverage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(coverage)


class StockDataCoverageRealityReportTests(unittest.TestCase):
    def test_no_broad_history_blocks_full_market_backtest_claim(self) -> None:
        narrow = {
            "label": "us_stock_sp100",
            "total_files": 132,
            "stock_files": 132,
            "etf_files": 0,
            "stock_sample_range": {"earliest": "2015-01-01", "latest": "2026-01-01"},
            "etf_sample_range": {"earliest": "", "latest": ""},
        }
        broad_us = {
            "label": "us_full_history",
            "total_files": 0,
            "stock_files": 0,
            "etf_files": 0,
            "stock_sample_range": {"earliest": "", "latest": ""},
            "etf_sample_range": {"earliest": "", "latest": ""},
        }
        broad_kr = dict(broad_us, label="kr_full_history")
        with patch.object(coverage, "scan_price_dirs", return_value=[narrow, broad_us, broad_kr]):
            report = coverage.build_report()

        self.assertEqual(report["status"], "INSUFFICIENT_FOR_FULL_MARKET_BACKTEST")
        self.assertIn("NO_BROAD_US_KR_STOCK_ETF_HISTORY_DIRECTORY", report["blockers"])

    def test_smoke_sized_broad_history_still_blocks_full_market_claim(self) -> None:
        broad_us = {
            "label": "us_full_history",
            "total_files": 4,
            "stock_files": 2,
            "etf_files": 2,
            "stock_sample_range": {"earliest": "2020-01-01", "latest": "2026-01-01"},
            "etf_sample_range": {"earliest": "2020-01-01", "latest": "2026-01-01"},
        }
        broad_kr = dict(broad_us, label="kr_full_history")
        with patch.object(coverage, "scan_price_dirs", return_value=[broad_us, broad_kr]):
            report = coverage.build_report()

        self.assertEqual(report["status"], "INSUFFICIENT_FOR_FULL_MARKET_BACKTEST")
        self.assertIn("BROAD_US_KR_STOCK_ETF_HISTORY_SMOKE_ONLY", report["blockers"])


if __name__ == "__main__":
    unittest.main()
