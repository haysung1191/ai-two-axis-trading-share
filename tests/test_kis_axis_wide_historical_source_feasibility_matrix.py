from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_axis_wide_historical_source_feasibility_matrix.py")
SPEC = importlib.util.spec_from_file_location("build_kis_axis_wide_historical_source_feasibility_matrix", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class KisAxisWideHistoricalSourceFeasibilityMatrixTests(unittest.TestCase):
    def test_matrix_blocks_when_no_direct_operation_ready_source_is_captured(self) -> None:
        report = module.build_report(
            "2026-05-16T00:00:00+09:00",
            fill_report={
                "status": "BLOCK_WORKLIST_FILL_PROGRESS",
                "complete_row_count": 0,
                "blocked_row_count": 16444,
                "axis_reports": [
                    {"axis": "kis_us_stocks", "blocked_row_count": 7392},
                    {"axis": "kis_us_etfs", "blocked_row_count": 5195},
                    {"axis": "kis_korea_stocks", "blocked_row_count": 2758},
                    {"axis": "kis_korea_etfs", "blocked_row_count": 1099},
                ],
            },
        )

        self.assertEqual(report["status"], "BLOCK_NO_DIRECT_OPERATION_READY_HISTORICAL_SOURCE_CAPTURED")
        self.assertEqual(report["blocked_worklist_row_count"], 16444)
        self.assertEqual(report["direct_operation_ready_source_count"], 0)
        self.assertGreaterEqual(report["promising_source_count"], 2)
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_current_symbol_directory_is_not_marked_historical_pit_ready(self) -> None:
        report = module.build_report("2026-05-16T00:00:00+09:00", fill_report={"axis_reports": []})
        nasdaq = next(
            row for row in report["source_candidates"] if row["source_id"] == "NASDAQ_TRADER_SYMBOL_DIRECTORY"
        )

        self.assertEqual(nasdaq["feasibility"], "CURRENT_SNAPSHOT_ONLY_NOT_HISTORICAL_PIT")
        self.assertFalse(nasdaq["direct_replacement_ready"])

    def test_render_md_surfaces_candidate_table_and_next_action(self) -> None:
        report = module.build_report("2026-05-16T00:00:00+09:00", fill_report={"axis_reports": []})
        md = module.render_md(report)

        self.assertIn("KIS Axis-Wide Historical Source Feasibility Matrix", md)
        self.assertIn("NASDAQ_TRADER_SYMBOL_DIRECTORY", md)
        self.assertIn(report["single_next_action"], md)


if __name__ == "__main__":
    unittest.main()
