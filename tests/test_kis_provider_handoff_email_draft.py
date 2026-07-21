from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_handoff_email_draft.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_handoff_email_draft", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
email_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(email_mod)


class KisProviderHandoffEmailDraftTests(unittest.TestCase):
    def test_email_draft_references_verified_zip_and_open_rows_without_sending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "note.json"
            note.write_text(
                json.dumps(
                    {
                        "status": "PROVIDER_HANDOFF_REQUEST_NOTE_READY",
                        "delivery_zip": "delivery.zip",
                        "open_rows": 18,
                        "open_request_ids_by_kind": {"membership": ["M1"], "event_or_no_event": ["E1"], "replay": ["R1"]},
                    }
                ),
                encoding="utf-8",
            )
            report = email_mod.build_report("2026-05-14T05:00:00+09:00", request_note_path=note)

        self.assertEqual(report["status"], "PROVIDER_HANDOFF_EMAIL_DRAFT_READY")
        self.assertEqual(report["attachments"], ["delivery.zip"])
        self.assertIn("M1", report["body"])
        self.assertIn("does_not_send_email", report["non_goals"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_email_draft_blocks_when_request_note_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "note.json"
            note.write_text(json.dumps({"status": "BLOCK"}), encoding="utf-8")
            report = email_mod.build_report("2026-05-14T05:00:00+09:00", request_note_path=note)

        self.assertEqual(report["status"], "BLOCK_PROVIDER_HANDOFF_EMAIL_DRAFT")
        self.assertIn("provider_handoff_request_note_not_ready", report["blockers"])


if __name__ == "__main__":
    unittest.main()
