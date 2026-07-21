from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_risk_conversion_sizing_repair_report.py")
SPEC = importlib.util.spec_from_file_location("build_stock_risk_conversion_sizing_repair_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
repair = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repair)


class StockRiskConversionSizingRepairReportTests(unittest.TestCase):
    def test_iterate_candidate_gets_sizing_only_repair_without_order_paths(self) -> None:
        report = repair.build_report(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "queue": [
                    {
                        "candidate_id": "stock_aggressive__switchcarry",
                        "lane": "kis_stocks",
                        "before": {"cagr": 0.76, "mdd": -0.338, "sharpe": 1.7},
                        "proposed_conversion": {
                            "overlay": "fixed_exposure_059",
                            "fixed_exposure_cap": 0.59,
                        },
                        "order_paths_allowed": False,
                        "broker_submit_allowed": False,
                        "live_enabled": False,
                        "private_submit_allowed": False,
                        "real_orders_allowed": False,
                    }
                ],
            },
            {
                "status": "ROBUSTNESS_STRESS_PASS",
                "candidate_results": [
                    {
                        "candidate_id": "stock_aggressive__switchcarry",
                        "status": "ROBUSTNESS_STRESS_ITERATE",
                        "pass_count": 2,
                        "mdd_stress_pass_count": 1,
                    }
                ],
            },
        )

        self.assertEqual(report["status"], "SIZING_REPAIR_READY")
        self.assertEqual(report["repair_ready_count"], 1)
        row = report["repairs"][0]
        self.assertEqual(row["repair_status"], "SIZING_REPAIR_READY")
        self.assertEqual(row["recommended_conversion"]["overlay"], "fixed_exposure_055")
        self.assertEqual(row["recommended_conversion"]["stress"]["pass_count"], 4)
        self.assertFalse(row["broker_submit_allowed"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_unsafe_source_queue(self) -> None:
        report = repair.build_report(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "queue": [
                    {
                        "candidate_id": "stock_aggressive__unsafe",
                        "before": {"cagr": 0.76, "mdd": -0.338},
                        "proposed_conversion": {"fixed_exposure_cap": 0.59},
                        "order_paths_allowed": False,
                        "broker_submit_allowed": True,
                        "live_enabled": False,
                        "private_submit_allowed": False,
                        "real_orders_allowed": False,
                    }
                ],
            },
            {
                "status": "ROBUSTNESS_STRESS_PASS",
                "candidate_results": [
                    {"candidate_id": "stock_aggressive__unsafe", "status": "ROBUSTNESS_STRESS_ITERATE"}
                ],
            },
        )

        self.assertEqual(report["status"], "NO_REPAIR_READY")
        self.assertIn("UNSAFE_ORDER_PATH_IN_SOURCE_QUEUE", report["blockers"])


if __name__ == "__main__":
    unittest.main()
