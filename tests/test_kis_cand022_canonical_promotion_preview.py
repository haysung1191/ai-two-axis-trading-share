from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_cand022_canonical_promotion_preview.py")
SPEC = importlib.util.spec_from_file_location("build_kis_cand022_canonical_promotion_preview", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
preview_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preview_mod)


class KisCand022CanonicalPromotionPreviewTests(unittest.TestCase):
    def test_incomplete_intake_blocks_without_preview_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            intake_report = {
                "status": "BLOCK_INTAKE_ROWS_INCOMPLETE",
                "templates": {},
            }
            report = preview_mod.build_report("2026-05-14T00:00:00+09:00", intake_report, Path(tmp))

        self.assertEqual(report["status"], "BLOCK_CANONICAL_PROMOTION_PREVIEW")
        self.assertIn("intake_templates_not_ready_for_canonical_review", report["blockers"])
        self.assertIsNone(report["preview"]["membership"])
        self.assertFalse(report["safety"]["live_enabled"])

    def test_ready_intake_with_only_no_event_coverage_creates_no_event_append_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            membership = tmp_path / "membership.csv"
            event = tmp_path / "event.csv"
            replay = tmp_path / "replay.csv"
            self.write_rows(
                membership,
                preview_mod.MEMBERSHIP_CANONICAL_HEADERS + ["target_file", "rebalance_date_to_cover"],
                [
                    {
                        "symbol": "MU",
                        "asset_type": "STOCK",
                        "axis": "kis_us_stocks",
                        "active_from": "2000-01-01",
                        "listed_date": "2000-01-01",
                        "source": "vendor",
                        "snapshot_id": "snap",
                        "evidence_quality": "licensed_vendor",
                    }
                ],
            )
            self.write_rows(
                event,
                preview_mod.EVENT_CANONICAL_HEADERS + ["coverage_start", "coverage_end", "coverage_status", "reviewed_at"],
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
                        "reviewed_at": "2026-05-14",
                    }
                ],
            )
            self.write_rows(
                replay,
                preview_mod.REPLAY_CANONICAL_HEADERS + ["scenario"],
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
                    }
                ],
            )
            report = preview_mod.build_report(
                "2026-05-14T00:00:00+09:00",
                {
                    "status": "READY_TO_COPY_INTAKE_TO_CANONICAL_REVIEW",
                    "templates": {
                        "membership": str(membership),
                        "event": str(event),
                        "replay": str(replay),
                    },
                },
                tmp_path / "preview",
            )

        self.assertEqual(report["status"], "READY_FOR_HUMAN_CANONICAL_APPEND_REVIEW")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["preview"]["membership"]["row_count"], 1)
        self.assertEqual(report["preview"]["event"]["canonical_event_row_count"], 0)
        self.assertEqual(report["preview"]["event"]["source_backed_no_event_coverage_count"], 1)

    def test_ready_intake_with_event_row_creates_append_review_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            membership = tmp_path / "membership.csv"
            event = tmp_path / "event.csv"
            replay = tmp_path / "replay.csv"
            preview_dir = tmp_path / "preview"
            self.write_rows(
                membership,
                preview_mod.MEMBERSHIP_CANONICAL_HEADERS,
                [
                    {
                        "symbol": "MU",
                        "asset_type": "STOCK",
                        "axis": "kis_us_stocks",
                        "active_from": "2000-01-01",
                        "listed_date": "2000-01-01",
                        "source": "vendor",
                        "snapshot_id": "snap",
                        "evidence_quality": "licensed_vendor",
                    }
                ],
            )
            self.write_rows(
                event,
                preview_mod.EVENT_CANONICAL_HEADERS + ["coverage_start", "coverage_end", "coverage_status"],
                [
                    {
                        "symbol": "MU",
                        "axis": "kis_us_stocks",
                        "coverage_start": "2000-01-01",
                        "coverage_end": "2026-04-30",
                        "coverage_status": "event_recorded",
                        "event_type": "ticker_change",
                        "event_date": "2020-01-01",
                        "terminal_price_policy": "successor_mapping",
                        "successor_symbol": "MUN",
                        "source": "vendor",
                        "snapshot_id": "snap",
                        "evidence_quality": "licensed_vendor",
                    }
                ],
            )
            self.write_rows(
                replay,
                preview_mod.REPLAY_CANONICAL_HEADERS + ["scenario"],
                [
                    {
                        "scenario": "ticker_change",
                        "case_id": "case1",
                        "symbol": "MU",
                        "axis": "kis_us_stocks",
                        "event_type": "ticker_change",
                        "event_date": "2020-01-01",
                        "successor_symbol": "MUN",
                        "expected_position_after_event": "1",
                        "expected_cash_after_event": "0",
                        "expected_blocked": "false",
                        "source": "vendor",
                        "snapshot_id": "snap",
                        "evidence_quality": "replay_test_authoritative",
                    }
                ],
            )
            report = preview_mod.build_report(
                "2026-05-14T00:00:00+09:00",
                {
                    "status": "READY_TO_COPY_INTAKE_TO_CANONICAL_REVIEW",
                    "templates": {
                        "membership": str(membership),
                        "event": str(event),
                        "replay": str(replay),
                    },
                },
                preview_dir,
            )
            self.assertTrue((preview_dir / "cand022_delisting_symbol_change_events_to_append.csv").exists())

        self.assertEqual(report["status"], "READY_FOR_HUMAN_CANONICAL_APPEND_REVIEW")
        self.assertEqual(report["blockers"], [])
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def write_rows(self, path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                writer.writerow({header: row.get(header, "") for header in headers})


if __name__ == "__main__":
    unittest.main()
