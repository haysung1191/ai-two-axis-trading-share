from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_handoff_fill_progress.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_handoff_fill_progress", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
progress_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(progress_mod)


class KisProviderHandoffFillProgressTests(unittest.TestCase):
    def test_progress_counts_completed_and_open_rows_without_mutating_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            validator_path = Path(tmp) / "validator.json"
            validator_path.write_text(
                json.dumps(
                    {
                        "status": "BLOCK_HANDOFF_DRAFT_INCOMPLETE",
                        "inspections": {
                            "membership": {
                                "row_count": 2,
                                "incomplete_rows": [{"row_number": 3, "request_id": "M2"}],
                                "unsupported_quality_row_numbers": [],
                                "invalid_coverage_row_numbers": [],
                                "rejected_source_rows": [],
                                "blockers": ["membership_draft_incomplete_rows"],
                                "passed": False,
                            },
                            "replay": {
                                "row_count": 1,
                                "incomplete_rows": [],
                                "unsupported_quality_row_numbers": [],
                                "invalid_coverage_row_numbers": [],
                                "rejected_source_rows": [],
                                "blockers": [],
                                "passed": True,
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            report = progress_mod.build_report("2026-05-14T02:30:00+09:00", validator_path=validator_path)

        self.assertEqual(report["status"], "BLOCK_HANDOFF_FILL_PROGRESS_OPEN")
        self.assertEqual(report["total_rows"], 3)
        self.assertEqual(report["completed_rows"], 2)
        self.assertEqual(report["open_rows"], 1)
        self.assertEqual(report["progress_by_kind"]["membership"]["blocked_request_ids"], ["M2"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_progress_ready_only_when_validator_ready_and_no_open_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            validator_path = Path(tmp) / "validator.json"
            validator_path.write_text(
                json.dumps(
                    {
                        "status": "READY_TO_COPY_HANDOFF_DRAFT_TO_PROVIDER_RESPONSE_DRAFT_REVIEW",
                        "inspections": {
                            "membership": {
                                "row_count": 1,
                                "incomplete_rows": [],
                                "unsupported_quality_row_numbers": [],
                                "invalid_coverage_row_numbers": [],
                                "rejected_source_rows": [],
                                "blockers": [],
                                "passed": True,
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            report = progress_mod.build_report("2026-05-14T02:30:00+09:00", validator_path=validator_path)

        self.assertEqual(report["status"], "READY_HANDOFF_FILL_COMPLETE_FOR_COPY_REVIEW")
        self.assertEqual(report["completion_percent"], 100.0)


if __name__ == "__main__":
    unittest.main()
