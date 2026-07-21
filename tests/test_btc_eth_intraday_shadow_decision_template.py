from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_shadow_decision_template.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_shadow_decision_template", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
decision_template = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(decision_template)


class BtcEthIntradayShadowDecisionTemplateTests(unittest.TestCase):
    def test_missing_human_decision_keeps_pending_without_side_effects(self) -> None:
        report = decision_template.build_report(
            {
                "status": "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION",
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "evidence_summary": {
                    "market": "KRW-BTC",
                    "timeframe": "4h",
                    "recommended_exposure_cap": 0.75,
                    "estimated_average_fold_cagr": 0.06,
                    "estimated_worst_fold_mdd": -0.12,
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
                "status": "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION",
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            },
            {
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
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

    def test_invalid_decision_is_blocked(self) -> None:
        report = decision_template.build_report(
            {
                "status": "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION",
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
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
