from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_delisting_event_verifier.py")
SPEC = importlib.util.spec_from_file_location("build_kis_delisting_event_verifier", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


class KisDelistingEventVerifierTests(unittest.TestCase):
    def test_empty_event_file_blocks_with_valid_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            path.write_text(",".join(verifier.REQUIRED_COLUMNS) + "\n", encoding="utf-8")
            report = verifier.build_report("2026-05-13T00:00:00+09:00", path)

        self.assertEqual(report["status"], "BLOCK_DELISTING_EVENT_FILE_NOT_VERIFIED")
        self.assertIn("kis_delisting_symbol_change_events_empty", report["blockers"])
        self.assertFalse(report["safety"]["live_enabled"])

    def test_caveated_event_file_does_not_clear_operation_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            path.write_text(
                ",".join(verifier.REQUIRED_COLUMNS)
                + "\nAAA,kis_us_stocks,delisting,2024-01-01,,cash_recovery,0.5,manual,snap,manual_review_caveated,test\n",
                encoding="utf-8",
            )
            report = verifier.build_report("2026-05-13T00:00:00+09:00", path)

        self.assertEqual(report["status"], "PASS_DELISTING_EVENT_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE")
        self.assertIn("kis_delisting_symbol_change_events_caveated_not_operation_ready", report["blockers"])

    def test_authoritative_event_file_can_pass_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            path.write_text(
                ",".join(verifier.REQUIRED_COLUMNS)
                + "\nAAA,kis_us_stocks,delisting,2024-01-01,,cash_recovery,0.5,exchange,snap,authoritative,test\n",
                encoding="utf-8",
            )
            report = verifier.build_report("2026-05-13T00:00:00+09:00", path)

        self.assertEqual(report["status"], "PASS_DELISTING_EVENT_FILE_VERIFIED")
        self.assertEqual(report["blockers"], [])
        self.assertFalse(report["safety"]["broker_submit_allowed"])


if __name__ == "__main__":
    unittest.main()
