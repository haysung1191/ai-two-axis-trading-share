from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_risk_conversion_candidate_backtest_report.py")
SPEC = importlib.util.spec_from_file_location("build_stock_risk_conversion_candidate_backtest_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
reporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reporter)


class StockRiskConversionCandidateBacktestReportTests(unittest.TestCase):
    def test_maps_stock_aggressive_spec_to_source_row_and_applies_cap(self) -> None:
        report = reporter.build_report(
            {
                "candidate_id": "stock_aggressive__tail_release_top25_mid75_pen35_floor25_conccarrykretfmicro_ct70_trim22_gap02_top2",
                "sizing_overlay": {"recommended_fixed_exposure_cap": 0.65},
                "frozen_scope": {"order_paths_allowed": False},
            },
            {
                "ranked_rows": [
                    {
                        "Variant": "tail_release_top25_mid75_pen35_floor25_conccarrykretfmicro_ct70_trim22_gap02_top2",
                        "CAGR": 0.7060692144490932,
                        "MDD": -0.3065255636909545,
                        "Sharpe": 1.7455973852445321,
                        "AnnualTurnover": 14.290301313023587,
                        "PositiveCAGRWindows": 4,
                        "NegativeCAGRWindows": 0,
                        "Top1PositiveSymbolShare": 0.48,
                        "Top3PositiveSymbolShare": 0.74,
                    }
                ]
            },
        )

        self.assertEqual(report["status"], "READY_FOR_GATEKEEPER_REVIEW")
        self.assertEqual(
            report["source_variant"],
            "tail_release_top25_mid75_pen35_floor25_conccarrykretfmicro_ct70_trim22_gap02_top2",
        )
        self.assertEqual(report["after_fixed_exposure"]["overlay"], "fixed_exposure_065")
        self.assertAlmostEqual(report["after_fixed_exposure"]["estimated_cagr"], 0.4589449893919106)
        self.assertAlmostEqual(report["after_fixed_exposure"]["estimated_mdd"], -0.19924161639912042)
        self.assertEqual(report["after_fixed_exposure"]["gate_result"], "pass_mdd_margin")
        self.assertTrue(report["acceptance_checks"]["source_row_found"])
        self.assertFalse(report["acceptance_checks"]["order_paths_allowed"])
        self.assertTrue(report["acceptance_checks"]["mdd_gate_passed"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertFalse(report["safety"]["private_submit_used"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_missing_source_row_stays_blocked(self) -> None:
        report = reporter.build_report(
            {
                "candidate_id": "stock_aggressive__missing",
                "sizing_overlay": {"recommended_fixed_exposure_cap": 0.65},
            },
            {"ranked_rows": [{"Variant": "other"}]},
        )

        self.assertEqual(report["status"], "SOURCE_ROW_MISSING")
        self.assertEqual(report["source_variant"], "missing")
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertEqual(report["safety"]["real_orders"], 0)


if __name__ == "__main__":
    unittest.main()
