from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_public_source_probe_report.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_public_source_probe_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
probe_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe_mod)


class KisProviderPublicSourceProbeReportTests(unittest.TestCase):
    def test_probe_report_rejects_non_pit_sources_without_mutating_state(self) -> None:
        report = probe_mod.build_report(
            "2026-05-14T04:30:00+09:00",
            probes=[
                {
                    "source_url": "https://example.com",
                    "decision": "REJECT_FOR_KIS_PIT_OPERATION_READY_INTAKE",
                }
            ],
        )

        self.assertEqual(report["status"], "PUBLIC_SOURCE_PROBE_REVIEW_ONLY_NO_OPERATION_READY_ROWS")
        self.assertEqual(report["accepted_for_operation_ready_intake_count"], 0)
        self.assertEqual(report["rejected_count"], 1)
        self.assertIn("does_not_fill handoff drafts", report["non_goals"])
        self.assertFalse(report["safety"]["order_intent_created"])


if __name__ == "__main__":
    unittest.main()
