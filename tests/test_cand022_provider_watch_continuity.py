from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\ensure_cand022_provider_return_watch_continuity.py")
SPEC = importlib.util.spec_from_file_location("ensure_cand022_provider_return_watch_continuity", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
ensure_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ensure_mod)


class Cand022ProviderWatchContinuityTests(unittest.TestCase):
    def test_reports_ok_when_watcher_has_enough_remaining_time(self) -> None:
        report = ensure_mod.build_report(
            "2026-05-14T13:20:00+09:00",
            start_if_needed=False,
            renew_within_minutes=30,
            process_status={
                "status": "WATCHER_RUNNING",
                "watch_running": True,
                "watcher_process_ids": [1234],
                "watcher_started": [{"remaining_minutes": 45.0}],
                "provider_return_watch_status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
                "provider_return_watch_blockers": ["returned_provider_csvs_missing"],
            },
        )

        self.assertEqual(report["status"], "WATCHER_CONTINUITY_OK")
        self.assertFalse(report["needs_new_watcher"])
        self.assertEqual(report["safety"], ensure_mod.SAFETY)

    def test_reports_needs_start_when_watcher_remaining_time_is_low(self) -> None:
        report = ensure_mod.build_report(
            "2026-05-14T13:20:00+09:00",
            start_if_needed=False,
            renew_within_minutes=30,
            process_status={
                "status": "WATCHER_RUNNING",
                "watch_running": True,
                "watcher_process_ids": [1234],
                "watcher_started": [{"remaining_minutes": 12.0}],
                "provider_return_watch_status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
                "provider_return_watch_blockers": ["returned_provider_csvs_missing"],
            },
        )

        self.assertEqual(report["status"], "WATCHER_CONTINUITY_NEEDS_START")
        self.assertTrue(report["needs_new_watcher"])
        self.assertIn("--cycles 180", report["start_command"])
        self.assertIn("Start-Process -WindowStyle Hidden", report["start_command"])

    def test_starts_when_requested_and_needed(self) -> None:
        launched: list[str] = []

        def fake_launcher(command: str) -> dict[str, object]:
            launched.append(command)
            return {"command": command, "returncode": 0, "started": True}

        report = ensure_mod.build_report(
            "2026-05-14T13:20:00+09:00",
            start_if_needed=True,
            renew_within_minutes=30,
            process_status={
                "status": "WATCHER_NOT_RUNNING_WAITING_FOR_EXTERNAL_INPUT",
                "watch_running": False,
                "watcher_process_ids": [],
                "watcher_started": [],
                "provider_return_watch_status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
                "provider_return_watch_blockers": ["returned_provider_csvs_missing"],
            },
            launcher=fake_launcher,
        )

        self.assertEqual(report["status"], "WATCHER_CONTINUITY_STARTED")
        self.assertTrue(report["needs_new_watcher"])
        self.assertEqual(len(launched), 1)
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_does_not_restart_when_any_watcher_has_enough_remaining_time(self) -> None:
        report = ensure_mod.build_report(
            "2026-05-14T13:20:00+09:00",
            start_if_needed=True,
            renew_within_minutes=30,
            process_status={
                "status": "WATCHER_RUNNING",
                "watch_running": True,
                "watcher_process_ids": [1234, 5678],
                "watcher_started": [{"remaining_minutes": 8.0}, {"remaining_minutes": 178.0}],
                "provider_return_watch_status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
                "provider_return_watch_blockers": ["returned_provider_csvs_missing"],
            },
            launcher=lambda _command: {"started": True},
        )

        self.assertEqual(report["status"], "WATCHER_CONTINUITY_OK")
        self.assertFalse(report["needs_new_watcher"])
        self.assertEqual(report["min_remaining_minutes"], 8.0)
        self.assertEqual(report["max_remaining_minutes"], 178.0)

    def test_does_not_start_when_copy_review_is_ready_for_manual_followup(self) -> None:
        report = ensure_mod.build_report(
            "2026-05-14T13:20:00+09:00",
            start_if_needed=True,
            process_status={
                "status": "WATCHER_NOT_RUNNING_COPY_REVIEW_READY",
                "watch_running": False,
                "watcher_process_ids": [],
                "watcher_started": [],
                "provider_return_watch_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                "provider_return_watch_blockers": [],
                "copy_review_ready_for_manual_followup": True,
                "provider_return_watch_policy": {
                    "copy_review_required_before_refresh": True,
                    "refresh_stack_invocation_policy": "manual_after_returned_to_handoff_copy_review_ready",
                    "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                    "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                },
            },
            launcher=lambda _command: {"started": True},
        )

        self.assertEqual(report["status"], "WATCHER_CONTINUITY_OK")
        self.assertFalse(report["needs_new_watcher"])
        self.assertTrue(report["copy_review_ready_for_manual_followup"])
        self.assertEqual(
            report["provider_return_watch_policy"]["refresh_stack_invocation_policy"],
            "manual_after_returned_to_handoff_copy_review_ready",
        )


if __name__ == "__main__":
    unittest.main()
