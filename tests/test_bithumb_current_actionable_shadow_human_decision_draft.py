from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_shadow_human_decision_draft.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_shadow_human_decision_draft", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
draft = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(draft)


class BithumbCurrentActionableShadowHumanDecisionDraftTests(unittest.TestCase):
    def test_builds_placeholder_draft_without_writing_human_decision_or_order_paths(self) -> None:
        report = draft.build_draft(
            {
                "registered_candidate": {"candidate_id": "sweep1354"},
                "latest_oos_candidate": {"candidate_id": "sweep1355"},
                "comparison": {
                    "candidate_rollover_detected": True,
                    "latest_cagr_higher": True,
                    "latest_mdd_not_worse": True,
                },
                "blockers": ["FRESH_HUMAN_DECISION_REQUIRED_FOR_LATEST_OOS_CANDIDATE"],
            },
            {"candidate_id": "sweep1355"},
            {"candidate_id": "sweep1354", "decision": "APPROVE_SHADOW_REVIEW_ONLY"},
        )

        self.assertEqual(report["status"], "DRAFT_READY")
        self.assertEqual(report["candidate_id"], "sweep1355")
        self.assertEqual(report["draft_decision"]["decision"], "HUMAN_MUST_CHOOSE_APPROVE_REJECT_OR_DEFER")
        self.assertIn("APPROVE_SHADOW_REVIEW_ONLY", report["draft_decision"]["allowed_decisions"])
        self.assertIn("EXISTING_DECISION_POINTS_TO_DIFFERENT_CANDIDATE", report["blockers"])
        self.assertFalse(report["safety"]["does_write_human_decision_file"])
        self.assertFalse(report["safety"]["does_register_shadow_candidate"])
        self.assertFalse(report["safety"]["does_emit_order_signal"])
        self.assertFalse(report["safety"]["does_enable_live"])
        self.assertFalse(report["safety"]["broker_submit_allowed_by_this_report"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_blocks_without_candidate_id(self) -> None:
        report = draft.build_draft({}, {}, {})

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("LATEST_OOS_CANDIDATE_MISSING", report["blockers"])


if __name__ == "__main__":
    unittest.main()
