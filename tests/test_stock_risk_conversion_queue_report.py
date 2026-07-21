from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_risk_conversion_queue_report.py")
SPEC = importlib.util.spec_from_file_location("build_stock_risk_conversion_queue_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
queue = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(queue)


class StockRiskConversionQueueReportTests(unittest.TestCase):
    def test_queue_ranks_ready_stock_aggressive_targets_without_order_paths(self) -> None:
        report = queue.build_report(
            {
                "gatekeeper_action_packet": {
                    "risk_conversion_targets": [
                        {
                            "candidate_id": "stock_aggressive__b",
                            "lane": "kis_stocks",
                            "status": "SHADOW_READY",
                            "cagr": 0.70,
                            "mdd": -0.31,
                            "sharpe": 1.7,
                            "fixed_exposure_recipe": {
                                "recommended_fixed_exposure_cap": 0.65,
                                "estimated_capped_cagr": 0.455,
                                "estimated_capped_mdd": -0.199,
                                "estimated_return_retention": 0.65,
                            },
                        },
                        {
                            "candidate_id": "stock_aggressive__a",
                            "lane": "kis_etfs",
                            "status": "SHADOW_READY",
                            "cagr": 0.72,
                            "mdd": -0.31,
                            "sharpe": 1.7,
                            "fixed_exposure_recipe": {
                                "recommended_fixed_exposure_cap": 0.64,
                                "estimated_capped_cagr": 0.461,
                                "estimated_capped_mdd": -0.198,
                                "estimated_return_retention": 0.64,
                            },
                        },
                    ]
                }
            },
            {"status": "PASS"},
        )

        self.assertEqual(report["status"], "READY_FOR_GATEKEEPER_REVIEW")
        self.assertEqual(report["target_count"], 2)
        self.assertEqual(report["ready_candidate_count"], 2)
        self.assertEqual(report["queue"][0]["candidate_id"], "stock_aggressive__a")
        self.assertFalse(report["no_order_assertions"]["promotion_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["queue"][0]["order_paths_allowed"])
        self.assertFalse(report["queue"][0]["live_enabled"])
        self.assertEqual(report["queue"][0]["proposed_conversion"]["gate_result"], "pass_mdd_margin")

    def test_queue_allows_warn_risk_guard_when_no_halts(self) -> None:
        report = queue.build_report(
            {
                "gatekeeper_action_packet": {
                    "risk_conversion_targets": [
                        {
                            "candidate_id": "stock_aggressive__a",
                            "fixed_exposure_recipe": {
                                "recommended_fixed_exposure_cap": 0.64,
                                "estimated_capped_cagr": 0.461,
                                "estimated_capped_mdd": -0.198,
                                "estimated_return_retention": 0.64,
                            },
                        }
                    ]
                }
            },
            {"status": "WARN", "halt_count": 0},
        )

        self.assertEqual(report["status"], "READY_FOR_GATEKEEPER_REVIEW")
        self.assertEqual(report["blockers"], [])
        self.assertTrue(report["risk_guard_allows_review"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])

    def test_queue_blocks_when_risk_guard_has_halt(self) -> None:
        report = queue.build_report(
            {"gatekeeper_action_packet": {"risk_conversion_targets": [{"candidate_id": "stock_aggressive__a"}]}},
            {"status": "WARN", "halt_count": 1},
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("RISK_GUARD_BLOCKS_REVIEW", report["blockers"])


if __name__ == "__main__":
    unittest.main()
