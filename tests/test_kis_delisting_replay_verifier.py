from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_delisting_replay_verifier.py")
SPEC = importlib.util.spec_from_file_location("build_kis_delisting_replay_verifier", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


class KisDelistingReplayVerifierTests(unittest.TestCase):
    def header(self) -> str:
        return ",".join(verifier.REQUIRED_COLUMNS) + "\n"

    def test_empty_replay_file_blocks_with_valid_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "replay.csv"
            path.write_text(self.header(), encoding="utf-8")
            report = verifier.build_report("2026-05-14T00:00:00+09:00", path)

        self.assertEqual(report["status"], "BLOCK_DELISTING_REPLAY_NOT_VERIFIED")
        self.assertIn("kis_delisting_replay_cases_empty", report["blockers"])
        self.assertIn("kis_delisting_replay_required_scenarios_missing", report["blockers"])
        self.assertFalse(report["safety"]["live_enabled"])

    def test_caveated_complete_scenarios_do_not_clear_operation_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "replay.csv"
            rows = [
                "tc,AAA,kis_us_stocks,ticker_change,2024-01-01,1,10,,BBB,,BBB,0,false,manual,snap,manual_review_caveated,test",
                "dt,AAA,kis_us_stocks,delisting,2024-01-01,1,10,8,,,0,8,false,manual,snap,manual_review_caveated,test",
                "dc,AAA,kis_us_stocks,delisting,2024-01-01,1,10,,,0.5,0,5,false,manual,snap,manual_review_caveated,test",
                "ub,AAA,kis_us_stocks,delisting,2024-01-01,1,10,,,,0,0,true,manual,snap,manual_review_caveated,test",
            ]
            path.write_text(self.header() + "\n".join(rows) + "\n", encoding="utf-8")
            report = verifier.build_report("2026-05-14T00:00:00+09:00", path)

        self.assertEqual(report["status"], "PASS_DELISTING_REPLAY_SCHEMA_WITH_CAVEATED_OR_INCOMPLETE_EVIDENCE")
        self.assertIn("kis_delisting_replay_cases_caveated_not_operation_ready", report["blockers"])
        self.assertFalse(report["inspection"]["verified"])

    def test_authoritative_complete_scenarios_can_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "replay.csv"
            rows = [
                "tc,AAA,kis_us_stocks,ticker_change,2024-01-01,1,10,,BBB,,BBB,0,false,test,snap,replay_test_authoritative,test",
                "dt,AAA,kis_us_stocks,delisting,2024-01-01,1,10,8,,,0,8,false,test,snap,replay_test_authoritative,test",
                "dc,AAA,kis_us_stocks,delisting,2024-01-01,1,10,,,0.5,0,5,false,test,snap,replay_test_authoritative,test",
                "ub,AAA,kis_us_stocks,delisting,2024-01-01,1,10,,,,0,0,true,test,snap,replay_test_authoritative,test",
            ]
            path.write_text(self.header() + "\n".join(rows) + "\n", encoding="utf-8")
            report = verifier.build_report("2026-05-14T00:00:00+09:00", path)

        self.assertEqual(report["status"], "PASS_DELISTING_REPLAY_VERIFIED")
        self.assertEqual(report["blockers"], [])
        self.assertFalse(report["safety"]["broker_submit_allowed"])


if __name__ == "__main__":
    unittest.main()
