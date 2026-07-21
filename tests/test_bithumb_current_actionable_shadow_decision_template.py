from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_shadow_decision_template.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_shadow_decision_template", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
decision_template = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(decision_template)


class BithumbCurrentActionableShadowDecisionTemplateTests(unittest.TestCase):
    def test_missing_human_decision_keeps_pending_without_side_effects(self) -> None:
        report = decision_template.build_report(
            {
                "status": "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION",
                "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
                "evidence_summary": {
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "recommended_exposure_cap": 0.53,
                    "estimated_cagr": 0.21,
                    "estimated_mdd": -0.20,
                },
            },
            {},
            False,
        )

        self.assertEqual(report["status"], "PENDING_HUMAN_GATEKEEPER_DECISION")
        self.assertIn("HUMAN_GATEKEEPER_SHADOW_DECISION_MISSING", report["blockers"])
        self.assertFalse(report["human_decision"]["decision_recorded"])
        self.assertFalse(report["approved_for_separate_shadow_registration_review"])
        self.assertFalse(report["safety"]["does_register_shadow_candidate"])
        self.assertFalse(report["safety"]["does_start_shadow_loop"])
        self.assertFalse(report["safety"]["does_enable_paper"])
        self.assertFalse(report["safety"]["does_enable_live"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertFalse(report["safety"]["private_submit_allowed"])
        self.assertFalse(report["safety"]["real_orders_allowed"])

    def test_valid_approval_records_decision_but_still_does_not_register_shadow(self) -> None:
        report = decision_template.build_report(
            {
                "status": "READY_FOR_SEPARATE_SHADOW_REGISTRATION_REVIEW",
                "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
            },
            {
                "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
                "decision": "APPROVE_SHADOW_REVIEW_ONLY",
                "decided_by": "human_gatekeeper",
                "rationale": "Approved for a separate shadow-registration review.",
            },
            True,
        )

        self.assertEqual(report["status"], "HUMAN_GATEKEEPER_SHADOW_DECISION_RECORDED")
        self.assertEqual(report["blocker_count"], 0)
        self.assertTrue(report["human_decision"]["decision_recorded"])
        self.assertTrue(report["approved_for_separate_shadow_registration_review"])
        self.assertFalse(report["safety"]["does_register_shadow_candidate"])
        self.assertFalse(report["safety"]["does_start_shadow_loop"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertFalse(report["safety"]["real_orders_allowed"])

    def test_valid_approval_is_not_registration_approved_when_preflight_blocks(self) -> None:
        report = decision_template.build_report(
            {
                "status": "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION",
                "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
                "blockers": ["gatekeeper_review_packet_ready"],
            },
            {
                "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
                "decision": "APPROVE_SHADOW_REVIEW_ONLY",
                "decided_by": "human_gatekeeper",
                "rationale": "Approved before later evidence blocked the preflight.",
            },
            True,
        )

        self.assertEqual(report["status"], "HUMAN_GATEKEEPER_DECISION_RECORDED_BUT_PREFLIGHT_BLOCKED")
        self.assertIn("SHADOW_PREFLIGHT_NOT_READY_FOR_REGISTRATION_REVIEW", report["blockers"])
        self.assertTrue(report["human_decision"]["decision_recorded"])
        self.assertFalse(report["approved_for_separate_shadow_registration_review"])
        self.assertFalse(report["safety"]["does_register_shadow_candidate"])
        self.assertFalse(report["safety"]["does_start_shadow_loop"])

    def test_invalid_decision_is_blocked(self) -> None:
        report = decision_template.build_report(
            {
                "status": "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION",
                "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
            },
            {
                "candidate_id": "other",
                "decision": "APPROVE_LIVE",
                "decided_by": "",
                "rationale": "",
            },
            True,
        )

        self.assertEqual(report["status"], "INVALID_HUMAN_GATEKEEPER_DECISION")
        self.assertIn("HUMAN_GATEKEEPER_DECISION_CANDIDATE_MISMATCH", report["blockers"])
        self.assertIn("HUMAN_GATEKEEPER_DECISION_NOT_ALLOWED", report["blockers"])
        self.assertFalse(report["human_decision"]["decision_recorded"])
        self.assertFalse(report["approved_for_separate_shadow_registration_review"])


if __name__ == "__main__":
    unittest.main()
