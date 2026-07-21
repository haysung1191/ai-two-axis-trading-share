from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_delisting_no_event_coverage_verifier.py")
SPEC = importlib.util.spec_from_file_location("build_kis_delisting_no_event_coverage_verifier", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
verifier_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier_mod)


class KisDelistingNoEventCoverageVerifierTests(unittest.TestCase):
    def test_empty_template_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "coverage.csv"
            report = verifier_mod.build_report("2026-05-14T00:00:00+09:00", path)

        self.assertEqual(report["status"], "BLOCK_DELISTING_NO_EVENT_COVERAGE_NOT_VERIFIED")
        self.assertTrue(report["template_created"])
        self.assertIn("kis_delisting_no_event_coverage_empty", report["blockers"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_authoritative_no_event_coverage_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "coverage.csv"
            path.write_text(
                ",".join(verifier_mod.REQUIRED_COLUMNS)
                + "\n"
                + "MU,kis_us_stocks,2000-01-01,2026-04-30,no_event_found,vendor,snap,licensed_vendor,2026-05-14,test\n",
                encoding="utf-8",
            )
            report = verifier_mod.build_report("2026-05-14T00:00:00+09:00", path)

        self.assertEqual(report["status"], "PASS_DELISTING_NO_EVENT_COVERAGE_VERIFIED")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["inspection"]["operation_ready_quality_row_count"], 1)
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_caveated_no_event_coverage_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "coverage.csv"
            path.write_text(
                ",".join(verifier_mod.REQUIRED_COLUMNS)
                + "\n"
                + "MU,kis_us_stocks,2000-01-01,2026-04-30,no_event_found,manual,snap,manual_review_caveated,2026-05-14,test\n",
                encoding="utf-8",
            )
            report = verifier_mod.build_report("2026-05-14T00:00:00+09:00", path)

        self.assertEqual(report["status"], "BLOCK_DELISTING_NO_EVENT_COVERAGE_NOT_VERIFIED")
        self.assertIn("kis_delisting_no_event_coverage_caveated_not_operation_ready", report["blockers"])


if __name__ == "__main__":
    unittest.main()
