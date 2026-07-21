from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_handoff_to_internal_copy_review.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_handoff_to_internal_copy_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
copy_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(copy_mod)


class KisProviderHandoffToInternalCopyReviewTests(unittest.TestCase):
    def test_copy_review_blocks_until_handoff_validator_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_files, internal_files = self.write_csvs(root)
            validator = self.write_validator(root, ready=False)
            report = copy_mod.build_report(
                "2026-05-14T02:30:00+09:00",
                handoff_validator_path=validator,
                handoff_files=handoff_files,
                internal_draft_files=internal_files,
            )

        self.assertEqual(report["status"], "BLOCK_HANDOFF_TO_INTERNAL_DRAFT_COPY_REVIEW")
        self.assertIn("handoff_draft_validator_not_ready", report["blockers"])
        self.assertIn("membership_draft_incomplete_rows", report["blockers"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_copy_review_ready_is_manual_and_non_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_files, internal_files = self.write_csvs(root)
            validator = self.write_validator(root, ready=True)
            report = copy_mod.build_report(
                "2026-05-14T02:30:00+09:00",
                handoff_validator_path=validator,
                handoff_files=handoff_files,
                internal_draft_files=internal_files,
            )

        self.assertEqual(report["status"], "READY_FOR_MANUAL_HANDOFF_TO_INTERNAL_DRAFT_COPY_REVIEW")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["copy_review"]["membership"]["handoff_row_count"], 1)
        self.assertIn("does_not_auto_copy handoff drafts", report["non_goals"])

    def write_csvs(self, root: Path) -> tuple[dict[str, Path], dict[str, Path]]:
        handoff_files = {
            "membership": root / "handoff_membership.csv",
            "event_or_no_event": root / "handoff_event.csv",
            "replay": root / "handoff_replay.csv",
        }
        internal_files = {
            "membership": root / "internal_membership.csv",
            "event_or_no_event": root / "internal_event.csv",
            "replay": root / "internal_replay.csv",
        }
        for path in list(handoff_files.values()) + list(internal_files.values()):
            self.write_csv(path, ["request_id", "symbol"], [["REQ1", "MU"]])
        return handoff_files, internal_files

    def write_validator(self, root: Path, ready: bool) -> Path:
        path = root / "handoff_validator.json"
        path.write_text(
            json.dumps(
                {
                    "status": "READY_TO_COPY_HANDOFF_DRAFT_TO_PROVIDER_RESPONSE_DRAFT_REVIEW" if ready else "BLOCK_HANDOFF_DRAFT_INCOMPLETE",
                    "blockers": [] if ready else ["membership_draft_incomplete_rows"],
                }
            ),
            encoding="utf-8",
        )
        return path

    def write_csv(self, path: Path, headers: list[str], rows: list[list[str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
