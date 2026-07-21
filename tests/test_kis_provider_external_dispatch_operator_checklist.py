from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_external_dispatch_operator_checklist.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_external_dispatch_operator_checklist", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
checklist_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checklist_mod)


class KisProviderExternalDispatchOperatorChecklistTests(unittest.TestCase):
    def test_checklist_surfaces_send_files_confirmation_and_return_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            send_status = root / "send.json"
            receipt = root / "receipt.json"
            freeze.write_text(
                json.dumps(
                    {
                        "status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
                        "freeze_dir": "freeze_dir",
                        "expected_return_files": ["a.csv", "b.csv", "c.csv"],
                        "return_staging_dir": "returned",
                        "frozen_files": {
                            "email_markdown": {"path": "email.md", "sha256": "emailhash"},
                            "attachment": {"path": "handoff.zip", "sha256": "ziphash"},
                        },
                    }
                ),
                encoding="utf-8",
            )
            send_status.write_text(
                json.dumps(
                    {
                        "status": "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION",
                        "send_confirmation_template": "template.json",
                        "send_confirmation_path": "sent.json",
                        "send_confirmation_helper": "write_cand022_dispatch_sent_confirmation.py",
                        "preferred_helper_command": "python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send",
                        "post_confirmation_watch_command": "python .\\run_cand022_provider_return_watch.py --cycles 180",
                        "send_confirmation_present": False,
                        "send_confirmation_valid": False,
                        "send_confirmation_blockers": ["dispatch_sent_confirmation_missing"],
                    }
                ),
                encoding="utf-8",
            )
            receipt.write_text(
                json.dumps(
                    {
                        "status": "WAITING_FOR_RETURNED_PROVIDER_CSVS",
                        "return_staging_dir": "returned",
                        "expected_return_files": ["a.csv", "b.csv", "c.csv"],
                    }
                ),
                encoding="utf-8",
            )

            report = checklist_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                send_status_path=send_status,
                return_receipt_path=receipt,
            )

        self.assertEqual(report["status"], "READY_OPERATOR_SEND_CONFIRMATION_CHECKLIST")
        self.assertEqual(report["send_files"]["attachment"], "handoff.zip")
        self.assertEqual(report["send_confirmation"]["template"], "template.json")
        self.assertEqual(report["send_confirmation"]["helper"], "write_cand022_dispatch_sent_confirmation.py")
        self.assertIn("--i-confirm-actual-send", report["send_confirmation"]["preferred_helper_command"])
        self.assertIn("run_cand022_provider_return_watch.py", report["send_confirmation"]["post_confirmation_watch_command"])
        self.assertEqual(report["expected_return_files"], ["a.csv", "b.csv", "c.csv"])
        self.assertIn("build_kis_provider_returned_to_handoff_copy_review.py", report["after_return"]["copy_review_command"])
        self.assertEqual(
            report["after_return"]["refresh_allowed_only_if_copy_review_status"],
            "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertFalse(report["safety"]["order_intent_created"])
        self.assertIn("does_not_send_email", report["non_goals"])
        self.assertTrue(any("validator can check them against the frozen packet" in step for step in report["operator_steps"]))
        self.assertTrue(any("ISO-8601 sent_at with timezone" in step for step in report["operator_steps"]))
        self.assertTrue(any("preferred_helper_command" in step for step in report["operator_steps"]))
        self.assertTrue(any("post_confirmation_watch_command" in step for step in report["operator_steps"]))
        self.assertTrue(any("copy_review_command before any refresh" in step for step in report["operator_steps"]))
        self.assertTrue(any("READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW" in step for step in report["operator_steps"]))
        self.assertTrue(any("helper preserves" in step and "safety" in step for step in report["operator_steps"]))
        self.assertTrue(any("schema_version" in step and "candidate_id" in step for step in report["operator_steps"]))

        md = checklist_mod.render_md(report)
        self.assertIn("Preferred helper command", md)
        self.assertIn("--i-confirm-actual-send", md)
        self.assertIn("Post-confirmation watcher", md)
        self.assertIn("## After Return", md)
        self.assertIn("First run copy-review", md)
        self.assertIn("READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW", md)
        self.assertIn("BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW", md)

    def test_checklist_blocks_when_frozen_packet_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            send_status = root / "send.json"
            receipt = root / "receipt.json"
            freeze.write_text(json.dumps({"status": "BLOCK"}), encoding="utf-8")
            send_status.write_text(json.dumps({"status": "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION"}), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")

            report = checklist_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                send_status_path=send_status,
                return_receipt_path=receipt,
            )

        self.assertEqual(report["status"], "BLOCK_OPERATOR_SEND_CONFIRMATION_CHECKLIST")
        self.assertIn("frozen_dispatch_packet_not_ready", report["blockers"])

    def test_checklist_remains_ready_when_returns_exist_but_dispatch_unconfirmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            send_status = root / "send.json"
            receipt = root / "receipt.json"
            freeze.write_text(
                json.dumps(
                    {
                        "status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
                        "freeze_dir": "freeze_dir",
                        "expected_return_files": ["a.csv", "b.csv", "c.csv"],
                        "return_staging_dir": "returned",
                        "frozen_files": {
                            "email_markdown": {"path": "email.md", "sha256": "emailhash"},
                            "attachment": {"path": "handoff.zip", "sha256": "ziphash"},
                        },
                    }
                ),
                encoding="utf-8",
            )
            send_status.write_text(
                json.dumps(
                    {
                        "status": "RETURNED_PROVIDER_CSVS_PRESENT_BUT_DISPATCH_UNCONFIRMED",
                        "send_confirmation_template": "template.json",
                        "send_confirmation_path": "sent.json",
                        "send_confirmation_present": False,
                        "send_confirmation_valid": False,
                        "send_confirmation_blockers": ["dispatch_sent_confirmation_missing"],
                    }
                ),
                encoding="utf-8",
            )
            receipt.write_text(
                json.dumps(
                    {
                        "status": "READY_RETURNED_PROVIDER_CSVS_FOR_REVIEW",
                        "return_staging_dir": "returned",
                        "expected_return_files": ["a.csv", "b.csv", "c.csv"],
                    }
                ),
                encoding="utf-8",
            )

            report = checklist_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                send_status_path=send_status,
                return_receipt_path=receipt,
            )

        self.assertEqual(report["status"], "READY_OPERATOR_SEND_CONFIRMATION_CHECKLIST")
        self.assertEqual(report["send_status"], "RETURNED_PROVIDER_CSVS_PRESENT_BUT_DISPATCH_UNCONFIRMED")
        self.assertEqual(report["send_confirmation"]["blockers"], ["dispatch_sent_confirmation_missing"])


if __name__ == "__main__":
    unittest.main()
