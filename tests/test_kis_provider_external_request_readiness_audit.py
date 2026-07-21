from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_external_request_readiness_audit.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_external_request_readiness_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_mod)


class KisProviderExternalRequestReadinessAuditTests(unittest.TestCase):
    def test_ready_to_send_when_delivery_note_email_and_staging_are_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            returned_dir = root / "returned"
            returned_dir.mkdir()
            delivery = root / "delivery.json"
            note = root / "note.json"
            email = root / "email.json"
            staging = root / "staging.json"
            progress = root / "progress.json"
            completion = root / "completion.json"
            delivery.write_text(json.dumps({"status": "PASS_PROVIDER_HANDOFF_DELIVERY_VERIFIED"}), encoding="utf-8")
            note.write_text(
                json.dumps({"status": "PROVIDER_HANDOFF_REQUEST_NOTE_READY", "delivery_zip": "handoff.zip"}),
                encoding="utf-8",
            )
            email.write_text(
                json.dumps({"status": "PROVIDER_HANDOFF_EMAIL_DRAFT_READY", "attachments": ["handoff.zip"]}),
                encoding="utf-8",
            )
            staging.write_text(json.dumps({"status": "BLOCK_RETURNED_HANDOFF_STAGING"}), encoding="utf-8")
            progress.write_text(
                json.dumps({"completed_rows": 0, "open_rows": 18, "total_rows": 18, "completion_percent": 0.0}),
                encoding="utf-8",
            )
            completion.write_text(json.dumps({"completion_decision": "NOT_COMPLETE"}), encoding="utf-8")

            report = audit_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                delivery_verifier_path=delivery,
                request_note_path=note,
                email_draft_path=email,
                returned_staging_path=staging,
                fill_progress_path=progress,
                completion_audit_path=completion,
                returned_dir=returned_dir,
            )

        self.assertEqual(report["status"], "READY_TO_SEND_EXTERNAL_SOURCE_BACKED_REQUEST")
        self.assertEqual(report["tiny_live_completion_decision"], "NOT_COMPLETE")
        self.assertTrue(report["does_not_mark_tiny_live_complete"])
        self.assertEqual(report["handoff_progress"]["open_rows"], 18)
        self.assertFalse(report["safety"]["order_intent_created"])
        self.assertIn("does_not_send_email", report["non_goals"])

    def test_blocks_when_email_has_no_attachment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            returned_dir = root / "returned"
            returned_dir.mkdir()
            delivery = root / "delivery.json"
            note = root / "note.json"
            email = root / "email.json"
            staging = root / "staging.json"
            progress = root / "progress.json"
            completion = root / "completion.json"
            delivery.write_text(json.dumps({"status": "PASS_PROVIDER_HANDOFF_DELIVERY_VERIFIED"}), encoding="utf-8")
            note.write_text(
                json.dumps({"status": "PROVIDER_HANDOFF_REQUEST_NOTE_READY", "delivery_zip": "handoff.zip"}),
                encoding="utf-8",
            )
            email.write_text(
                json.dumps({"status": "PROVIDER_HANDOFF_EMAIL_DRAFT_READY", "attachments": []}),
                encoding="utf-8",
            )
            staging.write_text(json.dumps({"status": "BLOCK_RETURNED_HANDOFF_STAGING"}), encoding="utf-8")
            progress.write_text(json.dumps({"open_rows": 18}), encoding="utf-8")
            completion.write_text(json.dumps({"completion_decision": "NOT_COMPLETE"}), encoding="utf-8")

            report = audit_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                delivery_verifier_path=delivery,
                request_note_path=note,
                email_draft_path=email,
                returned_staging_path=staging,
                fill_progress_path=progress,
                completion_audit_path=completion,
                returned_dir=returned_dir,
            )

        self.assertEqual(report["status"], "BLOCK_EXTERNAL_REQUEST_NOT_READY")
        self.assertIn("email_has_attachment", report["blockers"])


if __name__ == "__main__":
    unittest.main()
