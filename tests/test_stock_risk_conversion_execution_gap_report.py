from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_risk_conversion_execution_gap_report.py")
SPEC = importlib.util.spec_from_file_location("build_stock_risk_conversion_execution_gap_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
gap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gap)


class StockRiskConversionExecutionGapReportTests(unittest.TestCase):
    def test_reports_candidate_mismatch_as_not_gatekeeper_ready(self) -> None:
        report = gap.build_report(
            {
                "candidate_id": "stock_aggressive_trim22",
                "sizing_overlay": {"recommended_fixed_exposure_cap": 0.65},
            },
            {
                "frozen_model": "rule_breadth_it_us5_cap",
                "best_overlay": "fixed_exposure_075",
                "rows": [{"overlay": "fixed_exposure_065", "cagr": 0.2, "mdd": -0.19, "sharpe": 1.2}],
            },
        )

        self.assertEqual(report["status"], "NEEDS_CANDIDATE_SPECIFIC_CONVERSION_BACKTEST")
        self.assertFalse(report["same_candidate"])
        self.assertTrue(report["same_overlay_available"])
        self.assertIn("SPEC_CANDIDATE_NOT_COVERED_BY_EXISTING_WRAPPER", report["gap_summary"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_ready_only_when_candidate_and_overlay_match(self) -> None:
        report = gap.build_report(
            {
                "candidate_id": "stock_aggressive_trim22",
                "sizing_overlay": {"recommended_fixed_exposure_cap": 0.65},
            },
            {
                "frozen_model": "stock_aggressive_trim22",
                "best_overlay": "fixed_exposure_065",
                "rows": [{"overlay": "fixed_exposure_065", "cagr": 0.45, "mdd": -0.199, "sharpe": 1.7}],
            },
        )

        self.assertEqual(report["status"], "READY_FOR_GATEKEEPER_REVIEW")
        self.assertTrue(report["same_candidate"])
        self.assertTrue(report["same_overlay_available"])
        self.assertEqual(report["gap_summary"], [])

    def test_candidate_specific_evidence_resolves_wrapper_mismatch(self) -> None:
        report = gap.build_report(
            {
                "candidate_id": "stock_aggressive_trim22",
                "sizing_overlay": {"recommended_fixed_exposure_cap": 0.65},
            },
            {
                "frozen_model": "rule_breadth_it_us5_cap",
                "best_overlay": "fixed_exposure_075",
                "rows": [{"overlay": "fixed_exposure_075", "cagr": 0.21, "mdd": -0.19, "sharpe": 1.2}],
            },
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "candidate_id": "stock_aggressive_trim22",
                "source_variant": "tail_release_trim22",
                "after_fixed_exposure": {
                    "overlay": "fixed_exposure_065",
                    "estimated_cagr": 0.459,
                    "estimated_mdd": -0.199,
                    "estimated_sharpe": 1.74,
                    "gate_result": "pass_mdd_margin",
                },
            },
        )

        self.assertEqual(report["status"], "READY_FOR_GATEKEEPER_REVIEW")
        self.assertFalse(report["same_candidate"])
        self.assertFalse(report["same_overlay_available"])
        self.assertTrue(report["candidate_specific_evidence_ready"])
        self.assertEqual(report["gap_summary"], [])
        self.assertEqual(report["candidate_specific_evidence"]["overlay"], "fixed_exposure_065")


if __name__ == "__main__":
    unittest.main()
