from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_dispatch_confirmation_dry_run_from_eml.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_dispatch_confirmation_dry_run_from_eml", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
dry_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dry_mod)


class Cand022DispatchConfirmationDryRunFromEmlTests(unittest.TestCase):
    def test_dry_run_validates_writer_without_creating_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze = root / "freeze.json"
            template = root / "template.json"
            output = root / "sent.json"
            eml = root / "draft.eml"
            eml.write_bytes(b"Subject: CAND-022 source-backed provider response draft request\r\n\r\nbody")
            freeze_data = {
                "status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
                "freeze_dir": str(root),
                "frozen_files": {
                    "email_markdown": {"path": str(root / "email.md"), "sha256": "emailhash"},
                    "attachment": {"path": str(root / "handoff.zip"), "sha256": "ziphash"},
                },
                "expected_return_files": [
                    "cand022_membership_response_draft.csv",
                    "cand022_event_or_no_event_response_draft.csv",
                    "cand022_replay_response_draft.csv",
                ],
            }
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            template.write_text(json.dumps(dry_mod.writer.send_status.build_template(freeze_data)), encoding="utf-8")
            eml_report = root / "eml.json"
            eml_report.write_text(
                json.dumps(
                    {
                        "status": "READY_DISPATCH_EML_DRAFT_NO_SEND",
                        "eml_draft": str(eml),
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
                        "blockers": [],
                        "safety": dry_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = dry_mod.build_report(
                "2026-05-14T14:30:00+09:00",
                eml_report_path=eml_report,
                latest_report=root / "latest.json",
                latest_md=root / "latest.md",
                template_path=template,
                output_path=output,
                freeze_path=freeze,
            )

            self.assertEqual(report["status"], "READY_DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML")
            self.assertEqual(report["blockers"], [])
            self.assertEqual(report["dry_run_writer_status"], "DRY_RUN_READY_TO_WRITE_DISPATCH_SENT_CONFIRMATION")
            self.assertTrue(all(report["eml_inspection"]["checks"].values()))
            self.assertFalse(report["confirmation_output_exists_after_dry_run"])
            self.assertFalse(output.exists())
            self.assertIn("--i-confirm-actual-send", report["actual_after_send_command_template"])
            self.assertIn("--eml-report", report["actual_after_send_command_template"])
            self.assertIn(str(eml_report), report["actual_after_send_command_template"])
            self.assertTrue(report["dry_run_writer_report"]["eml_inspection_required"])
            self.assertTrue(report["dry_run_writer_report"]["eml_inspection_ready"])
            self.assertIn(
                "run_cand022_provider_return_watch.py",
                report["post_write_sequence_contract"]["watch_command"],
            )
            self.assertIn(
                "build_kis_provider_returned_to_handoff_copy_review.py",
                report["post_write_sequence_contract"]["copy_review_command"],
            )
            self.assertEqual(
                report["post_write_sequence_contract"]["refresh_allowed_only_if_copy_review_status"],
                "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
            )
            self.assertEqual(
                report["post_write_sequence_contract"]["refresh_forbidden_if_copy_review_status"],
                "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
            )
            self.assertIn("does_not_write_dispatch_confirmation", report["non_goals"])

            md = (root / "latest.md").read_text(encoding="utf-8")
            self.assertIn("After Successful Write", md)
            self.assertIn("build_kis_provider_returned_to_handoff_copy_review.py", md)
            self.assertIn("READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW", md)
            self.assertIn("BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW", md)

    def test_blocks_when_eml_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            eml_report = root / "eml.json"
            eml_report.write_text(
                json.dumps(
                    {
                        "status": "READY_DISPATCH_EML_DRAFT_NO_SEND",
                        "eml_draft": str(root / "missing.eml"),
                        "eml_inspection": {"checks": {"eml_exists": False}, "blockers": ["eml_exists"]},
                        "blockers": [],
                        "safety": dry_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = dry_mod.build_report(
                "2026-05-14T14:30:00+09:00",
                eml_report_path=eml_report,
                latest_report=root / "latest.json",
                latest_md=root / "latest.md",
                template_path=root / "template.json",
                output_path=root / "sent.json",
                freeze_path=root / "freeze.json",
            )

            self.assertEqual(report["status"], "BLOCK_DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML")
            self.assertIn("eml_draft_missing", report["blockers"])

    def test_blocks_when_eml_inspection_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            eml = root / "draft.eml"
            eml.write_bytes(b"Subject: CAND-022 source-backed provider response draft request\r\n\r\nbody")
            eml_report = root / "eml.json"
            eml_report.write_text(
                json.dumps(
                    {
                        "status": "READY_DISPATCH_EML_DRAFT_NO_SEND",
                        "eml_draft": str(eml),
                        "blockers": [],
                        "safety": dry_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = dry_mod.build_report(
                "2026-05-14T14:30:00+09:00",
                eml_report_path=eml_report,
                latest_report=root / "latest.json",
                latest_md=root / "latest.md",
                template_path=root / "template.json",
                output_path=root / "sent.json",
                freeze_path=root / "freeze.json",
            )

            self.assertEqual(report["status"], "BLOCK_DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML")
            self.assertIn("eml_inspection_missing", report["blockers"])

    def test_blocks_when_eml_inspection_checks_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            eml = root / "draft.eml"
            eml.write_bytes(b"Subject: CAND-022 source-backed provider response draft request\r\n\r\nbody")
            eml_report = root / "eml.json"
            eml_report.write_text(
                json.dumps(
                    {
                        "status": "READY_DISPATCH_EML_DRAFT_NO_SEND",
                        "eml_draft": str(eml),
                        "eml_inspection": {
                            "checks": {
                                "eml_exists": True,
                                "to_placeholder_present": False,
                            },
                            "blockers": ["to_placeholder_present"],
                        },
                        "blockers": [],
                        "safety": dry_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            report = dry_mod.build_report(
                "2026-05-14T14:30:00+09:00",
                eml_report_path=eml_report,
                latest_report=root / "latest.json",
                latest_md=root / "latest.md",
                template_path=root / "template.json",
                output_path=root / "sent.json",
                freeze_path=root / "freeze.json",
            )

            self.assertEqual(report["status"], "BLOCK_DISPATCH_CONFIRMATION_DRY_RUN_FROM_EML")
            self.assertIn("eml_inspection_checks_failed", report["blockers"])
            self.assertIn("eml_inspection_has_blockers", report["blockers"])


if __name__ == "__main__":
    unittest.main()
