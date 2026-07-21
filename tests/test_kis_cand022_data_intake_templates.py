from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_cand022_data_intake_templates.py")
SPEC = importlib.util.spec_from_file_location("build_kis_cand022_data_intake_templates", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
intake_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(intake_mod)


class KisCand022DataIntakeTemplatesTests(unittest.TestCase):
    def sample_requirements(self) -> dict:
        return {
            "membership_requirements": [
                {
                    "symbol": "MU",
                    "name": "Micron Technology",
                    "market": "US",
                    "route": "kis_us_stock",
                    "asset_type": "STOCK",
                    "axis": "kis_us_stocks",
                    "target_file": "membership.csv",
                    "rebalance_date_to_cover": "2026-04-30",
                }
            ],
            "delisting_replay_requirements": {
                "scenario_row_requirements": {
                    "ticker_change": {"event_type": "ticker_change"},
                    "unknown_treatment_block": {"event_type": "unknown_or_unmapped_corporate_action"},
                }
            },
        }

    def test_templates_are_created_but_remain_blocked_until_populated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = intake_mod.build_report(
                "2026-05-14T00:00:00+09:00",
                self.sample_requirements(),
                Path(tmp),
            )

        self.assertEqual(report["status"], "BLOCK_INTAKE_ROWS_INCOMPLETE")
        self.assertTrue(report["created"]["membership_template_created"])
        self.assertEqual(report["inspections"]["membership"]["row_count"], 1)
        self.assertEqual(report["inspections"]["replay"]["row_count"], 2)
        self.assertIn("membership_intake_rows_incomplete_or_not_operation_ready", report["blockers"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_complete_rows_are_ready_for_canonical_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            intake_mod.build_report("2026-05-14T00:00:00+09:00", self.sample_requirements(), tmp_path)
            membership_path = tmp_path / "cand022_authoritative_membership_rows_template.csv"
            event_path = tmp_path / "cand022_delisting_event_coverage_template.csv"
            replay_path = tmp_path / "cand022_delisting_replay_cases_template.csv"

            self.write_rows(
                membership_path,
                intake_mod.MEMBERSHIP_HEADERS,
                [
                    {
                        "symbol": "MU",
                        "name": "Micron Technology",
                        "market": "US",
                        "route": "kis_us_stock",
                        "asset_type": "STOCK",
                        "axis": "kis_us_stocks",
                        "target_file": "membership.csv",
                        "rebalance_date_to_cover": "2026-04-30",
                        "active_from": "2000-01-01",
                        "active_to": "",
                        "listed_date": "2000-01-01",
                        "delisted_date": "",
                        "source": "vendor",
                        "snapshot_id": "snap",
                        "evidence_quality": "licensed_vendor",
                        "notes": "test",
                    }
                ],
            )
            self.write_rows(
                event_path,
                intake_mod.EVENT_HEADERS,
                [
                    {
                        "symbol": "MU",
                        "axis": "kis_us_stocks",
                        "coverage_start": "2000-01-01",
                        "coverage_end": "2026-04-30",
                        "coverage_status": "no_event_found",
                        "source": "vendor",
                        "snapshot_id": "snap",
                        "evidence_quality": "licensed_vendor",
                    }
                ],
            )
            self.write_rows(
                replay_path,
                intake_mod.REPLAY_HEADERS,
                [
                    {
                        "scenario": "ticker_change",
                        "case_id": "case1",
                        "symbol": "AAA",
                        "axis": "kis_us_stocks",
                        "event_type": "ticker_change",
                        "event_date": "2020-01-01",
                        "successor_symbol": "BBB",
                        "expected_position_after_event": "1",
                        "expected_cash_after_event": "0",
                        "expected_blocked": "false",
                        "source": "vendor",
                        "snapshot_id": "snap",
                        "evidence_quality": "replay_test_authoritative",
                    },
                    {
                        "scenario": "unknown_treatment_block",
                        "case_id": "case2",
                        "symbol": "CCC",
                        "axis": "kis_us_stocks",
                        "event_type": "unknown_or_unmapped_corporate_action",
                        "event_date": "2020-01-01",
                        "expected_blocked": "true",
                        "source": "vendor",
                        "snapshot_id": "snap",
                        "evidence_quality": "replay_test_authoritative",
                    },
                ],
            )

            report = intake_mod.build_report("2026-05-14T00:00:00+09:00", self.sample_requirements(), tmp_path)

        self.assertEqual(report["status"], "READY_TO_COPY_INTAKE_TO_CANONICAL_REVIEW")
        self.assertEqual(report["blockers"], [])
        self.assertFalse(report["created"]["membership_template_created"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_existing_event_template_gets_coverage_columns_without_losing_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            event_path = tmp_path / "cand022_delisting_event_coverage_template.csv"
            event_path.write_text(
                "symbol,axis,coverage_status,source,snapshot_id,evidence_quality,notes\n"
                "MU,kis_us_stocks,,,,,old template\n",
                encoding="utf-8",
            )
            report = intake_mod.build_report("2026-05-14T00:00:00+09:00", self.sample_requirements(), tmp_path)
            with event_path.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))

        self.assertTrue(report["schema_updated"]["event_template_schema_updated"])
        self.assertEqual(rows[0]["symbol"], "MU")
        self.assertIn("coverage_start", rows[0])
        self.assertIn("coverage_end", rows[0])

    def write_rows(self, path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                writer.writerow({header: row.get(header, "") for header in headers})


if __name__ == "__main__":
    unittest.main()
