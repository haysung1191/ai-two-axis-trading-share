from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_external_presend_verifier.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_external_presend_verifier", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
presend_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(presend_mod)


class KisProviderExternalPresendVerifierTests(unittest.TestCase):
    def test_presend_passes_when_active_files_match_frozen_hashes_and_confirmation_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            email = root / "frozen_email.md"
            attachment = root / "frozen.zip"
            freeze = root / "freeze.json"
            send_status = root / "send_status.json"
            operator = root / "operator.json"
            email.write_text("email body", encoding="utf-8")
            self.write_valid_attachment(attachment)
            email_fp = presend_mod.file_fingerprint(email)
            attachment_fp = presend_mod.file_fingerprint(attachment)
            freeze.write_text(
                json.dumps(
                    {
                        "status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
                        "frozen_files": {
                            "email_markdown": email_fp,
                            "attachment": attachment_fp,
                        },
                    }
                ),
                encoding="utf-8",
            )
            send_status.write_text(
                json.dumps(
                    {
                        "send_confirmation_present": False,
                        "send_confirmation_valid": False,
                        "send_confirmation_path": "sent.json",
                        "send_confirmation_template": "template.json",
                        "send_confirmation_helper": "write_cand022_dispatch_sent_confirmation.py",
                        "preferred_helper_command": "python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send",
                        "send_confirmation_blockers": ["dispatch_sent_confirmation_missing"],
                        "safety": presend_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            operator.write_text(
                json.dumps(
                    {
                        "dispatch_file_policy": {
                            "active_send_source": "frozen_dispatch_packet",
                            "active_email_markdown": str(email),
                            "active_attachment": str(attachment),
                        },
                        "safety": presend_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = presend_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                send_status_path=send_status,
                operator_brief_path=operator,
            )

        self.assertEqual(report["status"], "PASS_PRESEND_ACTIVE_SEND_FILES_VERIFIED")
        self.assertEqual(report["blockers"], [])
        self.assertTrue(report["checks"]["active_email_sha256_matches_frozen"])
        self.assertTrue(report["checks"]["active_attachment_sha256_matches_frozen"])
        self.assertTrue(report["checks"]["active_attachment_zip_readable"])
        self.assertTrue(report["checks"]["active_attachment_expected_entries_present"])
        self.assertEqual(report["active_send_files"]["attachment_zip"]["missing_expected_entries"], [])
        self.assertTrue(report["checks"]["send_confirmation_not_present"])
        self.assertEqual(report["send_confirmation"]["helper"], "write_cand022_dispatch_sent_confirmation.py")
        self.assertIn("--i-confirm-actual-send", report["send_confirmation"]["preferred_helper_command"])
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", report["next_safe_action"])
        self.assertIn("--i-confirm-actual-send", report["next_safe_action"])
        self.assertIn("does_not_send_email", report["non_goals"])

        md = presend_mod.render_md(report)
        self.assertIn("Preferred helper command", md)
        self.assertIn("--i-confirm-actual-send", md)

    def test_presend_blocks_when_operator_points_to_mutable_or_wrong_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frozen_email = root / "frozen_email.md"
            wrong_email = root / "latest_email.md"
            attachment = root / "frozen.zip"
            freeze = root / "freeze.json"
            send_status = root / "send_status.json"
            operator = root / "operator.json"
            frozen_email.write_text("frozen email", encoding="utf-8")
            wrong_email.write_text("latest email", encoding="utf-8")
            self.write_valid_attachment(attachment)
            freeze.write_text(
                json.dumps(
                    {
                        "status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
                        "frozen_files": {
                            "email_markdown": presend_mod.file_fingerprint(frozen_email),
                            "attachment": presend_mod.file_fingerprint(attachment),
                        },
                    }
                ),
                encoding="utf-8",
            )
            send_status.write_text(
                json.dumps(
                    {
                        "send_confirmation_present": False,
                        "send_confirmation_valid": False,
                        "safety": presend_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            operator.write_text(
                json.dumps(
                    {
                        "dispatch_file_policy": {
                            "active_send_source": "dispatch_manifest",
                            "active_email_markdown": str(wrong_email),
                            "active_attachment": str(attachment),
                        },
                        "safety": presend_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = presend_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                send_status_path=send_status,
                operator_brief_path=operator,
            )

        self.assertEqual(report["status"], "BLOCK_PRESEND_ACTIVE_SEND_FILES")
        self.assertIn("operator_brief_uses_frozen_source", report["blockers"])
        self.assertIn("active_email_path_matches_frozen", report["blockers"])
        self.assertIn("active_email_sha256_matches_frozen", report["blockers"])

    def test_presend_blocks_after_dispatch_confirmation_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            email = root / "frozen_email.md"
            attachment = root / "frozen.zip"
            freeze = root / "freeze.json"
            send_status = root / "send_status.json"
            operator = root / "operator.json"
            email.write_text("email body", encoding="utf-8")
            self.write_valid_attachment(attachment)
            freeze.write_text(
                json.dumps(
                    {
                        "status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
                        "frozen_files": {
                            "email_markdown": presend_mod.file_fingerprint(email),
                            "attachment": presend_mod.file_fingerprint(attachment),
                        },
                    }
                ),
                encoding="utf-8",
            )
            send_status.write_text(
                json.dumps(
                    {
                        "send_confirmation_present": True,
                        "send_confirmation_valid": True,
                        "safety": presend_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            operator.write_text(
                json.dumps(
                    {
                        "dispatch_file_policy": {
                            "active_send_source": "frozen_dispatch_packet",
                            "active_email_markdown": str(email),
                            "active_attachment": str(attachment),
                        },
                        "safety": presend_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = presend_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                send_status_path=send_status,
                operator_brief_path=operator,
            )

        self.assertEqual(report["status"], "BLOCK_PRESEND_ACTIVE_SEND_FILES")
        self.assertIn("send_confirmation_not_present", report["blockers"])
        self.assertIn("send_confirmation_not_valid_yet", report["blockers"])
        self.assertIn("dispatch_already_confirmed_not_presend", report["blockers"])

    def test_presend_blocks_when_attachment_zip_is_missing_expected_drafts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            email = root / "frozen_email.md"
            attachment = root / "frozen.zip"
            freeze = root / "freeze.json"
            send_status = root / "send_status.json"
            operator = root / "operator.json"
            email.write_text("email body", encoding="utf-8")
            with zipfile.ZipFile(attachment, "w") as z:
                z.writestr("CAND-022_latest/README.md", "read me")
            freeze.write_text(
                json.dumps(
                    {
                        "status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
                        "frozen_files": {
                            "email_markdown": presend_mod.file_fingerprint(email),
                            "attachment": presend_mod.file_fingerprint(attachment),
                        },
                    }
                ),
                encoding="utf-8",
            )
            send_status.write_text(
                json.dumps(
                    {
                        "send_confirmation_present": False,
                        "send_confirmation_valid": False,
                        "safety": presend_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            operator.write_text(
                json.dumps(
                    {
                        "dispatch_file_policy": {
                            "active_send_source": "frozen_dispatch_packet",
                            "active_email_markdown": str(email),
                            "active_attachment": str(attachment),
                        },
                        "safety": presend_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = presend_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                send_status_path=send_status,
                operator_brief_path=operator,
            )

        self.assertEqual(report["status"], "BLOCK_PRESEND_ACTIVE_SEND_FILES")
        self.assertIn("active_attachment_expected_entries_present", report["blockers"])
        self.assertIn(
            "cand022_membership_response_draft.csv",
            report["active_send_files"]["attachment_zip"]["missing_expected_entries"],
        )

    def write_valid_attachment(self, path: Path) -> None:
        with zipfile.ZipFile(path, "w") as z:
            for entry in presend_mod.EXPECTED_ATTACHMENT_ENTRIES:
                z.writestr(f"CAND-022_latest/{entry}", "ok")


if __name__ == "__main__":
    unittest.main()
