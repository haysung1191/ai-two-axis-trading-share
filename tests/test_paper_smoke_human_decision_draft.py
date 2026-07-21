from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_paper_smoke_human_decision_draft.py")
SPEC = importlib.util.spec_from_file_location("build_paper_smoke_human_decision_draft", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
draft = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(draft)


class PaperSmokeHumanDecisionDraftTests(unittest.TestCase):
    def test_builds_acknowledgement_draft_without_paper_live_or_orders(self) -> None:
        report = draft.build_draft(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "review_ready": True,
                "blockers": [],
                "candidate_profile": "small_account_growth_paper",
                "evidence_summary": {
                    "paper_cycles_completed": 252,
                    "combined_non_flat_signal_count": 53,
                    "combined_executable_order_evidence_count": 53,
                    "extended_paper_ready": False,
                    "historical_replay_non_flat_excluded": 7621,
                },
                "permissions": {
                    "promotion_allowed_by_this_packet": False,
                    "extended_paper_promotion_allowed_by_this_packet": False,
                    "live_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                    "private_submit_allowed_by_this_packet": False,
                },
            }
        )

        self.assertEqual(report["status"], "DRAFT_READY")
        self.assertEqual(report["candidate_profile"], "small_account_growth_paper")
        self.assertIn("ACKNOWLEDGE_PAPER_SMOKE_REVIEW_ONLY", report["draft_decision"]["allowed_decisions"])
        self.assertFalse(report["safety"]["does_write_final_human_decision_file"])
        self.assertTrue(report["safety"]["does_acknowledge_only"])
        self.assertFalse(report["safety"]["does_enable_paper"])
        self.assertFalse(report["safety"]["does_enable_live"])
        self.assertFalse(report["safety"]["does_allow_broker_submit"])
        self.assertFalse(report["safety"]["does_allow_private_submit"])
        self.assertFalse(report["safety"]["does_allow_real_orders"])
        self.assertFalse(report["safety"]["does_change_capital"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_blocks_if_packet_is_not_ready(self) -> None:
        report = draft.build_draft({"status": "BLOCKED", "review_ready": False})

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("PAPER_SMOKE_PACKET_NOT_SAFE_OR_READY", report["blockers"])


if __name__ == "__main__":
    unittest.main()
