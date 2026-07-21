from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_pit_membership_verifier.py")
SPEC = importlib.util.spec_from_file_location("build_kis_pit_membership_verifier", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


class KisPitMembershipVerifierTests(unittest.TestCase):
    def test_empty_canonical_files_block_but_schema_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            files = {}
            for axis in ("kis_us_stocks", "kis_us_etfs", "kis_korea_stocks", "kis_korea_etfs"):
                path = Path(tmp) / f"{axis}.csv"
                path.write_text(",".join(verifier.REQUIRED_COLUMNS) + "\n", encoding="utf-8")
                files[axis] = path

            report = verifier.build_report("2026-05-13T00:00:00+09:00", files, {}, {}, {})

        self.assertEqual(report["status"], "BLOCK_INCOMPLETE_MEMBERSHIP_DATA")
        self.assertTrue(report["all_files_exist"])
        self.assertTrue(report["all_schema_ok"])
        self.assertFalse(report["all_have_rows"])
        self.assertFalse(report["all_schema_verified"])
        self.assertIn("canonical_membership_files_empty", report["blockers"])
        self.assertFalse(report["safety"]["live_enabled"])

    def test_populated_well_formed_files_can_pass_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            files = {}
            row = "ABC,us_stock,kis_us_stocks,2020-01-01,,2020-01-01,,test_source,snap1,authoritative,test\n"
            for axis in ("kis_us_stocks", "kis_us_etfs", "kis_korea_stocks", "kis_korea_etfs"):
                path = Path(tmp) / f"{axis}.csv"
                path.write_text(",".join(verifier.REQUIRED_COLUMNS) + "\n" + row, encoding="utf-8")
                files[axis] = path

            report = verifier.build_report(
                "2026-05-13T00:00:00+09:00",
                files,
                {"status": "READY_FOR_MANUAL_CANONICAL_IMPORT_REVIEW", "ready_rows": []},
                {"status": "PASS_SOURCE_ARTIFACT_REGISTRY_VERIFIED", "passed_registry_row_count": 1, "blockers": []},
                {"status": "PASS_INTAKE_SOURCE_PROVENANCE_VERIFIED", "passed_ready_row_count": 1, "blocked_ready_row_count": 0, "blockers": []},
            )

        self.assertEqual(report["status"], "PASS_MEMBERSHIP_FILES_VERIFIED")
        self.assertTrue(report["all_verified"])
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["axis_reports"][0]["replacement_remaining_count"], 0)
        self.assertEqual(report["axis_reports"][0]["operation_ready_coverage"], 1.0)
        self.assertEqual(report["axis_reports"][0]["evidence_quality_counts"]["authoritative"], 1)
        self.assertEqual(report["next_evidence_acquisition_targets"], [])
        self.assertTrue(report["intake_source_package"]["covers_remaining_replacement"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_caveated_rows_do_not_clear_operation_ready_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            files = {}
            row = "ABC,us_stock,kis_us_stocks,2020-01-01,,2020-01-01,,current_universe_snapshot,snap1,current_snapshot_caveated,test\n"
            for axis in ("kis_us_stocks", "kis_us_etfs", "kis_korea_stocks", "kis_korea_etfs"):
                path = Path(tmp) / f"{axis}.csv"
                path.write_text(",".join(verifier.REQUIRED_COLUMNS) + "\n" + row, encoding="utf-8")
                files[axis] = path

            report = verifier.build_report(
                "2026-05-13T00:00:00+09:00",
                files,
                {
                    "status": "READY_FOR_MANUAL_CANONICAL_IMPORT_REVIEW",
                    "ready_rows": [
                        {"kind": "membership", "axis": "kis_us_stocks"},
                        {"kind": "event_or_no_event", "axis": "kis_us_stocks"},
                        {"kind": "replay", "axis": "policy"},
                    ],
                },
                {"status": "PASS_SOURCE_ARTIFACT_REGISTRY_VERIFIED", "passed_registry_row_count": 1, "blockers": []},
                {"status": "PASS_INTAKE_SOURCE_PROVENANCE_VERIFIED", "passed_ready_row_count": 1, "blocked_ready_row_count": 0, "blockers": []},
            )

        self.assertEqual(report["status"], "PASS_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE")
        self.assertTrue(report["all_schema_verified"])
        self.assertTrue(report["any_caveated_rows"])
        self.assertFalse(report["all_verified"])
        self.assertEqual(report["axis_reports"][0]["replacement_remaining_count"], 1)
        self.assertEqual(report["axis_reports"][0]["operation_ready_coverage"], 0.0)
        self.assertEqual(report["remediation_priority"][0]["replacement_remaining_count"], 1)
        self.assertEqual(report["intake_source_package"]["preflight_ready_rows_by_kind"]["membership"], 1)
        self.assertEqual(report["intake_source_package"]["membership_ready_rows_by_axis"]["kis_us_stocks"], 1)
        self.assertEqual(report["intake_source_package"]["source_verified_coverage_gap"], 3)
        self.assertFalse(report["intake_source_package"]["covers_remaining_replacement"])
        self.assertEqual(report["next_evidence_acquisition_targets"][0]["axis"], "kis_us_etfs")
        self.assertEqual(report["next_evidence_acquisition_targets"][0]["missing_membership_rows"], 1)
        self.assertEqual(report["next_evidence_acquisition_targets"][0]["source_verified_membership_ready_rows"], 0)
        self.assertEqual(report["next_evidence_acquisition_targets"][0]["reason"], "zero_source_verified_membership_rows")
        self.assertEqual(
            report["next_evidence_acquisition_targets"][0]["recommended_source_class"],
            "exchange_official_or_licensed_vendor_pit_membership_history",
        )
        self.assertIn("still-uncovered membership rows", report["single_next_action"])
        self.assertIn("1/4 remaining rows", report["single_next_action"])
        self.assertIn("canonical_membership_evidence_quality_caveated_not_operation_ready", report["blockers"])


if __name__ == "__main__":
    unittest.main()
