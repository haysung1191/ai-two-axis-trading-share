from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_cand022_provider_return_watch_process_status.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_provider_return_watch_process_status", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
status_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(status_mod)


class Cand022ProviderReturnWatchProcessStatusTests(unittest.TestCase):
    def test_reports_running_watcher_without_side_effects(self) -> None:
        with patch.object(
            status_mod,
            "read_json_optional",
            return_value={
                "status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
                "blockers": ["dispatch_sent_confirmation_missing_or_invalid"],
                "copy_review_required_before_refresh": True,
                "refresh_stack_invocation_policy": "manual_after_returned_to_handoff_copy_review_ready",
                "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
            },
        ):
            report = status_mod.build_report(
                "2026-05-14T10:40:00+09:00",
                rows=[
                    {
                        "ProcessId": 1234,
                        "CreationDate": "/Date(1778722800000)/",
                        "CommandLine": "python run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60",
                    }
                ],
            )

        self.assertEqual(report["status"], "WATCHER_RUNNING")
        self.assertTrue(report["watch_running"])
        self.assertEqual(report["watcher_process_ids"], [1234])
        self.assertEqual(report["watcher_started"][0]["process_id"], 1234)
        self.assertIn("started_at_kst", report["watcher_started"][0])
        self.assertIsNotNone(report["watcher_started"][0]["age_minutes"])
        self.assertEqual(report["watcher_started"][0]["cycles"], 180)
        self.assertEqual(report["watcher_started"][0]["sleep_seconds"], 60)
        self.assertEqual(report["watcher_started"][0]["expected_duration_minutes"], 180.0)
        self.assertIn("expected_end_at_kst", report["watcher_started"][0])
        self.assertIsNotNone(report["watcher_started"][0]["remaining_minutes"])
        self.assertTrue(report["ready_for_unattended_wait"])
        self.assertEqual(
            report["provider_return_watch_policy"]["refresh_stack_invocation_policy"],
            "manual_after_returned_to_handoff_copy_review_ready",
        )
        self.assertIn("run_cand022_provider_return_watch.py", report["recommended_command_if_not_running"])
        self.assertIn("does_not_start_watcher", report["non_goals"])
        self.assertEqual(report["safety"], status_mod.SAFETY)

    def test_reports_not_running_but_ready_when_copy_review_ready_for_manual_followup(self) -> None:
        with patch.object(
            status_mod,
            "read_json_optional",
            return_value={
                "status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                "blockers": [],
                "copy_review_required_before_refresh": True,
                "refresh_stack_invocation_policy": "manual_after_returned_to_handoff_copy_review_ready",
                "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
            },
        ):
            report = status_mod.build_report("2026-05-14T10:40:00+09:00", rows=[])

        self.assertEqual(report["status"], "WATCHER_NOT_RUNNING_COPY_REVIEW_READY")
        self.assertFalse(report["watch_running"])
        self.assertTrue(report["copy_review_ready_for_manual_followup"])
        self.assertTrue(report["ready_for_unattended_wait"])

    def test_reports_not_running_while_still_waiting(self) -> None:
        with patch.object(
            status_mod,
            "read_json_optional",
            return_value={
                "status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
                "blockers": ["returned_provider_csvs_missing"],
            },
        ):
            report = status_mod.build_report("2026-05-14T10:40:00+09:00", rows=[])

        self.assertEqual(report["status"], "WATCHER_NOT_RUNNING_WAITING_FOR_EXTERNAL_INPUT")
        self.assertFalse(report["ready_for_unattended_wait"])
        self.assertIn("returned_provider_csvs_missing", report["provider_return_watch_blockers"])


if __name__ == "__main__":
    unittest.main()
