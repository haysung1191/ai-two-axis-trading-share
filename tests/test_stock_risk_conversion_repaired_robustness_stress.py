from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_risk_conversion_repaired_robustness_stress.py")
SPEC = importlib.util.spec_from_file_location("build_stock_risk_conversion_repaired_robustness_stress", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class StockRiskConversionRepairedRobustnessStressTests(unittest.TestCase):
    def test_repair_applies_to_iterate_candidates_and_keeps_no_order_safety(self) -> None:
        queue = {
            "status": "READY_FOR_GATEKEEPER_REVIEW",
            "target_count": 5,
            "ready_candidate_count": 5,
            "queue": [
                {
                    "candidate_id": f"candidate_{idx}",
                    "order_paths_allowed": False,
                    "broker_submit_allowed": False,
                    "live_enabled": False,
                    "private_submit_allowed": False,
                    "real_orders_allowed": False,
                }
                for idx in range(5)
            ],
        }
        robustness = {
            "status": "ROBUSTNESS_STRESS_PASS",
            "candidate_results": [
                {
                    "candidate_id": f"candidate_{idx}",
                    "lane": "kis_stocks",
                    "status": "ROBUSTNESS_STRESS_PASS" if idx < 3 else "ROBUSTNESS_STRESS_ITERATE",
                    "pass_count": 4 if idx < 3 else 2,
                    "mdd_stress_pass_count": 1,
                    "queue_order_paths_safe": True,
                }
                for idx in range(5)
            ],
        }
        sizing_repair = {
            "status": "SIZING_REPAIR_READY",
            "repairs": [
                {
                    "candidate_id": "candidate_3",
                    "repair_status": "SIZING_REPAIR_READY",
                    "recommended_conversion": {
                        "overlay": "fixed_exposure_055",
                        "fixed_exposure_cap": 0.55,
                        "stress": {"status": "ROBUSTNESS_STRESS_PASS", "case_count": 7, "pass_count": 4, "mdd_stress_pass_count": 2},
                    },
                },
                {
                    "candidate_id": "candidate_4",
                    "repair_status": "SIZING_REPAIR_READY",
                    "recommended_conversion": {
                        "overlay": "fixed_exposure_055",
                        "fixed_exposure_cap": 0.55,
                        "stress": {"status": "ROBUSTNESS_STRESS_PASS", "case_count": 7, "pass_count": 4, "mdd_stress_pass_count": 2},
                    },
                },
            ],
        }

        report = builder.build_report(queue, robustness, sizing_repair)

        self.assertEqual(report["status"], "REPAIRED_ROBUSTNESS_STRESS_PASS")
        self.assertEqual(report["queue_coverage"]["stress_pass_candidate_count"], 5)
        self.assertEqual(report["queue_coverage"]["repaired_candidate_count"], 2)
        self.assertEqual(report["blockers"], [])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])
        self.assertTrue(report["candidate_results"][3]["repair_applied"])

    def test_blocks_unsafe_queue(self) -> None:
        report = builder.build_report(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "queue": [
                    {
                        "candidate_id": "unsafe",
                        "order_paths_allowed": False,
                        "broker_submit_allowed": True,
                        "live_enabled": False,
                        "private_submit_allowed": False,
                        "real_orders_allowed": False,
                    }
                ],
            },
            {"status": "ROBUSTNESS_STRESS_PASS", "candidate_results": [{"candidate_id": "unsafe", "status": "ROBUSTNESS_STRESS_PASS", "queue_order_paths_safe": True}]},
            {"status": "SIZING_REPAIR_READY", "repairs": []},
        )

        self.assertEqual(report["status"], "REPAIRED_ROBUSTNESS_STRESS_ITERATE")
        self.assertIn("QUEUE_ORDER_PATH_NOT_SAFE", report["blockers"])


if __name__ == "__main__":
    unittest.main()
