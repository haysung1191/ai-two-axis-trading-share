from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_external_dispatch_manifest.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_external_dispatch_manifest", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
manifest_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manifest_mod)


class KisProviderExternalDispatchManifestTests(unittest.TestCase):
    def test_dispatch_manifest_ready_when_email_attachment_matches_verified_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = root / "handoff.zip"
            email_md = root / "email.md"
            readiness = root / "readiness.json"
            email_json = root / "email.json"
            delivery = root / "delivery.json"
            zip_path.write_bytes(b"verified package")
            email_md.write_text("draft body", encoding="utf-8")
            readiness.write_text(
                json.dumps(
                    {
                        "status": "READY_TO_SEND_EXTERNAL_SOURCE_BACKED_REQUEST",
                        "tiny_live_completion_decision": "NOT_COMPLETE",
                    }
                ),
                encoding="utf-8",
            )
            email_json.write_text(
                json.dumps(
                    {
                        "status": "PROVIDER_HANDOFF_EMAIL_DRAFT_READY",
                        "subject": "subject",
                        "attachments": [str(zip_path)],
                        "return_staging_dir": "returned",
                        "open_rows": 18,
                    }
                ),
                encoding="utf-8",
            )
            delivery.write_text(
                json.dumps(
                    {
                        "status": "PASS_PROVIDER_HANDOFF_DELIVERY_VERIFIED",
                        "zip_path": str(zip_path),
                    }
                ),
                encoding="utf-8",
            )

            report = manifest_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                readiness_path=readiness,
                email_draft_json_path=email_json,
                email_draft_md_path=email_md,
                delivery_verifier_path=delivery,
            )

        self.assertEqual(report["status"], "READY_EXTERNAL_DISPATCH_MANIFEST")
        self.assertEqual(report["blockers"], [])
        self.assertTrue(report["attachment"]["exists"])
        self.assertEqual(report["attachment"]["sha256"], "5b365b709602bee45e8db24117a4f631efd738927cd9e85e95f765d6d58d909d")
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertIn("does_not_send_email", report["non_goals"])

    def test_dispatch_manifest_blocks_when_attachment_does_not_match_verified_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = root / "handoff.zip"
            verified_zip = root / "verified.zip"
            email_md = root / "email.md"
            readiness = root / "readiness.json"
            email_json = root / "email.json"
            delivery = root / "delivery.json"
            zip_path.write_bytes(b"wrong package")
            verified_zip.write_bytes(b"verified package")
            email_md.write_text("draft body", encoding="utf-8")
            readiness.write_text(
                json.dumps(
                    {
                        "status": "READY_TO_SEND_EXTERNAL_SOURCE_BACKED_REQUEST",
                        "tiny_live_completion_decision": "NOT_COMPLETE",
                    }
                ),
                encoding="utf-8",
            )
            email_json.write_text(
                json.dumps(
                    {
                        "status": "PROVIDER_HANDOFF_EMAIL_DRAFT_READY",
                        "attachments": [str(zip_path)],
                        "open_rows": 18,
                    }
                ),
                encoding="utf-8",
            )
            delivery.write_text(
                json.dumps(
                    {
                        "status": "PASS_PROVIDER_HANDOFF_DELIVERY_VERIFIED",
                        "zip_path": str(verified_zip),
                    }
                ),
                encoding="utf-8",
            )

            report = manifest_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                readiness_path=readiness,
                email_draft_json_path=email_json,
                email_draft_md_path=email_md,
                delivery_verifier_path=delivery,
            )

        self.assertEqual(report["status"], "BLOCK_EXTERNAL_DISPATCH_MANIFEST")
        self.assertIn("attachment_matches_verified_zip", report["blockers"])


if __name__ == "__main__":
    unittest.main()
