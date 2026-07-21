from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_pit_intake_import_preflight.py")
SPEC = importlib.util.spec_from_file_location("build_kis_pit_intake_import_preflight", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


class KisPitIntakeImportPreflightTests(unittest.TestCase):
    def write_rows(self, path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                writer.writerow({header: row.get(header, "") for header in headers})

    def test_incomplete_templates_block_without_mutating_canonical_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            self.write_rows(
                tmp_path / "cand022_authoritative_membership_rows_template.csv",
                preflight.MEMBERSHIP_HEADERS,
                [{"symbol": "MU", "axis": "kis_us_stocks", "evidence_quality": "current_snapshot_caveated"}],
            )
            self.write_rows(tmp_path / "cand022_delisting_event_coverage_template.csv", preflight.EVENT_HEADERS, [])
            self.write_rows(tmp_path / "cand022_delisting_replay_cases_template.csv", preflight.REPLAY_HEADERS, [])

            report = preflight.build_preflight("2026-05-16T09:30:00+09:00", tmp_path)

        self.assertEqual(report["status"], "BLOCK_INTAKE_IMPORT_PREFLIGHT")
        self.assertFalse(report["canonical_files_mutated"])
        self.assertEqual(report["ready_row_count"], 0)
        self.assertIn("required_fields_missing", report["blockers"])
        self.assertIn("evidence_quality_not_operation_ready", report["blockers"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_ready_rows_create_manual_copy_plan_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            self.write_rows(
                tmp_path / "cand022_authoritative_membership_rows_template.csv",
                preflight.MEMBERSHIP_HEADERS,
                [
                    {
                        "symbol": "MU",
                        "axis": "kis_us_stocks",
                        "rebalance_date_to_cover": "2026-04-30",
                        "active_from": "2000-01-01",
                        "listed_date": "2000-01-01",
                        "source": "vendor",
                        "snapshot_id": "snap1",
                        "evidence_quality": "licensed_vendor",
                    }
                ],
            )
            self.write_rows(
                tmp_path / "cand022_delisting_event_coverage_template.csv",
                preflight.EVENT_HEADERS,
                [
                    {
                        "symbol": "MU",
                        "axis": "kis_us_stocks",
                        "coverage_start": "2000-01-01",
                        "coverage_end": "2026-04-30",
                        "coverage_status": "no_event_found",
                        "source": "vendor",
                        "snapshot_id": "snap1",
                        "evidence_quality": "licensed_vendor",
                    }
                ],
            )
            self.write_rows(
                tmp_path / "cand022_delisting_replay_cases_template.csv",
                preflight.REPLAY_HEADERS,
                [
                    {
                        "scenario": "unknown_treatment_block",
                        "case_id": "case1",
                        "symbol": "MU",
                        "axis": "kis_us_stocks",
                        "event_type": "unknown_or_unmapped_corporate_action",
                        "event_date": "2020-01-01",
                        "expected_blocked": "true",
                        "source": "vendor",
                        "snapshot_id": "snap1",
                        "evidence_quality": "replay_test_authoritative",
                    }
                ],
            )

            report = preflight.build_preflight("2026-05-16T09:30:00+09:00", tmp_path)

        self.assertEqual(report["status"], "READY_FOR_MANUAL_CANONICAL_IMPORT_REVIEW")
        self.assertEqual(report["ready_row_count"], 3)
        self.assertEqual(len(report["ready_rows"]), 3)
        self.assertEqual(report["blocked_row_count"], 0)
        self.assertFalse(report["canonical_files_mutated"])
        self.assertTrue(all(row["action"] == "append_after_manual_review" for row in report["copy_plan"]))
        self.assertFalse(report["safety"]["order_intent_created"])


if __name__ == "__main__":
    unittest.main()
