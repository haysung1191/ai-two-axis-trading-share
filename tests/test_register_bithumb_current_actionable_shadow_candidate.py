from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\register_bithumb_current_actionable_shadow_candidate.py")
SPEC = importlib.util.spec_from_file_location("register_bithumb_current_actionable_shadow_candidate", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
registration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(registration)


def ready_packet() -> dict:
    candidate_id = "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354"
    return {
        "status": "READY_FOR_SHADOW_REGISTRATION_ACTION_REVIEW",
        "candidate_id": candidate_id,
        "lane": "bithumb_1d",
        "planned_shadow_registration": {
            "candidate_id": candidate_id,
            "market": "KRW-POLA",
            "timeframe": "1d",
            "shadow_gate": "G07_SHADOW_REVIEW_ONLY",
            "recommended_exposure_cap": 0.86,
            "estimated_cagr": 0.94,
            "estimated_mdd": -0.2,
            "source_trade_count": 17,
            "source_profit_factor": 2.39,
        },
        "human_decision_summary": {
            "decision_recorded": True,
            "decision": "APPROVE_SHADOW_REVIEW_ONLY",
            "expected_candidate_id": candidate_id,
            "recorded_candidate_id": candidate_id,
            "decided_by": "human_gatekeeper",
            "rationale": "reviewed",
        },
        "blockers": [],
        "safety": {
            "does_register_shadow_candidate": False,
            "does_start_shadow_loop": False,
            "does_enable_paper": False,
            "does_enable_live": False,
            "broker_submit_allowed_by_this_packet": False,
            "private_submit_allowed_by_this_packet": False,
            "real_orders_allowed_by_this_packet": False,
            "real_orders": 0,
        },
    }


class BithumbCurrentActionableShadowCandidateRegistrationTests(unittest.TestCase):
    def test_ready_packet_builds_file_only_shadow_registration(self) -> None:
        report = registration.build_registration(ready_packet(), {"records": []})

        self.assertEqual(report["status"], "REGISTERED")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["record"]["mode"], "shadow_review_only")
        self.assertEqual(report["record"]["market"], "KRW-POLA")
        self.assertFalse(report["safety"]["does_start_shadow_loop"])
        self.assertFalse(report["safety"]["does_emit_order_signal"])
        self.assertFalse(report["safety"]["does_enable_paper"])
        self.assertFalse(report["safety"]["does_enable_live"])
        self.assertFalse(report["safety"]["broker_submit_allowed_by_this_report"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_stale_or_unsafe_packet_blocks_registration(self) -> None:
        packet = ready_packet()
        packet["human_decision_summary"]["recorded_candidate_id"] = "stale_candidate"
        packet["safety"]["does_start_shadow_loop"] = True

        report = registration.build_registration(packet, {"records": []})

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("ACTION_PACKET_SAFETY_NOT_CLEAN", report["blockers"])
        self.assertIn("HUMAN_DECISION_CANDIDATE_MISMATCH", report["blockers"])
        self.assertFalse(report["safety"]["does_start_shadow_loop"])
        self.assertFalse(report["safety"]["does_enable_live"])

    def test_registry_update_is_idempotent_by_candidate_id(self) -> None:
        packet = ready_packet()
        previous = {"records": [{"candidate_id": packet["candidate_id"], "old": True}]}
        report = registration.build_registration(packet, previous)
        registry = registration.update_registry(report, previous)

        self.assertEqual(registry["registered_count"], 1)
        self.assertFalse(registry["records"][0].get("old", False))
        self.assertEqual(registry["records"][0]["candidate_id"], packet["candidate_id"])


if __name__ == "__main__":
    unittest.main()
