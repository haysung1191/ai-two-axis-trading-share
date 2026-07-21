from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_family_parameter_repair_gatekeeper_packet.py")
SPEC = importlib.util.spec_from_file_location(
    "build_bithumb_current_actionable_family_parameter_repair_gatekeeper_packet",
    MODULE_PATH,
)
assert SPEC is not None
assert SPEC.loader is not None
packet_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_builder)


SAFE_REPAIR_ASSERTIONS = {
    "promotion_allowed_by_this_report": False,
    "paper_enabled_by_this_report": False,
    "live_allowed_by_this_report": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders_allowed_by_this_report": False,
}


class BithumbFamilyParameterRepairGatekeeperPacketTests(unittest.TestCase):
    def test_builds_review_ready_packet_without_order_permissions(self) -> None:
        repair = {
            "status": "FAMILY_PARAMETER_REPAIR_ROBUSTNESS_PASS",
            "seed_candidate_count": 2,
            "evaluated_trial_count": 10,
            "oos_pass_candidate_count": 3,
            "robustness_pass_candidate_count": 1,
            "no_order_assertions": SAFE_REPAIR_ASSERTIONS,
            "candidate_results": [
                {
                    "candidate_id": "pola_sweep1355",
                    "parent_candidate_id": "pola",
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "status": "OOS_CANDIDATE_PASS",
                    "parameters": {"lookback_bars": 3},
                    "source_conversion": {
                        "recommended_exposure_cap": 0.8,
                        "estimated_cagr": 1.0,
                        "estimated_mdd": -0.2,
                        "source_trade_count": 17,
                        "source_profit_factor": 2.5,
                    },
                    "aggregate": {
                        "fold_count": 3,
                        "pass_fold_count": 2,
                        "positive_fold_count": 2,
                        "worst_fold_mdd": -0.15,
                        "average_fold_cagr": 4.0,
                        "total_trade_count": 17,
                    },
                    "robustness": {
                        "status": "ROBUSTNESS_STRESS_PASS",
                        "case_count": 7,
                        "pass_count": 4,
                        "cost_pass_count": 2,
                    },
                }
            ],
        }

        packet = packet_builder.build_packet(repair, {"status": "PASS", "halt_count": 0})

        self.assertEqual(packet["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertEqual(packet["candidate_id"], "pola_sweep1355")
        self.assertEqual(packet["recommended_decision"], "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY")
        self.assertEqual(packet["exact_phrase_to_record"], "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY")
        self.assertIn("does not approve promotion", packet["review_only_effect"])
        self.assertIn("REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY", packet["gatekeeper_instruction"])
        self.assertEqual(packet["evidence_summary"]["oos_pass_fold_count"], 2)
        self.assertEqual(packet["evidence_summary"]["robustness_pass_count"], 4)
        self.assertFalse(packet["no_order_assertions"]["shadow_registration_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["broker_submit_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["real_orders_allowed_by_this_packet"])

    def test_allows_freshness_warn_when_hard_safety_passes(self) -> None:
        repair = {
            "status": "FAMILY_PARAMETER_REPAIR_ROBUSTNESS_PASS",
            "no_order_assertions": SAFE_REPAIR_ASSERTIONS,
            "candidate_results": [
                {
                    "candidate_id": "pola_sweep1355",
                    "status": "OOS_CANDIDATE_PASS",
                    "robustness": {"status": "ROBUSTNESS_STRESS_PASS"},
                }
            ],
        }

        packet = packet_builder.build_packet(
            repair,
            {
                "status": "WARN",
                "halt_count": 0,
                "checks": [
                    {"name": "live_disabled", "status": "PASS"},
                    {"name": "private_submit_unused", "status": "PASS"},
                    {"name": "real_orders_zero", "status": "PASS"},
                    {"name": "broker_submit_scope", "status": "PASS"},
                    {"name": "latest_run", "status": "WARN"},
                ],
            },
        )

        self.assertEqual(packet["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertTrue(packet["readiness_checks"]["risk_guard_hard_safety_pass"])
        self.assertEqual(packet["blockers"], [])

    def test_blocks_if_risk_guard_hard_safety_not_pass(self) -> None:
        repair = {
            "status": "FAMILY_PARAMETER_REPAIR_ROBUSTNESS_PASS",
            "no_order_assertions": SAFE_REPAIR_ASSERTIONS,
            "candidate_results": [
                {
                    "candidate_id": "pola_sweep1355",
                    "status": "OOS_CANDIDATE_PASS",
                    "robustness": {"status": "ROBUSTNESS_STRESS_PASS"},
                }
            ],
        }

        packet = packet_builder.build_packet(repair, {"status": "WARN"})

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("risk_guard_hard_safety_pass", packet["blockers"])
        self.assertFalse(packet["no_order_assertions"]["live_allowed_by_this_packet"])


if __name__ == "__main__":
    unittest.main()
