from __future__ import annotations

import csv
import json
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_returned_handoff_staging_verifier.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_returned_handoff_staging_verifier", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
returned_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(returned_mod)


class KisProviderReturnedHandoffStagingVerifierTests(unittest.TestCase):
    def test_blocks_when_returned_dir_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = returned_mod.build_report(
                "2026-05-14T04:15:00+09:00",
                returned_dir=root / "missing",
                handoff_dir=root / "handoff",
                dispatch_confirmation_path=root / "missing_confirmation.json",
                frozen_dispatch_path=root / "missing_freeze.json",
            )

        self.assertEqual(report["status"], "BLOCK_RETURNED_HANDOFF_STAGING")
        self.assertIn("dispatch_sent_confirmation_not_valid", report["blockers"])
        self.assertIn("returned_handoff_dir_missing", report["blockers"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_blocks_when_returned_files_are_ready_but_dispatch_is_unconfirmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "handoff"
            returned = root / "returned"
            handoff.mkdir()
            returned.mkdir()
            for filename, rows in self.complete_rows().items():
                self.write_csv(handoff / filename, rows)
                self.write_csv(returned / filename, rows)
            report = returned_mod.build_report(
                "2026-05-14T04:15:00+09:00",
                returned_dir=returned,
                handoff_dir=handoff,
                dispatch_confirmation_path=root / "missing_confirmation.json",
                frozen_dispatch_path=root / "missing_freeze.json",
            )

        self.assertEqual(report["status"], "BLOCK_RETURNED_HANDOFF_STAGING")
        self.assertIn("dispatch_sent_confirmation_not_valid", report["blockers"])
        self.assertIn("dispatch_sent_confirmation_missing", report["blockers"])
        self.assertTrue(report["request_id_checks"]["membership"]["matches"])

    def test_ready_when_dispatch_confirmed_and_returned_files_match_ids_and_pass_draft_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "handoff"
            returned = root / "returned"
            handoff.mkdir()
            returned.mkdir()
            for filename, rows in self.complete_rows().items():
                self.write_csv(handoff / filename, rows)
                self.write_csv(returned / filename, rows)
            freeze_path, confirmation_path = self.write_valid_dispatch_confirmation(root)
            report = returned_mod.build_report(
                "2026-05-14T04:15:00+09:00",
                returned_dir=returned,
                handoff_dir=handoff,
                dispatch_confirmation_path=confirmation_path,
                frozen_dispatch_path=freeze_path,
            )

        self.assertEqual(report["status"], "READY_RETURNED_HANDOFF_FOR_REVIEW")
        self.assertEqual(report["blockers"], [])
        self.assertTrue(report["dispatch_confirmation_valid"])
        self.assertTrue(report["request_id_checks"]["membership"]["matches"])

    def complete_rows(self) -> dict[str, list[dict[str, str]]]:
        return {
            "cand022_membership_response_draft.csv": [
                {
                    "request_id": "M1",
                    "symbol": "MU",
                    "axis": "kis_us_stocks",
                    "active_from": "2020-01-01",
                    "listed_date": "2020-01-01",
                    "source": "exchange_file",
                    "snapshot_id": "snapshot",
                    "evidence_quality": "exchange_official",
                }
            ],
            "cand022_event_or_no_event_response_draft.csv": [
                {
                    "request_id": "E1",
                    "symbol": "MU",
                    "axis": "kis_us_stocks",
                    "coverage_start": "2020-01-01",
                    "coverage_end": "2026-04-30",
                    "coverage_status": "no_event_found",
                    "source": "exchange_file",
                    "snapshot_id": "snapshot",
                    "evidence_quality": "exchange_official",
                }
            ],
            "cand022_replay_response_draft.csv": [
                {
                    "request_id": "R1",
                    "scenario": "unknown_treatment_block",
                    "case_id": "case1",
                    "symbol": "MU",
                    "axis": "kis_us_stocks",
                    "event_type": "unknown_or_unmapped_corporate_action",
                    "event_date": "2026-01-01",
                    "source": "exchange_file",
                    "snapshot_id": "snapshot",
                    "evidence_quality": "replay_test_authoritative",
                    "input_position_before_event": "1",
                    "input_price_before_event": "100",
                    "expected_blocked": "true",
                }
            ],
        }

    def write_csv(self, path: Path, rows: list[dict[str, str]]) -> None:
        headers = sorted({key for row in rows for key in row})
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    def write_valid_dispatch_confirmation(self, root: Path) -> tuple[Path, Path]:
        freeze_path = root / "freeze.json"
        confirmation_path = root / "confirmation.json"
        freeze = {
            "status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
            "freeze_dir": str(root / "freeze_dir"),
            "expected_return_files": [
                "cand022_membership_response_draft.csv",
                "cand022_event_or_no_event_response_draft.csv",
                "cand022_replay_response_draft.csv",
            ],
            "frozen_files": {
                "email_markdown": {"path": str(root / "email.md"), "sha256": "email-sha"},
                "attachment": {"path": str(root / "packet.zip"), "sha256": "zip-sha"},
            },
        }
        confirmation = {
            "schema_version": "1.0.0",
            "candidate_id": "CAND-022",
            "status": "DISPATCH_SENT",
            "sent_at": "2026-05-14T04:00:00+09:00",
            "sent_by": "operator_account",
            "recipient_or_channel": "provider@example.invalid",
            "freeze_dir": freeze["freeze_dir"],
            "frozen_email_markdown": freeze["frozen_files"]["email_markdown"]["path"],
            "frozen_email_sha256": freeze["frozen_files"]["email_markdown"]["sha256"],
            "frozen_attachment": freeze["frozen_files"]["attachment"]["path"],
            "frozen_attachment_sha256": freeze["frozen_files"]["attachment"]["sha256"],
            "expected_return_files": freeze["expected_return_files"],
            "safety": returned_mod.SAFETY,
        }
        freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
        confirmation_path.write_text(json.dumps(confirmation), encoding="utf-8")
        return freeze_path, confirmation_path


if __name__ == "__main__":
    unittest.main()
