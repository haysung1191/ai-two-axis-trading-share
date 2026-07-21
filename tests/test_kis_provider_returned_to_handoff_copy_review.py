from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_returned_to_handoff_copy_review.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_returned_to_handoff_copy_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
copy_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(copy_mod)


class KisProviderReturnedToHandoffCopyReviewTests(unittest.TestCase):
    def write_csv(self, path: Path, request_ids: list[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["request_id", "source"])
            writer.writeheader()
            for request_id in request_ids:
                writer.writerow({"request_id": request_id, "source": "licensed_vendor"})

    def test_blocks_until_returned_staging_verifier_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            verifier = root / "verifier.json"
            returned = root / "returned"
            handoff = root / "handoff"
            verifier.write_text(
                json.dumps({"status": "BLOCK_RETURNED_HANDOFF_STAGING", "blockers": ["returned_draft_missing"]}),
                encoding="utf-8",
            )

            report = copy_mod.build_report(
                "2026-05-14T16:00:00+09:00",
                verifier_path=verifier,
                returned_dir=returned,
                handoff_dir=handoff,
            )

        self.assertEqual(report["status"], "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW")
        self.assertIn("returned_handoff_staging_verifier_not_ready", report["blockers"])
        self.assertIn("membership_returned_file_missing", report["blockers"])
        self.assertIn("does_not_auto_copy_returned_files", report["non_goals"])
        self.assertEqual(report["safety"], copy_mod.SAFETY)

    def test_ready_report_builds_manual_copy_plan_without_copying(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            verifier = root / "verifier.json"
            returned = root / "returned"
            handoff = root / "handoff"
            verifier.write_text(json.dumps({"status": "READY_RETURNED_HANDOFF_FOR_REVIEW"}), encoding="utf-8")
            for filename in copy_mod.EXPECTED_FILES.values():
                self.write_csv(returned / filename, ["REQ-1", "REQ-2"])
                self.write_csv(handoff / filename, ["OLD-REQ"])

            report = copy_mod.build_report(
                "2026-05-14T16:00:00+09:00",
                verifier_path=verifier,
                returned_dir=returned,
                handoff_dir=handoff,
            )

        self.assertEqual(report["status"], "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(len(report["manual_copy_plan"]), 3)
        self.assertEqual(report["copy_review"]["membership"]["returned_request_ids"], ["REQ-1", "REQ-2"])
        self.assertEqual(report["copy_review"]["membership"]["current_handoff_request_ids"], ["OLD-REQ"])
        self.assertTrue(
            all(
                row["allowed_only_if_status"] == "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW"
                for row in report["manual_copy_plan"]
            )
        )
        self.assertIn("does_not_mutate_provider_response", report["non_goals"])


if __name__ == "__main__":
    unittest.main()
