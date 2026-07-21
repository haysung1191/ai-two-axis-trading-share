from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\record_bithumb_current_actionable_shadow_decision.py")
SPEC = importlib.util.spec_from_file_location("record_bithumb_current_actionable_shadow_decision", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
recorder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recorder)


def phrase_packet(candidate_id: str = "sweep2154") -> dict:
    return {
        "next_phrase": {
            "decision_id": "bithumb_current_actionable_shadow_review",
            "candidate_id": candidate_id,
            "exact_phrase_to_record": "APPROVE_SHADOW_REVIEW_ONLY",
        }
    }


class RecordBithumbCurrentActionableShadowDecisionTests(unittest.TestCase):
    def test_dry_run_validates_exact_candidate_without_writing(self) -> None:
        report = recorder.build_record(
            phrase_packet(),
            candidate_id="sweep2154",
            decision="APPROVE_SHADOW_REVIEW_ONLY",
            rationale="reviewed",
        )

        self.assertEqual(report["status"], "READY_TO_WRITE_DECISION")
        self.assertFalse(report["file_mutated"])
        self.assertEqual(report["blockers"], [])
        self.assertFalse(report["safety"]["does_register_shadow_candidate"])
        self.assertFalse(report["safety"]["does_enable_live"])
        self.assertFalse(report["safety"]["broker_submit_allowed_by_this_report"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_blocks_stale_candidate_and_bad_decision(self) -> None:
        report = recorder.build_record(
            phrase_packet(),
            candidate_id="stale",
            decision="APPROVE_LIVE",
            rationale="reviewed",
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("CANDIDATE_ID_MISMATCH", report["blockers"])
        self.assertIn("DECISION_NOT_ALLOWED", report["blockers"])
        self.assertIsNone(report["decision_payload"])

    def test_write_records_only_human_decision_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            decision_path = Path(td) / "decision.json"
            with patch.object(recorder, "DECISION_JSON", decision_path):
                report = recorder.build_record(
                    phrase_packet(),
                    candidate_id="sweep2154",
                    decision="DEFER",
                    rationale="wait",
                    write=True,
                    generated_at_utc="2026-05-16T00:00:00+00:00",
                )

            self.assertEqual(report["status"], "DECISION_RECORDED")
            self.assertTrue(report["file_mutated"])
            payload = recorder.read_json(decision_path, {})
            self.assertEqual(payload["candidate_id"], "sweep2154")
            self.assertEqual(payload["decision"], "DEFER")
            self.assertEqual(payload["decided_by"], "human_gatekeeper")


if __name__ == "__main__":
    unittest.main()
