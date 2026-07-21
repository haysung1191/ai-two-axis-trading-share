from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_cand022_provider_return_watch as watch


class Cand022ProviderReturnWatchTests(unittest.TestCase):
    def test_waits_without_writing_or_refreshing_when_dispatch_not_confirmed(self) -> None:
        return_dir = Path(tempfile.mkdtemp())
        send = {
            "send_confirmation_path": "sent.json",
            "send_confirmation_valid": False,
            "send_confirmation_blockers": ["dispatch_sent_confirmation_missing"],
        }
        receipt = {
            "return_staging_dir": str(return_dir),
            "expected_return_files": ["a.csv", "b.csv", "c.csv"],
        }

        with patch.object(watch, "read_json_optional", side_effect=[send, receipt]), patch.object(
            watch, "run_refresh"
        ) as run_refresh:
            report = watch.build_report("2026-05-14T10:00:00+09:00", run_refresh_when_ready=True, timeout_seconds=120)

        self.assertEqual(report["status"], "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES")
        self.assertIn("dispatch_sent_confirmation_missing_or_invalid", report["blockers"])
        self.assertIn("returned_provider_csvs_missing", report["blockers"])
        self.assertEqual(report["safety"], watch.SAFETY)
        self.assertTrue(report["run_refresh_when_ready_legacy_alias_for_copy_review_when_ready"])
        self.assertIn("does not run the refresh stack", report["legacy_field_notes"]["run_refresh_when_ready"])
        self.assertTrue(report["copy_review_required_before_refresh"])
        self.assertEqual(
            report["refresh_stack_invocation_policy"],
            "manual_after_returned_to_handoff_copy_review_ready",
        )
        self.assertEqual(
            report["refresh_allowed_only_if_copy_review_status"],
            "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertEqual(
            report["refresh_forbidden_if_copy_review_status"],
            "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        run_refresh.assert_not_called()

    def test_runs_copy_review_instead_of_refresh_when_confirmation_and_all_returns_are_present(self) -> None:
        return_dir = Path(tempfile.mkdtemp())
        for name in ["a.csv", "b.csv", "c.csv"]:
            (return_dir / name).write_text("request_id,value\n1,x\n", encoding="utf-8")
        send = {
            "send_confirmation_path": "sent.json",
            "send_confirmation_valid": True,
            "send_confirmation_blockers": [],
        }
        receipt = {
            "return_staging_dir": str(return_dir),
            "expected_return_files": ["a.csv", "b.csv", "c.csv"],
        }

        with patch.object(watch, "read_json_optional", side_effect=[send, receipt]), patch.object(
            watch, "run_refresh"
        ) as run_refresh, patch.object(
            watch,
            "run_copy_review",
            return_value={
                "passed": True,
                "returncode": 0,
                "latest_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                "latest_blockers": [],
                "latest_json": "copy_review.json",
            },
        ) as run_copy_review:
            report = watch.build_report("2026-05-14T10:00:00+09:00", run_refresh_when_ready=True, timeout_seconds=120)

        self.assertEqual(report["status"], "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW")
        self.assertEqual(report["blockers"], [])
        self.assertTrue(all(row["nonempty"] for row in report["returned_files"].values()))
        self.assertEqual(report["safety"], watch.SAFETY)
        self.assertIn("kis_provider_returned_to_handoff_copy_review_latest.json", report["source_files"]["copy_review"])
        self.assertIsNone(report["refresh_result"])
        self.assertTrue(report["copy_review_required_before_refresh"])
        self.assertIn("Deprecated compatibility alias", report["legacy_field_notes"]["run_refresh_when_ready"])
        self.assertEqual(
            report["refresh_stack_invocation_policy"],
            "manual_after_returned_to_handoff_copy_review_ready",
        )
        run_copy_review.assert_called_once_with(120)
        run_refresh.assert_not_called()

    def test_blocks_refresh_when_copy_review_is_not_ready(self) -> None:
        return_dir = Path(tempfile.mkdtemp())
        for name in ["a.csv", "b.csv", "c.csv"]:
            (return_dir / name).write_text("request_id,value\n1,x\n", encoding="utf-8")
        send = {
            "send_confirmation_path": "sent.json",
            "send_confirmation_valid": True,
            "send_confirmation_blockers": [],
        }
        receipt = {
            "return_staging_dir": str(return_dir),
            "expected_return_files": ["a.csv", "b.csv", "c.csv"],
        }

        with patch.object(watch, "read_json_optional", side_effect=[send, receipt]), patch.object(
            watch, "run_refresh"
        ) as run_refresh, patch.object(
            watch,
            "run_copy_review",
            return_value={
                "passed": True,
                "returncode": 0,
                "latest_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                "latest_blockers": ["returned_handoff_staging_verifier_not_ready"],
                "latest_json": "copy_review.json",
            },
        ):
            report = watch.build_report("2026-05-14T10:00:00+09:00", run_refresh_when_ready=True, timeout_seconds=120)

        self.assertEqual(report["status"], "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW")
        self.assertIn("returned_handoff_staging_verifier_not_ready", report["blockers"])
        self.assertIsNone(report["refresh_result"])
        run_refresh.assert_not_called()

    def test_no_refresh_mode_reports_ready_without_running_stack(self) -> None:
        return_dir = Path(tempfile.mkdtemp())
        for name in ["a.csv", "b.csv", "c.csv"]:
            (return_dir / name).write_text("ok\n", encoding="utf-8")
        send = {"send_confirmation_valid": True, "send_confirmation_blockers": []}
        receipt = {"return_staging_dir": str(return_dir), "expected_return_files": ["a.csv", "b.csv", "c.csv"]}

        with patch.object(watch, "read_json_optional", side_effect=[send, receipt]), patch.object(
            watch, "run_refresh"
        ) as run_refresh:
            report = watch.build_report("2026-05-14T10:00:00+09:00", run_refresh_when_ready=False, timeout_seconds=120)

        self.assertEqual(report["status"], "READY_TO_REVIEW_RETURNED_PROVIDER_CSVS")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["safety"], watch.SAFETY)
        run_refresh.assert_not_called()

    def test_outputs_json_and_markdown_are_serializable(self) -> None:
        report = {
            "generated_at": "2026-05-14T10:00:00+09:00",
            "status": "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES",
            "blockers": ["dispatch_sent_confirmation_missing_or_invalid"],
            "send_confirmation": {"valid": False},
            "return_staging_dir": "C:\\AI\\returned",
            "run_refresh_when_ready": True,
            "run_refresh_when_ready_legacy_alias_for_copy_review_when_ready": True,
            "legacy_field_notes": {
                "run_refresh_when_ready": "Deprecated compatibility alias. It controls copy review only."
            },
            "run_copy_review_when_ready": True,
            "copy_review_required_before_refresh": True,
            "refresh_stack_invocation_policy": "manual_after_returned_to_handoff_copy_review_ready",
            "refresh_allowed_only_if_copy_review_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
            "refresh_forbidden_if_copy_review_status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
            "returned_files": {},
            "copy_review_result": None,
            "refresh_result": None,
            "safety": watch.SAFETY,
            "source_files": {"copy_review": "copy_review.json"},
        }
        json.dumps(report)
        self.assertIn("CAND-022 Provider Return Watch", watch.render_md(report))


if __name__ == "__main__":
    unittest.main()
