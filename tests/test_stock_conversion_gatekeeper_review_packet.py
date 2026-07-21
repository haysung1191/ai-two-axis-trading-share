from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_conversion_gatekeeper_review_packet.py")
SPEC = importlib.util.spec_from_file_location("build_stock_conversion_gatekeeper_review_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
packet_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_builder)


class StockConversionGatekeeperReviewPacketTests(unittest.TestCase):
    def test_ready_packet_is_review_only_and_no_order(self) -> None:
        packet = packet_builder.build_packet(
            {
                "status": "READY_FOR_CONVERSION_BACKTEST",
                "candidate_id": "stock_aggressive_trim22",
                "before": {"cagr": 0.706, "mdd": -0.306, "sharpe": 1.74, "failure_reason": "MDD_TOO_HIGH"},
                "sizing_overlay": {"recommended_fixed_exposure_cap": 0.65},
            },
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "candidate_id": "stock_aggressive_trim22",
                "after_fixed_exposure": {
                    "overlay": "fixed_exposure_065",
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
                },
            },
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "spec_requested_overlay": "fixed_exposure_065",
                "candidate_specific_evidence_ready": True,
            },
            {
                "status": "ROBUSTNESS_STRESS_PASS",
                "candidate_id": "stock_aggressive_trim22",
                "case_count": 7,
                "pass_count": 5,
                "mdd_stress_pass_count": 1,
                "queue_coverage": {
                    "covered_candidate_count": 5,
                    "stress_pass_candidate_count": 5,
                    "all_covered_candidates_safe": True,
                    "top5_full_coverage": True,
                },
                "candidate_results": [
                    {
                        "candidate_id": f"stock_aggressive_trim{i}",
                        "lane": "kis_etfs",
                        "status": "ROBUSTNESS_STRESS_PASS",
                        "case_count": 7,
                        "pass_count": 5,
                        "mdd_stress_pass_count": 1,
                        "queue_order_paths_safe": True,
                    }
                    for i in range(5)
                ],
            },
            {
                "status": "SIZING_REPAIR_READY",
                "evaluated_iterate_candidate_count": 2,
                "repair_ready_count": 2,
                "repairs": [
                    {
                        "candidate_id": "stock_aggressive_trim_repair",
                        "lane": "kis_stocks",
                        "repair_status": "SIZING_REPAIR_READY",
                        "current_fixed_exposure_cap": 0.59,
                        "recommended_conversion": {
                            "overlay": "fixed_exposure_055",
                            "fixed_exposure_cap": 0.55,
                            "stress": {"pass_count": 4},
                        },
                    }
                ],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            {
                "status": "REPAIRED_ROBUSTNESS_STRESS_PASS",
                "queue_coverage": {
                    "covered_candidate_count": 5,
                    "stress_pass_candidate_count": 5,
                    "repaired_candidate_count": 2,
                    "all_covered_candidates_safe": True,
                    "top5_full_coverage": True,
                },
                "candidate_results": [
                    {
                        "candidate_id": "stock_aggressive_trim_repair",
                        "lane": "kis_stocks",
                        "status": "ROBUSTNESS_STRESS_PASS",
                        "overlay": "fixed_exposure_055",
                        "fixed_exposure_cap": 0.55,
                        "pass_count": 4,
                        "mdd_stress_pass_count": 2,
                        "repair_applied": True,
                        "queue_order_paths_safe": True,
                    }
                ],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            {
                "gatekeeper_action_packet": {
                    "candidate_specific_conversion_evidence": {"ready_for_gatekeeper_review": True}
                }
            },
            {"status": "WARN", "halt_count": 0},
        )

        self.assertEqual(packet["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertEqual(packet["blockers"], [])
        self.assertTrue(packet["readiness_checks"]["robustness_top5_queue_coverage_present"])
        self.assertEqual(packet["robustness_stress"]["queue_coverage"]["covered_candidate_count"], 5)
        self.assertEqual(len(packet["robustness_stress"]["candidate_results"]), 5)
        self.assertEqual(packet["sizing_repair"]["repair_ready_count"], 2)
        self.assertEqual(packet["sizing_repair"]["repairs"][0]["recommended_overlay"], "fixed_exposure_055")
        self.assertTrue(packet["readiness_checks"]["repaired_robustness_top5_pass"])
        self.assertEqual(packet["repaired_robustness"]["queue_coverage"]["stress_pass_candidate_count"], 5)
        self.assertEqual(packet["repaired_robustness"]["candidate_results"][0]["repair_applied"], True)
        self.assertFalse(packet["no_order_assertions"]["promotion_allowed_by_this_report"])
        self.assertFalse(packet["no_order_assertions"]["paper_enabled_by_this_report"])
        self.assertFalse(packet["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(packet["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(packet["no_order_assertions"]["private_submit_allowed_by_this_report"])
        self.assertFalse(packet["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_packet_blocks_unsafe_candidate_evidence(self) -> None:
        packet = packet_builder.build_packet(
            {"status": "READY_FOR_CONVERSION_BACKTEST", "candidate_id": "stock_aggressive_trim22"},
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "candidate_id": "stock_aggressive_trim22",
                "after_fixed_exposure": {"overlay": "fixed_exposure_065", "gate_result": "pass_mdd_margin"},
                "safety": {"live_enabled": False, "broker_submit_allowed": True, "private_submit_used": False, "real_orders": 0},
            },
            {"status": "READY_FOR_GATEKEEPER_REVIEW", "spec_requested_overlay": "fixed_exposure_065", "candidate_specific_evidence_ready": True},
            {
                "status": "ROBUSTNESS_STRESS_PASS",
                "candidate_id": "stock_aggressive_trim22",
                "queue_coverage": {
                    "covered_candidate_count": 5,
                    "all_covered_candidates_safe": True,
                    "top5_full_coverage": True,
                },
            },
            {},
            {},
            {"gatekeeper_action_packet": {"candidate_specific_conversion_evidence": {"ready_for_gatekeeper_review": True}}},
            {"status": "PASS"},
        )

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("CANDIDATE_EVIDENCE_ORDER_PATH_NOT_SAFE", packet["blockers"])


if __name__ == "__main__":
    unittest.main()
