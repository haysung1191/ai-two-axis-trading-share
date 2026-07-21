from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_response_import_preview.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_response_import_preview", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
preview_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preview_mod)


class KisProviderResponseImportPreviewTests(unittest.TestCase):
    def test_import_blocks_when_validator_not_ready(self) -> None:
        report = preview_mod.build_report(
            "2026-05-14T00:00:00+09:00",
            {"status": "BLOCK_PROVIDER_RESPONSE_NOT_READY", "blockers": ["membership_response_empty"]},
        )

        self.assertEqual(report["status"], "BLOCK_PROVIDER_RESPONSE_IMPORT")
        self.assertIn("provider_response_validator_not_ready", report["blockers"])
        self.assertIsNone(report["preview_files"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_ready_validator_builds_preview_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            old_response = preview_mod.RESPONSE_FILES
            old_preview = preview_mod.INTAKE_REVIEW_FILES
            try:
                preview_mod.RESPONSE_FILES = {
                    "membership": tmp_path / "membership_response.csv",
                    "event_or_no_event": tmp_path / "event_response.csv",
                    "replay": tmp_path / "replay_response.csv",
                }
                preview_mod.INTAKE_REVIEW_FILES = {
                    "membership": tmp_path / "preview" / "membership.csv",
                    "event_or_no_event": tmp_path / "preview" / "event.csv",
                    "replay": tmp_path / "preview" / "replay.csv",
                }
                self.write_rows(
                    preview_mod.RESPONSE_FILES["membership"],
                    preview_mod.MEMBERSHIP_INTAKE_HEADERS + ["request_id"],
                    [{"request_id": "REQ1", "symbol": "MU", "axis": "kis_us_stocks", "active_from": "2000-01-01"}],
                )
                self.write_rows(
                    preview_mod.RESPONSE_FILES["event_or_no_event"],
                    preview_mod.EVENT_INTAKE_HEADERS + ["request_id"],
                    [{"request_id": "REQ2", "symbol": "MU", "axis": "kis_us_stocks", "coverage_status": "no_event_found"}],
                )
                self.write_rows(
                    preview_mod.RESPONSE_FILES["replay"],
                    preview_mod.REPLAY_INTAKE_HEADERS + ["request_id"],
                    [{"request_id": "REQ3", "scenario": "ticker_change", "symbol": "MU"}],
                )
                report = preview_mod.build_report(
                    "2026-05-14T00:00:00+09:00",
                    {"status": "READY_TO_IMPORT_PROVIDER_RESPONSE_TO_INTAKE_REVIEW", "blockers": []},
                )
            finally:
                preview_mod.RESPONSE_FILES = old_response
                preview_mod.INTAKE_REVIEW_FILES = old_preview

        self.assertEqual(report["status"], "READY_FOR_MANUAL_INTAKE_IMPORT_REVIEW")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["preview_files"]["membership"]["row_count"], 1)
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def write_rows(self, path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                writer.writerow({header: row.get(header, "") for header in headers})


if __name__ == "__main__":
    unittest.main()
