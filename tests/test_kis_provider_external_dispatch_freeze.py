from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_external_dispatch_freeze.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_external_dispatch_freeze", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
freeze_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(freeze_mod)


class KisProviderExternalDispatchFreezeTests(unittest.TestCase):
    def test_freeze_copies_dispatch_files_and_verifies_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            freeze_root = root / "freeze"
            source.mkdir()
            email = source / "email.md"
            attachment = source / "handoff.zip"
            manifest_json = source / "manifest.json"
            manifest_md = source / "manifest.md"
            email.write_text(f"email body attachment={attachment}", encoding="utf-8")
            attachment.write_bytes(b"zip bytes")
            manifest_md.write_text("manifest body", encoding="utf-8")
            manifest_json.write_text(
                json.dumps(
                    {
                        "status": "READY_EXTERNAL_DISPATCH_MANIFEST",
                        "tiny_live_completion_decision": "NOT_COMPLETE",
                        "open_rows": 18,
                        "email_markdown": {"path": str(email)},
                        "attachment": {"path": str(attachment)},
                        "return_staging_dir": "returned",
                        "expected_return_files": ["a.csv", "b.csv", "c.csv"],
                    }
                ),
                encoding="utf-8",
            )

            report = freeze_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                "20260514_050000",
                dispatch_manifest_json=manifest_json,
                dispatch_manifest_md=manifest_md,
                freeze_root=freeze_root,
            )

            self.assertEqual(report["status"], "READY_FROZEN_EXTERNAL_DISPATCH_PACKET")
            self.assertEqual(report["blockers"], [])
            self.assertTrue(Path(report["freeze_dir"], "kis_provider_handoff_email_draft.md").exists())
            self.assertTrue(Path(report["freeze_dir"], "handoff.zip").exists())
            self.assertTrue(report["copy_checks"]["email_markdown_attachment_path_normalized"])
            self.assertTrue(report["copy_checks"]["attachment"])
            frozen_email = Path(report["frozen_files"]["email_markdown"]["path"]).read_text(encoding="utf-8-sig")
            self.assertIn(str(Path(report["frozen_files"]["attachment"]["path"])), frozen_email)
            self.assertNotIn(str(attachment), frozen_email)
            self.assertTrue(report["email_attachment_path_normalized"])
            self.assertFalse(report["safety"]["order_intent_created"])
            self.assertIn("does_not_send_email", report["non_goals"])

    def test_freeze_blocks_when_manifest_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_json = root / "manifest.json"
            manifest_md = root / "manifest.md"
            manifest_json.write_text(json.dumps({"status": "BLOCK_EXTERNAL_DISPATCH_MANIFEST"}), encoding="utf-8")
            manifest_md.write_text("manifest body", encoding="utf-8")

            report = freeze_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                "20260514_050000",
                dispatch_manifest_json=manifest_json,
                dispatch_manifest_md=manifest_md,
                freeze_root=root / "freeze",
            )

        self.assertEqual(report["status"], "BLOCK_FROZEN_EXTERNAL_DISPATCH_PACKET")
        self.assertIn("dispatch_manifest_not_ready", report["blockers"])

    def test_freeze_reuses_existing_packet_when_source_hashes_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            freeze_root = root / "freeze"
            source.mkdir()
            email = source / "email.md"
            attachment = source / "handoff.zip"
            manifest_json = source / "manifest.json"
            manifest_md = source / "manifest.md"
            previous = root / "previous.json"
            email.write_text(f"email body attachment={attachment}", encoding="utf-8")
            attachment.write_bytes(b"zip bytes")
            manifest_md.write_text("manifest body", encoding="utf-8")
            manifest_json.write_text(
                json.dumps(
                    {
                        "status": "READY_EXTERNAL_DISPATCH_MANIFEST",
                        "tiny_live_completion_decision": "NOT_COMPLETE",
                        "open_rows": 18,
                        "email_markdown": {"path": str(email)},
                        "attachment": {"path": str(attachment)},
                        "return_staging_dir": "returned",
                        "expected_return_files": ["a.csv", "b.csv", "c.csv"],
                    }
                ),
                encoding="utf-8",
            )
            first = freeze_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                "20260514_050000",
                dispatch_manifest_json=manifest_json,
                dispatch_manifest_md=manifest_md,
                freeze_root=freeze_root,
                previous_report_path=previous,
            )
            previous.write_text(json.dumps(first), encoding="utf-8")
            second = freeze_mod.build_report(
                "2026-05-14T05:01:00+09:00",
                "20260514_050100",
                dispatch_manifest_json=manifest_json,
                dispatch_manifest_md=manifest_md,
                freeze_root=freeze_root,
                previous_report_path=previous,
            )

        self.assertEqual(second["status"], "READY_FROZEN_EXTERNAL_DISPATCH_PACKET")
        self.assertTrue(second["reused_existing_freeze"])
        self.assertEqual(second["freeze_dir"], first["freeze_dir"])

    def test_freeze_does_not_reuse_legacy_packet_without_normalized_email(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            freeze_root = root / "freeze"
            source.mkdir()
            email = source / "email.md"
            attachment = source / "handoff.zip"
            manifest_json = source / "manifest.json"
            manifest_md = source / "manifest.md"
            previous = root / "previous.json"
            email.write_text(f"email body attachment={attachment}", encoding="utf-8")
            attachment.write_bytes(b"zip bytes")
            manifest_md.write_text("manifest body", encoding="utf-8")
            manifest_json.write_text(
                json.dumps(
                    {
                        "status": "READY_EXTERNAL_DISPATCH_MANIFEST",
                        "tiny_live_completion_decision": "NOT_COMPLETE",
                        "open_rows": 18,
                        "email_markdown": {"path": str(email)},
                        "attachment": {"path": str(attachment)},
                        "return_staging_dir": "returned",
                        "expected_return_files": ["a.csv", "b.csv", "c.csv"],
                    }
                ),
                encoding="utf-8",
            )
            legacy = freeze_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                "20260514_050000",
                dispatch_manifest_json=manifest_json,
                dispatch_manifest_md=manifest_md,
                freeze_root=freeze_root,
                previous_report_path=previous,
            )
            legacy.pop("email_attachment_path_normalized", None)
            previous.write_text(json.dumps(legacy), encoding="utf-8")
            second = freeze_mod.build_report(
                "2026-05-14T05:01:00+09:00",
                "20260514_050100",
                dispatch_manifest_json=manifest_json,
                dispatch_manifest_md=manifest_md,
                freeze_root=freeze_root,
                previous_report_path=previous,
            )

        self.assertEqual(second["status"], "READY_FROZEN_EXTERNAL_DISPATCH_PACKET")
        self.assertFalse(second["reused_existing_freeze"])
        self.assertNotEqual(second["freeze_dir"], legacy["freeze_dir"])
        self.assertTrue(second["email_attachment_path_normalized"])


if __name__ == "__main__":
    unittest.main()
