from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_delisting_symbol_change_policy.py")
SPEC = importlib.util.spec_from_file_location("build_kis_delisting_symbol_change_policy", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
policy_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy_mod)


class KisDelistingSymbolChangePolicyTests(unittest.TestCase):
    def test_policy_blocks_without_event_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = policy_mod.build_policy(
                "2026-05-13T00:00:00+09:00",
                Path(tmp) / "missing.csv",
                {"status": "BLOCK_DELISTING_EVENT_FILE_NOT_VERIFIED"},
                {"status": "BLOCK_DELISTING_NO_EVENT_COVERAGE_NOT_VERIFIED"},
                {"status": "BLOCK_DELISTING_REPLAY_NOT_VERIFIED"},
            )

        self.assertEqual(policy["status"], "BLOCKED_DELISTING_SYMBOL_POLICY_NOT_VERIFIED")
        self.assertFalse(policy["operation_ready"])
        self.assertIn("kis_delisting_symbol_change_events_missing", policy["blockers"])
        self.assertIn("kis_delisting_symbol_change_events_not_operation_ready", policy["blockers"])
        self.assertIn("kis_delisting_replay_evidence_not_operation_ready", policy["blockers"])
        self.assertFalse(policy["safety"]["broker_submit_allowed"])

    def test_policy_uses_event_verifier_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            path.write_text("symbol\n", encoding="utf-8")
            policy = policy_mod.build_policy(
                "2026-05-13T00:00:00+09:00",
                path,
                {"status": "BLOCK_DELISTING_EVENT_FILE_NOT_VERIFIED"},
                {"status": "BLOCK_DELISTING_NO_EVENT_COVERAGE_NOT_VERIFIED"},
                {"status": "BLOCK_DELISTING_REPLAY_NOT_VERIFIED"},
            )

        self.assertEqual(policy["event_verifier_status"], "BLOCK_DELISTING_EVENT_FILE_NOT_VERIFIED")
        self.assertEqual(policy["no_event_verifier_status"], "BLOCK_DELISTING_NO_EVENT_COVERAGE_NOT_VERIFIED")
        self.assertEqual(policy["replay_verifier_status"], "BLOCK_DELISTING_REPLAY_NOT_VERIFIED")
        self.assertFalse(policy["event_file_verified"])
        self.assertFalse(policy["no_event_coverage_verified"])
        self.assertFalse(policy["event_coverage_verified"])
        self.assertFalse(policy["replay_verified"])
        self.assertIn("kis_delisting_symbol_change_events_not_operation_ready", policy["blockers"])
        self.assertIn("kis_delisting_no_event_coverage_not_operation_ready", policy["blockers"])

    def test_policy_accepts_verified_no_event_coverage_as_event_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            path.write_text("symbol\n", encoding="utf-8")
            policy = policy_mod.build_policy(
                "2026-05-13T00:00:00+09:00",
                path,
                {"status": "BLOCK_DELISTING_EVENT_FILE_NOT_VERIFIED"},
                {"status": "PASS_DELISTING_NO_EVENT_COVERAGE_VERIFIED"},
                {"status": "BLOCK_DELISTING_REPLAY_NOT_VERIFIED"},
            )

        self.assertTrue(policy["no_event_coverage_verified"])
        self.assertTrue(policy["event_coverage_verified"])
        self.assertNotIn("kis_delisting_symbol_change_events_not_operation_ready", policy["blockers"])
        self.assertIn("kis_delisting_replay_evidence_not_operation_ready", policy["blockers"])

    def test_policy_passes_with_verified_no_event_coverage_and_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            path.write_text("symbol\n", encoding="utf-8")
            policy = policy_mod.build_policy(
                "2026-05-13T00:00:00+09:00",
                path,
                {"status": "BLOCK_DELISTING_EVENT_FILE_NOT_VERIFIED"},
                {"status": "PASS_DELISTING_NO_EVENT_COVERAGE_VERIFIED"},
                {"status": "PASS_DELISTING_REPLAY_VERIFIED"},
            )

        self.assertEqual(policy["status"], "PASS_DELISTING_SYMBOL_POLICY_VERIFIED")
        self.assertTrue(policy["operation_ready"])
        self.assertEqual(policy["blockers"], [])


if __name__ == "__main__":
    unittest.main()
