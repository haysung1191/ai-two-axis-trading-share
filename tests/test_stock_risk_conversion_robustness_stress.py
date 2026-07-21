from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_risk_conversion_robustness_stress.py")
SPEC = importlib.util.spec_from_file_location("build_stock_risk_conversion_robustness_stress", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
stress = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stress)


class StockRiskConversionRobustnessStressTests(unittest.TestCase):
    def test_ready_report_is_review_only_and_no_order(self) -> None:
        original_read_json = stress.read_json
        try:
            def fake_read_json(path, _default):
                if path == stress.RISK_CONVERSION_QUEUE:
                    return {
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "target_count": 5,
                        "ready_candidate_count": 5,
                        "queue": [
                            {
                                "candidate_id": f"stock_aggressive_trim{i}",
                                "lane": "kis_etfs",
                                "before": {"negative_cagr_windows": 0, "sharpe": 1.7},
                                "proposed_conversion": {
                                    "overlay": "fixed_exposure_065",
                                    "fixed_exposure_cap": 0.65,
                                    "estimated_cagr": 0.459,
                                    "estimated_mdd": -0.199,
                                    "estimated_return_retention": 0.65,
                                    "gate_result": "pass_mdd_margin",
                                },
                                "order_paths_allowed": False,
                                "broker_submit_allowed": False,
                                "live_enabled": False,
                                "private_submit_allowed": False,
                                "real_orders_allowed": False,
                            }
                            for i in range(5)
                        ],
                    }
                return {
                    "status": "READY_FOR_GATEKEEPER_REVIEW",
                    "candidate_id": "stock_aggressive_trim22",
                    "source_variant": "trim22",
                    "before": {"negative_cagr_windows": 0},
                    "after_fixed_exposure": {
                        "overlay": "fixed_exposure_065",
                        "fixed_exposure_cap": 0.65,
                        "estimated_cagr": 0.459,
                        "estimated_mdd": -0.199,
                        "estimated_sharpe": 1.74,
                        "estimated_return_retention": 0.65,
                        "gate_result": "pass_mdd_margin",
                    },
                    "safety": {
                        "live_enabled": False,
                        "broker_submit_allowed": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                        "order_paths_allowed": False,
                    },
                }
            stress.read_json = fake_read_json
            report = stress.build_report()
        finally:
            stress.read_json = original_read_json

        self.assertEqual(report["status"], "ROBUSTNESS_STRESS_PASS")
        self.assertEqual(report["case_count"], len(stress.STRESS_CASES))
        self.assertGreaterEqual(report["pass_count"], stress.MIN_PASS_CASES)
        self.assertEqual(report["queue_coverage"]["covered_candidate_count"], 5)
        self.assertEqual(report["queue_coverage"]["stress_pass_candidate_count"], 5)
        self.assertTrue(report["queue_coverage"]["top5_full_coverage"])
        self.assertEqual(len(report["candidate_results"]), 5)
        self.assertFalse(report["no_order_assertions"]["promotion_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["paper_enabled_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["private_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_unsafe_candidate_evidence(self) -> None:
        original_read_json = stress.read_json
        try:
            stress.read_json = lambda _path, _default: {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "candidate_id": "stock_aggressive_trim22",
                "after_fixed_exposure": {"gate_result": "pass_mdd_margin"},
                "safety": {
                    "live_enabled": False,
                    "broker_submit_allowed": True,
                    "private_submit_used": False,
                    "real_orders": 0,
                    "order_paths_allowed": False,
                },
            }
            report = stress.build_report()
        finally:
            stress.read_json = original_read_json

        self.assertEqual(report["status"], "BLOCKED_UNSAFE_CANDIDATE_EVIDENCE")
        self.assertIn("CANDIDATE_EVIDENCE_ORDER_PATH_NOT_SAFE", report["blockers"])


if __name__ == "__main__":
    unittest.main()
