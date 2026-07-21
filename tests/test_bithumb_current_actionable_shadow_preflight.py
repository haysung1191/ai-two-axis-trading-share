from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_shadow_preflight.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_shadow_preflight", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


class BithumbCurrentActionableShadowPreflightTests(unittest.TestCase):
    def test_preflight_remains_blocked_pending_human_gatekeeper_decision(self) -> None:
        report = preflight.build_report(
            {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
                "blockers": [],
                "evidence_summary": {"market": "KRW-POLA", "timeframe": "1d"},
                "no_order_assertions": {
                    "promotion_allowed_by_this_packet": False,
                    "shadow_enabled_by_this_packet": False,
                    "paper_enabled_by_this_packet": False,
                    "live_allowed_by_this_packet": False,
                    "broker_submit_allowed_by_this_packet": False,
                    "private_submit_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                },
            },
            {"status": "PASS"},
            {"shadow_enabled": True, "paper_enabled": False, "live_enabled": False},
        )

        self.assertEqual(report["status"], "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION")
        self.assertIn("HUMAN_GATEKEEPER_SHADOW_DECISION_MISSING", report["blockers"])
        self.assertFalse(report["safety"]["does_register_shadow_candidate"])
        self.assertFalse(report["safety"]["does_start_shadow_loop"])
        self.assertFalse(report["safety"]["does_enable_paper"])
        self.assertFalse(report["safety"]["does_enable_live"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertFalse(report["safety"]["real_orders_allowed"])

    def test_preflight_records_human_approval_without_registering_shadow(self) -> None:
        candidate_id = "bithumb_current_actionable_pola_1d_long_freeze001_sweep3956"
        report = preflight.build_report(
            {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "candidate_id": candidate_id,
                "blockers": [],
                "evidence_summary": {"market": "KRW-POLA", "timeframe": "1d"},
                "no_order_assertions": {
                    "promotion_allowed_by_this_packet": False,
                    "shadow_enabled_by_this_packet": False,
                    "paper_enabled_by_this_packet": False,
                    "live_allowed_by_this_packet": False,
                    "broker_submit_allowed_by_this_packet": False,
                    "private_submit_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                },
            },
            {"status": "PASS"},
            {"shadow_enabled": True, "paper_enabled": False, "live_enabled": False},
            {
                "candidate_id": candidate_id,
                "decision": "APPROVE_SHADOW_REVIEW_ONLY",
                "decided_by": "human_gatekeeper",
                "rationale": "Approved for shadow-review-only registration consideration.",
            },
        )

        self.assertEqual(report["status"], "READY_FOR_SEPARATE_SHADOW_REGISTRATION_REVIEW")
        self.assertEqual(report["blockers"], [])
        self.assertTrue(report["human_decision"]["approved_for_shadow_review_only"])
        self.assertFalse(report["safety"]["does_register_shadow_candidate"])
        self.assertFalse(report["safety"]["does_start_shadow_loop"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertFalse(report["safety"]["real_orders_allowed"])

    def test_preflight_records_source_readiness_blockers(self) -> None:
        report = preflight.build_report(
            {"status": "BLOCKED", "no_order_assertions": {}},
            {"status": "WARN"},
            {"paper_enabled": True, "live_enabled": False},
        )

        self.assertEqual(report["status"], "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION")
        self.assertIn("gatekeeper_review_packet_ready", report["blockers"])
        self.assertIn("risk_guard_pass", report["blockers"])
        self.assertIn("paper_disabled", report["blockers"])


if __name__ == "__main__":
    unittest.main()
