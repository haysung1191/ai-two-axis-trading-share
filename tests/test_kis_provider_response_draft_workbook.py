from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_response_draft_workbook.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_response_draft_workbook", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
draft_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(draft_mod)


class KisProviderResponseDraftWorkbookTests(unittest.TestCase):
    def test_draft_workbook_prefills_request_identity_without_claiming_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_files = self.write_requests(root)
            draft_files = {
                "membership": root / "draft" / "membership.csv",
                "event_or_no_event": root / "draft" / "event.csv",
                "replay": root / "draft" / "replay.csv",
            }
            report = draft_mod.build_report(
                "2026-05-14T01:10:00+09:00",
                request_files=request_files,
                draft_files=draft_files,
            )
            membership = self.read_rows(draft_files["membership"])
            event = self.read_rows(draft_files["event_or_no_event"])
            replay = self.read_rows(draft_files["replay"])

        self.assertEqual(report["status"], "DRAFT_WORKBOOK_READY_NOT_VALIDATED_DATA")
        self.assertEqual(report["row_counts"], {"membership": 1, "event_or_no_event": 1, "replay": 1})
        self.assertEqual(membership[0]["request_id"], "M1")
        self.assertEqual(membership[0]["symbol"], "MU")
        self.assertEqual(membership[0]["source"], "")
        self.assertEqual(event[0]["coverage_end"], "2026-04-30")
        self.assertEqual(replay[0]["scenario"], "ticker_change")
        self.assertFalse(report["safety"]["order_intent_created"])
        self.assertIn("draft files are not operation-ready evidence", report["non_goals"])

    def write_requests(self, root: Path) -> dict[str, Path]:
        request_files = {
            "membership": root / "membership_request.csv",
            "event_or_no_event": root / "event_request.csv",
            "replay": root / "replay_request.csv",
        }
        self.write_csv(
            request_files["membership"],
            ["request_id", "symbol", "axis", "accepted_evidence_quality", "rebalance_date_to_cover"],
            [["M1", "MU", "kis_us_stocks", "authoritative|licensed_vendor", "2026-04-30"]],
        )
        self.write_csv(
            request_files["event_or_no_event"],
            ["request_id", "symbol", "axis", "accepted_coverage_status", "accepted_evidence_quality"],
            [["E1", "MU", "kis_us_stocks", "event_recorded|no_event_found", "authoritative|licensed_vendor"]],
        )
        self.write_csv(
            request_files["replay"],
            ["request_id", "scenario", "event_type", "required_fields", "accepted_evidence_quality"],
            [["R1", "ticker_change", "ticker_change", "case_id,symbol,successor_symbol", "replay_test_authoritative"]],
        )
        return request_files

    def write_csv(self, path: Path, headers: list[str], rows: list[list[str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

    def read_rows(self, path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))


if __name__ == "__main__":
    unittest.main()
