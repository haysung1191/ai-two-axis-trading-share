from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_dependency_relief_packet.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_dependency_relief_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class BithumbCurrentActionableDependencyReliefPacketTests(unittest.TestCase):
    def test_ready_packet_reduces_registered_candidate_dependency_without_permissions(self) -> None:
        packet = builder.build_packet(
            {
                "status": "ROLLOVER_REVIEW_READY",
                "registered_candidate": {"candidate_id": "sweep1354", "estimated_cagr": 0.94, "estimated_mdd": -0.2},
                "latest_oos_candidate": {"candidate_id": "orca1507", "estimated_cagr": 1.39, "estimated_mdd": -0.2},
                "comparison": {"candidate_rollover_detected": True, "registered_vs_latest_cagr_delta": 0.45},
                "safety": {
                    "does_register_shadow_candidate": False,
                    "does_start_shadow_loop": False,
                    "does_enable_paper": False,
                    "does_enable_live": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                    "real_orders": 0,
                },
            },
            {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "candidate_id": "sweep1355",
                "parent_candidate_id": "pola",
                "evidence_summary": {
                    "market": "KRW-POLA",
                    "estimated_cagr": 0.88,
                    "estimated_mdd": -0.2,
                    "robustness_status": "ROBUSTNESS_STRESS_PASS",
                },
                "no_order_assertions": {
                    "promotion_allowed_by_this_packet": False,
                    "shadow_registration_allowed_by_this_packet": False,
                    "paper_enabled_by_this_packet": False,
                    "live_allowed_by_this_packet": False,
                    "broker_submit_allowed_by_this_packet": False,
                    "private_submit_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                },
            },
        )

        self.assertEqual(packet["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertEqual(packet["exact_phrase_to_record"], "REVIEW_DEPENDENCY_RELIEF_EVIDENCE_ONLY")
        self.assertTrue(packet["dependency_relief_summary"]["sweep1354_dependency_reduced_by_review_evidence"])
        self.assertFalse(packet["dependency_relief_summary"]["relief_candidate_is_registered_candidate"])
        self.assertFalse(packet["no_order_assertions"]["shadow_registration_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["broker_submit_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["real_orders_allowed_by_this_packet"])

    def test_blocks_when_relief_candidate_matches_registered(self) -> None:
        packet = builder.build_packet(
            {
                "status": "ROLLOVER_REVIEW_READY",
                "registered_candidate": {"candidate_id": "same"},
                "latest_oos_candidate": {"candidate_id": "latest"},
                "safety": {
                    "does_register_shadow_candidate": False,
                    "does_start_shadow_loop": False,
                    "does_enable_paper": False,
                    "does_enable_live": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                    "real_orders": 0,
                },
            },
            {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "candidate_id": "same",
                "no_order_assertions": {
                    "promotion_allowed_by_this_packet": False,
                    "shadow_registration_allowed_by_this_packet": False,
                    "paper_enabled_by_this_packet": False,
                    "live_allowed_by_this_packet": False,
                    "broker_submit_allowed_by_this_packet": False,
                    "private_submit_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                },
            },
        )

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("dependency_relief_candidate_differs_from_registered", packet["blockers"])


if __name__ == "__main__":
    unittest.main()
