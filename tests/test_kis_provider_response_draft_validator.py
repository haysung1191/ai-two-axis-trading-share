from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_response_draft_validator.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_response_draft_validator", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
validator_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator_mod)


class KisProviderResponseDraftValidatorTests(unittest.TestCase):
    def test_draft_validator_blocks_blank_source_backed_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_files = self.write_drafts(root, complete=False)
            report = validator_mod.build_report("2026-05-14T01:20:00+09:00", draft_files=draft_files)

        self.assertEqual(report["status"], "BLOCK_PROVIDER_RESPONSE_DRAFT_INCOMPLETE")
        self.assertIn("membership_draft_incomplete_rows", report["blockers"])
        self.assertIn("event_or_no_event_draft_incomplete_rows", report["blockers"])
        self.assertIn("replay_draft_incomplete_rows", report["blockers"])
        self.assertIn("source", report["inspections"]["membership"]["incomplete_rows"][0]["missing_fields"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_draft_validator_allows_complete_rows_for_manual_copy_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_files = self.write_drafts(root, complete=True)
            report = validator_mod.build_report("2026-05-14T01:20:00+09:00", draft_files=draft_files)

        self.assertEqual(report["status"], "READY_TO_COPY_DRAFT_TO_PROVIDER_RESPONSE_REVIEW")
        self.assertEqual(report["blockers"], [])
        self.assertIn("do_not_auto_copy_draft_to_provider_response", report["non_goals"])

    def test_draft_validator_rejects_policy_shortcut_markers_even_when_required_fields_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_files = self.write_drafts(root, complete=True)
            self.write_csv(
                draft_files["membership"],
                ["request_id", "symbol", "axis", "active_from", "listed_date", "source", "snapshot_id", "evidence_quality", "notes"],
                [[
                    "M1",
                    "MU",
                    "kis_us_stocks",
                    "2020-01-01",
                    "2020-01-01",
                    "current_full_market_universe_snapshot",
                    "snap",
                    "authoritative",
                    "current_snapshot_caveated",
                ]],
            )
            report = validator_mod.build_report("2026-05-14T01:20:00+09:00", draft_files=draft_files)

        self.assertEqual(report["status"], "BLOCK_PROVIDER_RESPONSE_DRAFT_INCOMPLETE")
        self.assertIn("membership_draft_rejected_source_marker", report["blockers"])
        rejected = report["inspections"]["membership"]["rejected_source_rows"][0]["rejected_markers"]
        self.assertIn("current_full_market_universe_snapshot", rejected)
        self.assertIn("current_snapshot_caveated", rejected)

    def write_drafts(self, root: Path, complete: bool) -> dict[str, Path]:
        draft_files = {
            "membership": root / "membership.csv",
            "event_or_no_event": root / "event.csv",
            "replay": root / "replay.csv",
        }
        self.write_csv(
            draft_files["membership"],
            ["request_id", "symbol", "axis", "active_from", "listed_date", "source", "snapshot_id", "evidence_quality"],
            [["M1", "MU", "kis_us_stocks", "2020-01-01" if complete else "", "2020-01-01" if complete else "", "source" if complete else "", "snap" if complete else "", "authoritative" if complete else ""]],
        )
        self.write_csv(
            draft_files["event_or_no_event"],
            ["request_id", "symbol", "axis", "coverage_start", "coverage_end", "coverage_status", "source", "snapshot_id", "evidence_quality"],
            [["E1", "MU", "kis_us_stocks", "2020-01-01" if complete else "", "2026-04-30" if complete else "", "no_event_found" if complete else "", "source" if complete else "", "snap" if complete else "", "licensed_vendor" if complete else ""]],
        )
        self.write_csv(
            draft_files["replay"],
            [
                "request_id",
                "scenario",
                "case_id",
                "symbol",
                "axis",
                "event_type",
                "event_date",
                "input_position_before_event",
                "input_price_before_event",
                "successor_symbol",
                "expected_position_after_event",
                "expected_cash_after_event",
                "expected_blocked",
                "source",
                "snapshot_id",
                "evidence_quality",
            ],
            [
                [
                    "R1",
                    "ticker_change",
                    "CASE1" if complete else "",
                    "ABC" if complete else "",
                    "kis_us_stocks" if complete else "",
                    "ticker_change",
                    "2024-01-01" if complete else "",
                    "1" if complete else "",
                    "10" if complete else "",
                    "DEF" if complete else "",
                    "1" if complete else "",
                    "0" if complete else "",
                    "false" if complete else "",
                    "source" if complete else "",
                    "snap" if complete else "",
                    "replay_test_authoritative" if complete else "",
                ]
            ],
        )
        return draft_files

    def write_csv(self, path: Path, headers: list[str], rows: list[list[str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
