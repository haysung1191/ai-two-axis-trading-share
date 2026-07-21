from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import zipfile
from email import policy
from email.parser import BytesParser
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_provider_dispatch_eml_draft.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_provider_dispatch_eml_draft", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
eml_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(eml_mod)


class Cand022ProviderDispatchEmlDraftTests(unittest.TestCase):
    def test_build_report_writes_local_eml_without_send_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dispatch = root / "dispatch"
            dispatch.mkdir()
            email_md = dispatch / "kis_provider_handoff_email_draft.md"
            attachment = dispatch / "CAND-022_provider_handoff_delivery_latest.zip"
            email_md.write_text("Please fill the attached source-backed rows.\n", encoding="utf-8")
            with zipfile.ZipFile(attachment, "w") as zf:
                zf.writestr("request.csv", "request_id,value\nCAND022_MEMBERSHIP_01,\n")
            slip = root / "slip.json"
            slip.write_text(
                json.dumps(
                    {
                        "status": "READY_MANUAL_DISPATCH_EXECUTION_SLIP",
                        "send_now": {
                            "subject": "CAND-022 source-backed provider response draft request",
                            "email_markdown": str(email_md),
                            "email_sha256": eml_mod.sha256_file(email_md),
                            "attachment": str(attachment),
                            "attachment_sha256": eml_mod.sha256_file(attachment),
                        },
                        "non_goals": ["does_not_send_email"],
                        "safety": eml_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = eml_mod.build_report(
                "2026-05-14T14:30:00+09:00",
                slip_path=slip,
                latest_report=root / "latest.json",
                latest_md=root / "latest.md",
            )

            self.assertEqual(report["status"], "READY_DISPATCH_EML_DRAFT_NO_SEND")
            self.assertEqual(report["blockers"], [])
            self.assertIn("does_not_send_email", report["non_goals"])
            self.assertFalse(report["safety"]["order_intent_created"])
            self.assertTrue(all(report["eml_inspection"]["checks"].values()))
            eml_path = Path(report["eml_draft"])
            self.assertTrue(eml_path.exists())

            msg = BytesParser(policy=policy.default).parsebytes(eml_path.read_bytes())
            self.assertEqual(msg["To"], eml_mod.PLACEHOLDER_TO)
            self.assertEqual(msg["Subject"], "CAND-022 source-backed provider response draft request")
            self.assertEqual(msg["X-CAND-022-Dispatch-Draft"], "NO_SEND_OPERATOR_REVIEW_REQUIRED")
            self.assertEqual(msg["X-CAND-022-Generated-At"], "2026-05-14T14:30:00+09:00")
            self.assertTrue(msg.is_multipart())
            attachments = list(msg.iter_attachments())
            self.assertEqual(len(attachments), 1)
            self.assertEqual(attachments[0].get_filename(), attachment.name)
            self.assertEqual(attachments[0].get_payload(decode=True), attachment.read_bytes())
            md = (root / "latest.md").read_text(encoding="utf-8")
            self.assertIn("EML Inspection", md)
            self.assertIn("attachment_payload_sha256_matches", md)

    def test_hash_mismatch_blocks_eml_creation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            email_md = root / "email.md"
            attachment = root / "handoff.zip"
            email_md.write_text("body\n", encoding="utf-8")
            attachment.write_bytes(b"zip-bytes")
            slip = root / "slip.json"
            slip.write_text(
                json.dumps(
                    {
                        "status": "READY_MANUAL_DISPATCH_EXECUTION_SLIP",
                        "send_now": {
                            "subject": "subject",
                            "email_markdown": str(email_md),
                            "email_sha256": "wrong",
                            "attachment": str(attachment),
                            "attachment_sha256": eml_mod.sha256_file(attachment),
                        },
                        "non_goals": ["does_not_send_email"],
                        "safety": eml_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = eml_mod.build_report(
                "2026-05-14T14:30:00+09:00",
                slip_path=slip,
                latest_report=root / "latest.json",
                latest_md=root / "latest.md",
            )

            self.assertEqual(report["status"], "BLOCK_DISPATCH_EML_DRAFT")
            self.assertIn("email_sha256_mismatch", report["blockers"])
            self.assertFalse(Path(report["eml_draft"]).exists())


if __name__ == "__main__":
    unittest.main()
