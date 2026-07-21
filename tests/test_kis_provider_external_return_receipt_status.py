from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_external_return_receipt_status.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_external_return_receipt_status", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
receipt_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(receipt_mod)


class KisProviderExternalReturnReceiptStatusTests(unittest.TestCase):
    def test_waits_when_frozen_packet_ready_but_returned_files_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            returned = root / "returned"
            returned.mkdir()
            freeze = root / "freeze.json"
            staging = root / "staging.json"
            expected = ["a.csv", "b.csv", "c.csv"]
            freeze.write_text(
                json.dumps(
                    {
                        "status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
                        "return_staging_dir": str(returned),
                        "expected_return_files": expected,
                    }
                ),
                encoding="utf-8",
            )
            staging.write_text(json.dumps({"status": "BLOCK_RETURNED_HANDOFF_STAGING"}), encoding="utf-8")

            report = receipt_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                returned_staging_path=staging,
                send_confirm_path=root / "missing_confirmation.json",
            )

        self.assertEqual(report["status"], "WAITING_FOR_RETURNED_PROVIDER_CSVS")
        self.assertEqual(report["missing_files"], expected)
        self.assertIn("returned_expected_files_missing", report["blockers"])
        self.assertIn("valid dispatch confirmation", report["next_safe_action"])
        self.assertIn("three returned edited CSVs", report["next_safe_action"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_blocks_review_when_returned_files_exist_but_dispatch_is_unconfirmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            returned = root / "returned"
            returned.mkdir()
            expected = ["a.csv", "b.csv", "c.csv"]
            for filename in expected:
                (returned / filename).write_text("request_id\nX\n", encoding="utf-8")
            freeze = root / "freeze.json"
            staging = root / "staging.json"
            freeze.write_text(
                json.dumps(
                    {
                        "status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
                        "return_staging_dir": str(returned),
                        "expected_return_files": expected,
                    }
                ),
                encoding="utf-8",
            )
            staging.write_text(json.dumps({"status": "READY_RETURNED_HANDOFF_FOR_REVIEW"}), encoding="utf-8")

            report = receipt_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                returned_staging_path=staging,
                send_confirm_path=root / "missing_confirmation.json",
            )

        self.assertEqual(report["status"], "RETURNED_PROVIDER_CSVS_PRESENT_BUT_DISPATCH_UNCONFIRMED")
        self.assertIn("dispatch_sent_confirmation_missing", report["blockers"])
        self.assertFalse(report["send_confirmation_valid"])

    def test_ready_when_all_files_exist_staging_verifier_is_ready_and_dispatch_confirmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            returned = root / "returned"
            returned.mkdir()
            expected = ["a.csv", "b.csv", "c.csv"]
            for filename in expected:
                (returned / filename).write_text("request_id\nX\n", encoding="utf-8")
            freeze = root / "freeze.json"
            staging = root / "staging.json"
            confirm = root / "confirmation.json"
            freeze_data = {
                "status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
                "freeze_dir": "freeze_dir",
                "return_staging_dir": str(returned),
                "expected_return_files": expected,
                "frozen_files": {
                    "email_markdown": {"path": "email.md", "sha256": "emailhash"},
                    "attachment": {"path": "handoff.zip", "sha256": "ziphash"},
                },
            }
            freeze.write_text(json.dumps(freeze_data), encoding="utf-8")
            staging.write_text(json.dumps({"status": "READY_RETURNED_HANDOFF_FOR_REVIEW"}), encoding="utf-8")
            confirm.write_text(json.dumps(self.confirmation(freeze_data)), encoding="utf-8")

            report = receipt_mod.build_report(
                "2026-05-14T05:00:00+09:00",
                freeze_path=freeze,
                returned_staging_path=staging,
                send_confirm_path=confirm,
            )

        self.assertEqual(report["status"], "READY_RETURNED_PROVIDER_CSVS_FOR_REVIEW")
        self.assertEqual(report["missing_files"], [])
        self.assertEqual(report["blockers"], [])
        self.assertTrue(report["send_confirmation_valid"])

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
            "safety": receipt_mod.SAFETY,
        }


if __name__ == "__main__":
    unittest.main()
