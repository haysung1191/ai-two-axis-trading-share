from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_external_dispatch_instruction_packet.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_external_dispatch_instruction_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
packet_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_mod)


EMAIL_MD = """# Draft

## Subject

CAND-022 source-backed provider response draft request

## Attachments

```json
["mutable_latest.zip"]
```

## Body

```text
Please fill the attached package.

This is a data request only.
```

## Safety

{}
"""


class KisProviderExternalDispatchInstructionPacketTests(unittest.TestCase):
    def test_packet_uses_verified_frozen_attachment_and_extracts_subject_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            email = root / "frozen_email.md"
            presend = root / "presend.json"
            checklist = root / "checklist.json"
            email.write_text(EMAIL_MD, encoding="utf-8")
            presend.write_text(
                json.dumps(
                    {
                        "status": "PASS_PRESEND_ACTIVE_SEND_FILES_VERIFIED",
                        "active_send_files": {
                            "email_markdown": {"path": str(email), "sha256": "emailhash"},
                            "attachment": {
                                "path": "frozen.zip",
                                "sha256": "ziphash",
                                "size_bytes": 123,
                                "exists": True,
                            },
                        },
                        "safety": packet_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            checklist.write_text(
                json.dumps(
                    {
                        "status": "READY_OPERATOR_SEND_CONFIRMATION_CHECKLIST",
                        "send_confirmation": {"template": "template.json", "latest": "sent.json"},
                        "expected_return_files": ["a.csv", "b.csv", "c.csv"],
                        "return_staging_dir": "returned",
                        "safety": packet_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = packet_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                presend_path=presend,
                checklist_path=checklist,
            )

        self.assertEqual(report["status"], "READY_MANUAL_DISPATCH_INSTRUCTION_PACKET")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["email"]["subject"], "CAND-022 source-backed provider response draft request")
        self.assertIn("Please fill the attached package.", report["email"]["body"])
        self.assertEqual(report["attachment_to_send"]["path"], "frozen.zip")
        self.assertEqual(report["confirmation_after_send"]["editable_fields_only"], ["sent_at", "sent_by", "recipient_or_channel"])
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", report["confirmation_after_send"]["preferred_helper_command"])
        self.assertIn("--i-confirm-actual-send", report["confirmation_after_send"]["preferred_helper_command"])
        self.assertIn("--eml-report", report["confirmation_after_send"]["preferred_helper_command"])
        self.assertEqual(
            report["confirmation_after_send"]["eml_report"],
            str(packet_mod.PROVIDER_DISPATCH_EML_DRAFT),
        )
        self.assertIn("run_cand022_provider_return_watch.py", report["confirmation_after_send"]["post_confirmation_watch_command"])
        self.assertEqual(
            report["after_return"]["refresh_allowed_only_if_copy_review_status"],
            "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertIn("build_kis_provider_returned_to_handoff_copy_review.py", report["after_return"]["copy_review_command"])
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", report["next_safe_action"])
        self.assertIn("--i-confirm-actual-send", report["next_safe_action"])
        self.assertIn("READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW", report["next_safe_action"])
        self.assertIn("does_not_send_email", report["non_goals"])

        md = packet_mod.render_md(report)
        self.assertIn("Email markdown:", md)
        self.assertIn("Email sha256: `emailhash`", md)
        self.assertIn("Attachment: `frozen.zip`", md)
        self.assertIn("Attachment sha256: `ziphash`", md)
        self.assertIn("Preferred helper command", md)
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", md)
        self.assertIn("--eml-report", md)
        self.assertIn("run_cand022_provider_return_watch.py", md)
        self.assertIn("## After Return", md)
        self.assertIn("First run copy-review", md)
        self.assertIn("READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW", md)
        self.assertIn("BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW", md)
        self.assertIn("Next safe action", md)
        self.assertIn("--i-confirm-actual-send", md)
        self.assertIn("This is a data request only.", md)

    def test_packet_blocks_when_presend_verifier_is_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            presend = root / "presend.json"
            checklist = root / "checklist.json"
            presend.write_text(
                json.dumps(
                    {
                        "status": "BLOCK_PRESEND_ACTIVE_SEND_FILES",
                        "active_send_files": {},
                        "safety": packet_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            checklist.write_text(
                json.dumps(
                    {
                        "status": "READY_OPERATOR_SEND_CONFIRMATION_CHECKLIST",
                        "safety": packet_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = packet_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                presend_path=presend,
                checklist_path=checklist,
            )

        self.assertEqual(report["status"], "BLOCK_MANUAL_DISPATCH_INSTRUCTION_PACKET")
        self.assertIn("presend_verified", report["blockers"])
        self.assertIn("email_subject_extracted", report["blockers"])
        self.assertIn("attachment_verified", report["blockers"])


if __name__ == "__main__":
    unittest.main()
