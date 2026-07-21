from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_official_open_trading_api_source_probe.py")
SPEC = importlib.util.spec_from_file_location("build_kis_official_open_trading_api_source_probe", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class KisOfficialOpenTradingApiSourceProbeTests(unittest.TestCase):
    def test_build_report_marks_official_repo_as_current_master_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            stocks_info = repo / "stocks_info"
            stocks_info.mkdir()
            (stocks_info / "kis_kospi_code_mst.py").write_text("", encoding="utf-8")
            (stocks_info / "kis_kosdaq_code_mst.py").write_text("", encoding="utf-8")
            (stocks_info / "overseas_stock_code.py").write_text("", encoding="utf-8")

            report = module.build_report("2026-05-16T00:00:00+09:00", repo=repo)

        self.assertEqual(report["status"], "REVIEW_ONLY_NOT_OPERATION_READY_FOR_AXIS_WIDE_PIT")
        self.assertFalse(report["accepted_for_replacement_worklist_fill"])
        self.assertEqual(report["operation_ready_replacement_row_count"], 0)
        self.assertIn(
            "official_repo_samples_are_current_master_downloaders_not_historical_pit_membership",
            report["blockers"],
        )
        self.assertTrue(all(not row["historical_pit_membership_available"] for row in report["axis_reports"]))
        self.assertTrue(all(not row["replacement_worklist_operation_ready"] for row in report["axis_reports"]))

    def test_license_file_is_detected_without_changing_operation_ready_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "stocks_info").mkdir()
            (repo / "LICENSE").write_text("test", encoding="utf-8")

            report = module.build_report("2026-05-16T00:00:00+09:00", repo=repo)

        self.assertTrue(report["license_file_exists"])
        self.assertFalse(report["accepted_for_replacement_worklist_fill"])
        self.assertIn("operation_ready_replacement_rows_remain_zero", report["blockers"])

    def test_render_md_surfaces_decision_and_next_action(self) -> None:
        report = {
            "generated_at": "2026-05-16T00:00:00+09:00",
            "status": "REVIEW_ONLY_NOT_OPERATION_READY_FOR_AXIS_WIDE_PIT",
            "accepted_for_replacement_worklist_fill": False,
            "operation_ready_replacement_row_count": 0,
            "license_file_exists": False,
            "axis_reports": [
                {
                    "axis": "kis_us_stocks",
                    "official_current_master_available": True,
                    "historical_pit_membership_available": False,
                    "replacement_worklist_operation_ready": False,
                }
            ],
            "single_next_action": "Acquire licensed historical membership data.",
        }

        md = module.render_md(report)

        self.assertIn("REVIEW_ONLY_NOT_OPERATION_READY_FOR_AXIS_WIDE_PIT", md)
        self.assertIn("Acquire licensed historical membership data.", md)


if __name__ == "__main__":
    unittest.main()
