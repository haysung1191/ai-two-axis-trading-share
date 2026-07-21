from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_response_copy_review_packet.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_response_copy_review_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
copy_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(copy_mod)


class KisProviderResponseCopyReviewPacketTests(unittest.TestCase):
    def test_copy_review_blocks_until_draft_validator_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_files, response_files = self.write_csvs(root)
            validator_path = self.write_validator(root, ready=False)
            report = copy_mod.build_report(
                "2026-05-14T01:30:00+09:00",
                validator_path=validator_path,
                draft_files=draft_files,
                response_files=response_files,
            )

        self.assertEqual(report["status"], "BLOCK_PROVIDER_RESPONSE_COPY_REVIEW")
        self.assertIn("provider_response_draft_validator_not_ready", report["blockers"])
        self.assertIn("draft_incomplete", report["blockers"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_copy_review_ready_is_manual_and_non_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_files, response_files = self.write_csvs(root)
            validator_path = self.write_validator(root, ready=True)
            report = copy_mod.build_report(
                "2026-05-14T01:30:00+09:00",
                validator_path=validator_path,
                draft_files=draft_files,
                response_files=response_files,
            )

        self.assertEqual(report["status"], "READY_FOR_MANUAL_PROVIDER_RESPONSE_COPY_REVIEW")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["copy_review"]["membership"]["draft_row_count"], 1)
        self.assertEqual(report["copy_review"]["membership"]["current_response_row_count"], 0)
        self.assertIn("do_not_auto_copy_files", report["non_goals"])

    def write_csvs(self, root: Path) -> tuple[dict[str, Path], dict[str, Path]]:
        draft_files = {
            "membership": root / "draft_membership.csv",
            "event_or_no_event": root / "draft_event.csv",
            "replay": root / "draft_replay.csv",
        }
        response_files = {
            "membership": root / "response_membership.csv",
            "event_or_no_event": root / "response_event.csv",
            "replay": root / "response_replay.csv",
        }
        for path in draft_files.values():
            self.write_csv(path, ["request_id", "symbol"], [["REQ1", "MU"]])
        for path in response_files.values():
            self.write_csv(path, ["request_id", "symbol"], [])
        return draft_files, response_files

    def write_validator(self, root: Path, ready: bool) -> Path:
        path = root / "draft_validator.json"
        path.write_text(
            json.dumps(
                {
                    "status": "READY_TO_COPY_DRAFT_TO_PROVIDER_RESPONSE_REVIEW" if ready else "BLOCK_PROVIDER_RESPONSE_DRAFT_INCOMPLETE",
                    "blockers": [] if ready else ["draft_incomplete"],
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
