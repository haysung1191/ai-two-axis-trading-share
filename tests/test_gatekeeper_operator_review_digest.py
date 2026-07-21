from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_gatekeeper_operator_review_digest.py")
SPEC = importlib.util.spec_from_file_location("build_gatekeeper_operator_review_digest", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
digest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(digest)


class GatekeeperOperatorReviewDigestTests(unittest.TestCase):
    def priority_packet(self) -> dict:
        return {
            "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
            "ready_decision_count": 2,
            "ready_decisions": [
                {
                    "decision_id": "paper_smoke_review",
                    "candidate_id": "small_account_growth_paper",
                    "lane": "portfolio",
                    "priority_score": 100,
                    "exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                    "review_only_effect": "review only",
                    "blockers": [],
                }
            ],
        }

    def compression_packet(self) -> dict:
        return {
            "status": "PASS",
            "estimated_review_rows_after_compression": 1,
            "compression_group_count": 1,
        }

    def dashboard_packet(self) -> dict:
        return {
            "safety": {
                "live_enabled": False,
                "real_orders": 0,
                "private_submit_used": False,
                "broker_submit_scope": "paper_only",
            }
        }

    def monitor_packet(self) -> dict:
        return {"status": "WARN", "blockers": [], "actionable_warnings": []}

    def test_builds_safe_operator_digest(self) -> None:
        report = digest.build_report(
            self.priority_packet(),
            self.compression_packet(),
            self.dashboard_packet(),
            self.monitor_packet(),
        )

        self.assertEqual(report["status"], "READY_FOR_OPERATOR_REVIEW")
        self.assertEqual(report["top_action_count"], 1)
        self.assertTrue(report["hard_safety"]["ok"])
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_when_live_flag_is_enabled(self) -> None:
        dashboard = self.dashboard_packet()
        dashboard["safety"]["live_enabled"] = True

        report = digest.build_report(
            self.priority_packet(),
            self.compression_packet(),
            dashboard,
            self.monitor_packet(),
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("HARD_SAFETY_FLAGS_NOT_OK", report["blockers"])

    def test_does_not_block_on_prior_monitor_self_reference(self) -> None:
        monitor = {
            "status": "HALT_RECOMMENDED",
            "blockers": ["MISSING_REPORT"],
            "actionable_warnings": ["NON_PASS_STATUS:gatekeeper_operator_review_digest:BLOCKED"],
        }

        report = digest.build_report(
            self.priority_packet(),
            self.compression_packet(),
            self.dashboard_packet(),
            monitor,
        )

        self.assertEqual(report["status"], "READY_FOR_OPERATOR_REVIEW")
        self.assertEqual(report["operational_monitor"]["blocker_count"], 1)


if __name__ == "__main__":
    unittest.main()
