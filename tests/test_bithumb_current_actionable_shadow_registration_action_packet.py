from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_shadow_registration_action_packet.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_shadow_registration_action_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
packet_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_builder)


class BithumbCurrentActionableShadowRegistrationActionPacketTests(unittest.TestCase):
    def test_packet_is_ready_after_human_shadow_review_only_decision_without_side_effects(self) -> None:
        packet = packet_builder.build_packet(
            {
                "status": "READY_FOR_SEPARATE_SHADOW_REGISTRATION_REVIEW",
                "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep3956",
                "evidence_summary": {
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "recommended_exposure_cap": 1.0,
                    "estimated_cagr": 1.16,
                    "estimated_mdd": -0.19,
                    "source_trade_count": 8,
                    "source_profit_factor": 3.05,
                },
            },
            {
                "approved_for_separate_shadow_registration_review": True,
                "human_decision": {
                    "decision_recorded": True,
                    "normalized": {
                        "decision": "APPROVE_SHADOW_REVIEW_ONLY",
                        "decided_by": "human_gatekeeper",
                        "rationale": "reviewed",
                    },
                },
            },
            {"status": "PASS"},
            {"paper_enabled": False, "live_enabled": False},
        )

        self.assertEqual(packet["status"], "READY_FOR_SHADOW_REGISTRATION_ACTION_REVIEW")
        self.assertEqual(packet["blockers"], [])
        self.assertEqual(packet["planned_shadow_registration"]["shadow_gate"], "G07_SHADOW_REVIEW_ONLY")
        self.assertFalse(packet["safety"]["does_register_shadow_candidate"])
        self.assertFalse(packet["safety"]["does_start_shadow_loop"])
        self.assertFalse(packet["safety"]["does_enable_paper"])
        self.assertFalse(packet["safety"]["does_enable_live"])
        self.assertFalse(packet["safety"]["broker_submit_allowed_by_this_packet"])
        self.assertFalse(packet["safety"]["private_submit_allowed_by_this_packet"])
        self.assertFalse(packet["safety"]["real_orders_allowed_by_this_packet"])

    def test_packet_blocks_without_human_decision(self) -> None:
        packet = packet_builder.build_packet(
            {"status": "READY_FOR_SEPARATE_SHADOW_REGISTRATION_REVIEW", "candidate_id": "candidate"},
            {},
            {"status": "PASS"},
            {"paper_enabled": False, "live_enabled": False},
        )

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("HUMAN_SHADOW_REVIEW_ONLY_APPROVAL_NOT_RECORDED", packet["blockers"])
        self.assertIn("VALID_HUMAN_SHADOW_REVIEW_ONLY_DECISION_MISSING", packet["blockers"])

    def test_packet_surfaces_stale_human_decision_candidate_mismatch(self) -> None:
        packet = packet_builder.build_packet(
            {
                "status": "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION",
                "candidate_id": "current_candidate",
                "evidence_summary": {"market": "KRW-POLA", "timeframe": "1d"},
            },
            {
                "candidate_id": "current_candidate",
                "approved_for_separate_shadow_registration_review": False,
                "blockers": ["HUMAN_GATEKEEPER_DECISION_CANDIDATE_MISMATCH"],
                "human_decision": {
                    "decision_recorded": False,
                    "normalized": {
                        "candidate_id": "stale_candidate",
                        "decision": "APPROVE_SHADOW_REVIEW_ONLY",
                        "decided_by": "human_gatekeeper",
                        "rationale": "approved stale candidate",
                    },
                },
            },
            {"status": "PASS"},
            {"paper_enabled": False, "live_enabled": False},
        )

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("HUMAN_GATEKEEPER_DECISION_CANDIDATE_MISMATCH", packet["blockers"])
        self.assertEqual(packet["human_decision_summary"]["expected_candidate_id"], "current_candidate")
        self.assertEqual(packet["human_decision_summary"]["recorded_candidate_id"], "stale_candidate")
        self.assertFalse(packet["safety"]["does_register_shadow_candidate"])
        self.assertFalse(packet["safety"]["does_enable_paper"])
        self.assertFalse(packet["safety"]["does_enable_live"])

    def test_packet_does_not_add_risk_blocker_for_freshness_warn_when_hard_safety_passes(self) -> None:
        packet = packet_builder.build_packet(
            {
                "status": "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION",
                "candidate_id": "current_candidate",
                "evidence_summary": {"market": "KRW-ORCA", "timeframe": "1d"},
            },
            {
                "candidate_id": "current_candidate",
                "approved_for_separate_shadow_registration_review": False,
                "blockers": ["HUMAN_GATEKEEPER_DECISION_CANDIDATE_MISMATCH"],
                "human_decision": {
                    "decision_recorded": False,
                    "normalized": {
                        "candidate_id": "stale_candidate",
                        "decision": "APPROVE_SHADOW_REVIEW_ONLY",
                    },
                },
            },
            {
                "status": "WARN",
                "halt_count": 0,
                "checks": [
                    {"name": "live_disabled", "status": "PASS", "observed": False},
                    {"name": "private_submit_unused", "status": "PASS", "observed": False},
                    {"name": "real_orders_zero", "status": "PASS", "observed": 0},
                    {
                        "name": "broker_submit_scope",
                        "status": "PASS",
                        "observed": {"broker_submit_allowed": True, "broker_submit_scope": "paper_only"},
                    },
                    {"name": "paper_loop", "status": "WARN", "reason": "stale"},
                ],
            },
            {"paper_enabled": False, "live_enabled": False},
        )

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("HUMAN_GATEKEEPER_DECISION_CANDIDATE_MISMATCH", packet["blockers"])
        self.assertNotIn("RISK_GUARD_NOT_PASS", packet["blockers"])
        self.assertEqual(packet["safety"]["risk_guard_status"], "WARN")
        self.assertTrue(packet["safety"]["risk_guard_hard_safety_ok"])
        self.assertFalse(packet["safety"]["broker_submit_allowed_by_this_packet"])
        self.assertFalse(packet["safety"]["real_orders_allowed_by_this_packet"])

    def test_packet_blocks_when_risk_guard_hard_safety_fails(self) -> None:
        packet = packet_builder.build_packet(
            {"status": "READY_FOR_SEPARATE_SHADOW_REGISTRATION_REVIEW", "candidate_id": "candidate"},
            {
                "approved_for_separate_shadow_registration_review": True,
                "human_decision": {
                    "decision_recorded": True,
                    "normalized": {"decision": "APPROVE_SHADOW_REVIEW_ONLY"},
                },
            },
            {
                "status": "WARN",
                "halt_count": 0,
                "checks": [
                    {"name": "live_disabled", "status": "FAIL", "observed": True},
                    {"name": "private_submit_unused", "status": "PASS", "observed": False},
                    {"name": "real_orders_zero", "status": "PASS", "observed": 0},
                    {
                        "name": "broker_submit_scope",
                        "status": "PASS",
                        "observed": {"broker_submit_allowed": True, "broker_submit_scope": "paper_only"},
                    },
                ],
            },
            {"paper_enabled": False, "live_enabled": False},
        )

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("RISK_GUARD_NOT_PASS", packet["blockers"])
        self.assertFalse(packet["safety"]["risk_guard_hard_safety_ok"])


if __name__ == "__main__":
    unittest.main()
