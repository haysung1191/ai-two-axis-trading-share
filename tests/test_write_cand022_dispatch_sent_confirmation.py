from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\write_cand022_dispatch_sent_confirmation.py")
SPEC = importlib.util.spec_from_file_location("write_cand022_dispatch_sent_confirmation", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
writer_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(writer_mod)


class WriteCand022DispatchSentConfirmationTests(unittest.TestCase):
    def test_blocks_without_explicit_actual_send_flag_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze_data = self.freeze()
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(self.template(freeze_data)), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=False,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertIn("missing_i_confirm_actual_send_flag", report["blockers"])
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertIn("--i-confirm-actual-send", report["next_safe_action"])
        self.assertEqual(report["after_write_commands"], [])
        self.assertEqual(
            report["planned_after_write_commands"],
            [
                "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120",
            ],
        )

    def test_writes_confirmation_when_actual_send_flag_and_fields_are_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze_data = self.freeze()
            template_data = self.template(freeze_data)
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(template_data), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )
            written = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(report["status"], "WROTE_DISPATCH_SENT_CONFIRMATION")
        self.assertTrue(report["wrote_confirmation"])
        self.assertEqual(written["sent_at"], "2026-05-14T05:00:00+09:00")
        self.assertEqual(written["sent_by"], "operator_name")
        self.assertEqual(written["recipient_or_channel"], "provider@example.test")
        self.assertEqual(written["freeze_dir"], template_data["freeze_dir"])
        self.assertEqual(written["frozen_attachment_sha256"], template_data["frozen_attachment_sha256"])
        self.assertEqual(written["safety"], writer_mod.send_status.SAFETY)
        self.assertIn("run_cand022_provider_return_watch.py", report["next_safe_action"])
        self.assertIn("build_kis_provider_returned_to_handoff_copy_review.py", report["next_safe_action"])
        self.assertIn("READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW", report["next_safe_action"])
        self.assertIn("run_cand022_provider_response_refresh_stack.py", report["next_safe_action"])
        self.assertEqual(
            report["after_write_commands"],
            [
                "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120",
            ],
        )
        self.assertEqual(report["planned_after_write_commands"], report["after_write_commands"])
        self.assertEqual(
            report["post_write_sequence_contract"]["immediate_safe_commands"],
            [
                "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120",
            ],
        )
        self.assertTrue(report["post_write_sequence_contract"]["copy_review_required_before_refresh"])
        self.assertEqual(
            report["post_write_sequence_contract"]["copy_review_command"],
            "python .\\build_kis_provider_returned_to_handoff_copy_review.py",
        )
        self.assertEqual(
            report["post_write_sequence_contract"]["refresh_allowed_only_if_copy_review_status"],
            "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertEqual(
            report["post_write_sequence_contract"]["refresh_forbidden_if_copy_review_status"],
            "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertEqual(
            report["post_write_sequence_contract"]["refresh_command_after_allowed_copy_review"],
            "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120",
        )

    def test_dry_run_validates_without_writing_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze_data = self.freeze()
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(self.template(freeze_data)), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                dry_run=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "DRY_RUN_READY_TO_WRITE_DISPATCH_SENT_CONFIRMATION")
        self.assertTrue(report["dry_run"])
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertIn("Dry run passed", report["next_safe_action"])
        self.assertEqual(report["after_write_commands"], [])
        self.assertEqual(
            report["planned_after_write_commands"],
            [
                "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120",
            ],
        )

    def test_cli_style_write_requires_verified_eml_report_when_supplied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            eml_report = root / "eml.json"
            freeze_data = self.freeze()
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(self.template(freeze_data)), encoding="utf-8")
            eml_report.write_text(json.dumps(self.eml_report()), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                dry_run=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                eml_report_path=eml_report,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "DRY_RUN_READY_TO_WRITE_DISPATCH_SENT_CONFIRMATION")
        self.assertTrue(report["eml_inspection_required"])
        self.assertTrue(report["eml_inspection_ready"])
        self.assertEqual(report["blockers"], [])

    def test_cli_style_write_blocks_when_eml_inspection_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            eml_report = root / "eml.json"
            freeze_data = self.freeze()
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(self.template(freeze_data)), encoding="utf-8")
            bad_eml = self.eml_report()
            bad_eml["eml_inspection"]["checks"]["attachment_payload_sha256_matches"] = False  # type: ignore[index]
            eml_report.write_text(json.dumps(bad_eml), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                eml_report_path=eml_report,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertIn("eml_inspection_not_ready", report["blockers"])

    def test_rejects_existing_confirmation_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze_data = self.freeze()
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(self.template(freeze_data)), encoding="utf-8")
            output.write_text("{}", encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertIn("confirmation_already_exists", report["blockers"])

    def test_rejects_template_when_frozen_metadata_does_not_match_freeze_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze_data = self.freeze()
            template_data = self.template(freeze_data)
            template_data["frozen_attachment_sha256"] = "wronghash"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(template_data), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertTrue(any("frozen_attachment_sha256" in blocker for blocker in report["blockers"]))

    def test_rejects_template_placeholder_sender_or_recipient_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze_data = self.freeze()
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(self.template(freeze_data)), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="operator",
                recipient_or_channel="provider_or_source_backed_data_contact",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertIn("sent_by_missing_or_template_value", report["blockers"])
        self.assertIn("recipient_or_channel_missing_or_template_value", report["blockers"])

    def test_rejects_eml_placeholder_recipient_and_generic_command_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze_data = self.freeze()
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(self.template(freeze_data)), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="<operator_or_account>",
                recipient_or_channel="provider_or_channel_to_fill@example.invalid",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertIn("sent_by_missing_or_template_value", report["blockers"])
        self.assertIn("recipient_or_channel_missing_or_template_value", report["blockers"])

    def test_rejects_future_sent_at_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze_data = self.freeze()
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(self.template(freeze_data)), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:10:01+09:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:05:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertIn("sent_at_in_future", report["blockers"])

    def test_rejects_sent_at_without_timezone_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze_data = self.freeze()
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(self.template(freeze_data)), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertIn("sent_at_timezone_missing", report["blockers"])

    def test_rejects_invalid_sent_at_format_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze_data = self.freeze()
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(self.template(freeze_data)), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="not-a-timestamp",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertIn("sent_at_not_iso8601", report["blockers"])

    def test_rejects_missing_template_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "missing_template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze.write_text(json.dumps(self.freeze()), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertIn("template_missing", report["blockers"])
        self.assertIn("confirmation_not_built", report["blockers"])

    def test_rejects_missing_freeze_packet_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "missing_freeze.json"
            freeze_data = self.freeze()
            template.write_text(json.dumps(self.template(freeze_data)), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertTrue(any("freeze_dir" in blocker for blocker in report["blockers"]))
        self.assertTrue(any("frozen_attachment" in blocker for blocker in report["blockers"]))

    def test_rejects_template_with_mutated_safety_block_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze_data = self.freeze()
            template_data = self.template(freeze_data)
            template_data["safety"] = dict(writer_mod.send_status.SAFETY)
            template_data["safety"]["broker_submit_allowed"] = True
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(template_data), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertIn("safety_invariant_mismatch", report["blockers"])

    def test_rejects_template_with_mutated_expected_return_files_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze_data = self.freeze()
            template_data = self.template(freeze_data)
            template_data["expected_return_files"] = ["wrong.csv"]
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(template_data), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertIn("expected_return_files_mismatch", report["blockers"])

    def test_rejects_template_with_wrong_candidate_id_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze_data = self.freeze()
            template_data = self.template(freeze_data)
            template_data["candidate_id"] = "CAND-999"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(template_data), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertIn("candidate_id_mismatch", report["blockers"])

    def test_rejects_template_with_wrong_dispatch_status_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze_data = self.freeze()
            template_data = self.template(freeze_data)
            template_data["status"] = "READY_TO_SEND"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(template_data), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertIn("dispatch_sent_status_missing", report["blockers"])

    def test_rejects_template_with_wrong_schema_version_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.json"
            output = root / "sent.json"
            freeze = root / "freeze.json"
            freeze_data = self.freeze()
            template_data = self.template(freeze_data)
            template_data["schema_version"] = "0.9.0"
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(template_data), encoding="utf-8")

            report = writer_mod.write_confirmation(
                sent_at="2026-05-14T05:00:00+09:00",
                sent_by="operator_name",
                recipient_or_channel="provider@example.test",
                i_confirm_actual_send=True,
                template_path=template,
                output_path=output,
                freeze_path=freeze,
                generated_at="2026-05-14T05:01:00+09:00",
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_SENT_CONFIRMATION_WRITE")
        self.assertFalse(report["wrote_confirmation"])
        self.assertFalse(output.exists())
        self.assertIn("schema_version_mismatch", report["blockers"])

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

    def template(self, freeze: dict[str, object]) -> dict[str, object]:
        frozen_files = freeze["frozen_files"]  # type: ignore[index]
        return {
            "schema_version": "1.0.0",
            "candidate_id": "CAND-022",
            "status": "DISPATCH_SENT",
            "sent_at": "YYYY-MM-DDTHH:MM:SS+09:00",
            "sent_by": "operator",
            "recipient_or_channel": "provider_or_source_backed_data_contact",
            "freeze_dir": freeze["freeze_dir"],
            "frozen_email_markdown": frozen_files["email_markdown"]["path"],  # type: ignore[index]
            "frozen_email_sha256": frozen_files["email_markdown"]["sha256"],  # type: ignore[index]
            "frozen_attachment": frozen_files["attachment"]["path"],  # type: ignore[index]
            "frozen_attachment_sha256": frozen_files["attachment"]["sha256"],  # type: ignore[index]
            "expected_return_files": freeze["expected_return_files"],
            "safety": writer_mod.send_status.SAFETY,
        }

    def eml_report(self) -> dict[str, object]:
        return {
            "status": "READY_DISPATCH_EML_DRAFT_NO_SEND",
            "blockers": [],
            "eml_inspection": {
                "checks": {
                    "eml_exists": True,
                    "to_placeholder_present": True,
                    "subject_matches": True,
                    "no_send_header_present": True,
                    "generated_at_header_matches": True,
                    "is_multipart": True,
                    "single_attachment_present": True,
                    "attachment_filename_matches": True,
                    "attachment_payload_sha256_matches": True,
                },
                "blockers": [],
            },
            "safety": writer_mod.send_status.SAFETY,
        }


if __name__ == "__main__":
    unittest.main()
