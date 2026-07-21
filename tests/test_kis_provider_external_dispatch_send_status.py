from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_external_dispatch_send_status.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_external_dispatch_send_status", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
send_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(send_mod)


class KisProviderExternalDispatchSendStatusTests(unittest.TestCase):
    def test_waits_for_send_confirmation_and_writes_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze.write_text(json.dumps(self.freeze()), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

            self.assertEqual(report["status"], "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION")
            self.assertTrue(template.exists())
            self.assertFalse(confirm.exists())
            template_data = json.loads(template.read_text(encoding="utf-8"))
            self.assertIn("ISO-8601", template_data["notes"])
            self.assertIn("+09:00", template_data["notes"])
            self.assertIn("safety block unchanged", template_data["notes"])
            self.assertFalse(report["send_confirmation_valid"])
            self.assertIn("dispatch_sent_confirmation_missing", report["blockers"])
            self.assertEqual(report["send_confirmation_editable_fields"], ["sent_at", "sent_by", "recipient_or_channel"])
            self.assertIn("write_cand022_dispatch_sent_confirmation.py", report["preferred_helper_command"])
            self.assertIn("--i-confirm-actual-send", report["preferred_helper_command"])
            self.assertIn("write_cand022_dispatch_sent_confirmation.py", report["next_safe_action"])
            self.assertIn("run_cand022_provider_return_watch.py", report["next_safe_action"])
            self.assertIn("run_cand022_provider_return_watch.py", report["post_confirmation_watch_command"])
            self.assertIn("--cycles 180", report["post_confirmation_watch_command"])
            self.assertEqual(report["frozen_email_markdown"], "email.md")
            self.assertEqual(report["frozen_email_sha256"], "emailhash")
            self.assertEqual(report["frozen_attachment"], "handoff.zip")
            self.assertEqual(report["frozen_attachment_sha256"], "ziphash")
            self.assertIn("schema_version", report["send_confirmation_frozen_fields_must_match"])
            self.assertIn("candidate_id", report["send_confirmation_frozen_fields_must_match"])
            self.assertIn("expected_return_files", report["send_confirmation_frozen_fields_must_match"])
            self.assertIn("safety", report["send_confirmation_frozen_fields_must_match"])
            self.assertFalse(report["safety"]["order_intent_created"])

    def test_markdown_surfaces_next_action_and_confirmation_blockers(self) -> None:
        report = {
            "generated_at": "2026-05-14T05:00:00+09:00",
            "candidate_id": "CAND-022",
            "status": "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION",
            "frozen_dispatch_status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
            "frozen_email_markdown": "email.md",
            "frozen_email_sha256": "emailhash",
            "frozen_attachment": "handoff.zip",
            "frozen_attachment_sha256": "ziphash",
            "return_receipt_status": "WAITING_FOR_RETURNED_PROVIDER_CSVS",
            "send_confirmation_present": False,
            "send_confirmation_valid": False,
            "send_confirmation_editable_fields": ["sent_at"],
            "send_confirmation_frozen_fields_must_match": ["schema_version"],
            "next_safe_action": "fill confirmation",
            "send_confirmation_template": "template.json",
            "send_confirmation_helper": "write_cand022_dispatch_sent_confirmation.py",
            "preferred_helper_command": "python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send",
            "post_confirmation_watch_command": "python .\\run_cand022_provider_return_watch.py --cycles 180",
            "send_confirmation_path": "sent.json",
            "blockers": ["dispatch_sent_confirmation_missing"],
            "send_confirmation_blockers": ["dispatch_sent_confirmation_missing"],
            "safety": send_mod.SAFETY,
        }

        md = send_mod.render_md(report)

        self.assertIn("Next safe action", md)
        self.assertIn("fill confirmation", md)
        self.assertIn("Confirmation Blockers", md)
        self.assertIn("dispatch_sent_confirmation_missing", md)
        self.assertIn("Latest confirmation is auto-created: `false`", md)
        self.assertIn("Preferred helper command", md)
        self.assertIn("Post-confirmation watch command", md)
        self.assertIn("Frozen email markdown", md)
        self.assertIn("Frozen attachment sha256", md)
        self.assertIn("run_cand022_provider_return_watch.py", md)
        self.assertIn("--i-confirm-actual-send", md)

    def test_sent_confirmation_waits_for_returned_csvs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(self.confirmation(freeze_data)), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertEqual(report["status"], "DISPATCH_SENT_WAITING_FOR_RETURNED_PROVIDER_CSVS")
        self.assertTrue(report["send_confirmation_valid"])
        self.assertEqual(report["send_confirmation_blockers"], [])

    def test_returned_csvs_do_not_override_missing_dispatch_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze.write_text(json.dumps(self.freeze()), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "READY_RETURNED_PROVIDER_CSVS_FOR_REVIEW"}), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertEqual(report["status"], "RETURNED_PROVIDER_CSVS_PRESENT_BUT_DISPATCH_UNCONFIRMED")
        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("dispatch_sent_confirmation_missing", report["blockers"])
        self.assertIn("dispatch is not confirmed", report["next_safe_action"])
        self.assertIn("before treating returns as review-ready", report["next_safe_action"])
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", report["next_safe_action"])

    def test_returned_csvs_ready_only_after_valid_dispatch_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "READY_RETURNED_PROVIDER_CSVS_FOR_REVIEW"}), encoding="utf-8")
            confirm.write_text(json.dumps(self.confirmation(freeze_data)), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertEqual(report["status"], "RETURNED_PROVIDER_CSVS_READY_FOR_REVIEW")
        self.assertTrue(report["send_confirmation_valid"])

    def test_template_values_do_not_count_as_sent_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(send_mod.build_template(freeze_data)), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertEqual(report["status"], "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION")
        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("sent_at_missing_or_template_value", report["send_confirmation_blockers"])
        self.assertIn("sent_by_missing_or_template_value", report["send_confirmation_blockers"])
        self.assertIn("recipient_or_channel_missing_or_template_value", report["send_confirmation_blockers"])

    def test_confirmation_must_match_frozen_paths_and_expected_returns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            mismatched = self.confirmation(freeze_data)
            mismatched["frozen_email_markdown"] = "other.md"
            mismatched["frozen_attachment"] = "other.zip"
            mismatched["expected_return_files"] = ["a.csv"]
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(mismatched), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("frozen_email_markdown_path_mismatch", report["send_confirmation_blockers"])
        self.assertIn("frozen_attachment_path_mismatch", report["send_confirmation_blockers"])
        self.assertIn("expected_return_files_mismatch", report["send_confirmation_blockers"])

    def test_confirmation_rejects_frozen_attachment_sha256_mismatch_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            invalid = self.confirmation(freeze_data)
            invalid["frozen_attachment_sha256"] = "wronghash"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(invalid), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertEqual(report["status"], "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION")
        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("frozen_attachment_sha256_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("frozen_attachment_path_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("expected_return_files_mismatch", report["send_confirmation_blockers"])

    def test_confirmation_rejects_frozen_email_path_mismatch_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            invalid = self.confirmation(freeze_data)
            invalid["frozen_email_markdown"] = "other.md"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(invalid), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertEqual(report["status"], "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION")
        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("frozen_email_markdown_path_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("frozen_email_sha256_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("expected_return_files_mismatch", report["send_confirmation_blockers"])

    def test_confirmation_rejects_frozen_attachment_path_mismatch_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            invalid = self.confirmation(freeze_data)
            invalid["frozen_attachment"] = "other.zip"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(invalid), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertEqual(report["status"], "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION")
        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("frozen_attachment_path_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("frozen_attachment_sha256_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("expected_return_files_mismatch", report["send_confirmation_blockers"])

    def test_confirmation_rejects_frozen_email_sha256_mismatch_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            invalid = self.confirmation(freeze_data)
            invalid["frozen_email_sha256"] = "wronghash"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(invalid), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertEqual(report["status"], "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION")
        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("frozen_email_sha256_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("frozen_email_markdown_path_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("expected_return_files_mismatch", report["send_confirmation_blockers"])

    def test_confirmation_rejects_expected_return_files_mismatch_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            invalid = self.confirmation(freeze_data)
            invalid["expected_return_files"] = ["unexpected.csv"]
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(invalid), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertEqual(report["status"], "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION")
        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("expected_return_files_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("frozen_email_markdown_path_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("frozen_attachment_path_mismatch", report["send_confirmation_blockers"])

    def test_confirmation_rejects_freeze_dir_mismatch_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            invalid = self.confirmation(freeze_data)
            invalid["freeze_dir"] = "other_freeze_dir"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(invalid), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertEqual(report["status"], "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION")
        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("freeze_dir_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("expected_return_files_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("frozen_attachment_path_mismatch", report["send_confirmation_blockers"])

    def test_confirmation_requires_iso8601_sent_at_with_timezone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            invalid = self.confirmation(freeze_data)
            invalid["sent_at"] = "2026/05/14 05:00"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(invalid), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("sent_at_not_iso8601", report["send_confirmation_blockers"])

    def test_confirmation_requires_sent_at_timezone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            invalid = self.confirmation(freeze_data)
            invalid["sent_at"] = "2026-05-14T05:00:00"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(invalid), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("sent_at_timezone_missing", report["send_confirmation_blockers"])

    def test_confirmation_rejects_future_sent_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            invalid = self.confirmation(freeze_data)
            invalid["sent_at"] = "2026-05-14T06:00:00+09:00"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(invalid), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("sent_at_in_future", report["send_confirmation_blockers"])

    def test_confirmation_requires_safety_invariant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            invalid = self.confirmation(freeze_data)
            invalid["safety"] = dict(send_mod.SAFETY)
            invalid["safety"]["live_enabled"] = True
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(invalid), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("safety_invariant_mismatch", report["send_confirmation_blockers"])

    def test_confirmation_requires_schema_and_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            invalid = self.confirmation(freeze_data)
            invalid["schema_version"] = "9.9.9"
            invalid["candidate_id"] = "CAND-999"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(invalid), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("schema_version_mismatch", report["send_confirmation_blockers"])
        self.assertIn("candidate_id_mismatch", report["send_confirmation_blockers"])

    def test_confirmation_rejects_schema_version_mismatch_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            invalid = self.confirmation(freeze_data)
            invalid["schema_version"] = "9.9.9"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(invalid), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertEqual(report["status"], "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION")
        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("schema_version_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("candidate_id_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("safety_invariant_mismatch", report["send_confirmation_blockers"])

    def test_confirmation_rejects_dispatch_status_mismatch_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            invalid = self.confirmation(freeze_data)
            invalid["status"] = "DRAFT"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(invalid), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertEqual(report["status"], "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION")
        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("dispatch_sent_status_missing", report["send_confirmation_blockers"])
        self.assertNotIn("schema_version_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("candidate_id_mismatch", report["send_confirmation_blockers"])

    def test_confirmation_rejects_candidate_id_mismatch_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            receipt = root / "receipt.json"
            confirm = root / "sent.json"
            template = root / "template.json"
            freeze_data = self.freeze()
            invalid = self.confirmation(freeze_data)
            invalid["candidate_id"] = "CAND-999"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            receipt.write_text(json.dumps({"status": "WAITING_FOR_RETURNED_PROVIDER_CSVS"}), encoding="utf-8")
            confirm.write_text(json.dumps(invalid), encoding="utf-8")

            report = send_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                return_receipt_path=receipt,
                send_confirm_path=confirm,
                send_confirm_template=template,
            )

        self.assertEqual(report["status"], "WAITING_FOR_EXTERNAL_DISPATCH_SEND_CONFIRMATION")
        self.assertFalse(report["send_confirmation_valid"])
        self.assertIn("candidate_id_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("schema_version_mismatch", report["send_confirmation_blockers"])
        self.assertNotIn("dispatch_sent_status_missing", report["send_confirmation_blockers"])

    def freeze(self) -> dict[str, object]:
        return {
            "status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
            "freeze_dir": "freeze_dir",
            "expected_return_files": ["a.csv", "b.csv", "c.csv"],
            "frozen_files": {
                "email_markdown": {"path": "email.md", "sha256": "emailhash"},
                "attachment": {"path": "handoff.zip", "sha256": "ziphash"},
            },
        }

    def confirmation(self, freeze: dict[str, object]) -> dict[str, object]:
        frozen_files = freeze["frozen_files"]  # type: ignore[index]
        return {
            "schema_version": "1.0.0",
            "candidate_id": "CAND-022",
            "status": "DISPATCH_SENT",
            "sent_at": "2026-05-14T05:00:00+09:00",
            "sent_by": "operator_name",
            "recipient_or_channel": "provider@example.test",
            "freeze_dir": freeze["freeze_dir"],
            "frozen_email_markdown": frozen_files["email_markdown"]["path"],  # type: ignore[index]
            "frozen_email_sha256": frozen_files["email_markdown"]["sha256"],  # type: ignore[index]
            "frozen_attachment": frozen_files["attachment"]["path"],  # type: ignore[index]
            "frozen_attachment_sha256": frozen_files["attachment"]["sha256"],  # type: ignore[index]
            "expected_return_files": freeze["expected_return_files"],
            "safety": send_mod.SAFETY,
        }


if __name__ == "__main__":
    unittest.main()
