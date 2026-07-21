from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_handoff_request_note.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_handoff_request_note", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
note_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(note_mod)


class KisProviderHandoffRequestNoteTests(unittest.TestCase):
    def test_request_note_surfaces_verified_zip_and_open_request_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            delivery = root / "delivery.json"
            progress = root / "progress.json"
            closure = root / "closure.json"
            delivery.write_text(
                json.dumps(
                    {
                        "status": "PASS_PROVIDER_HANDOFF_DELIVERY_VERIFIED",
                        "zip_path": "delivery.zip",
                        "verified_file_count": 18,
                        "manifest_file_count": 18,
                    }
                ),
                encoding="utf-8",
            )
            progress.write_text(
                json.dumps(
                    {
                        "completed_rows": 0,
                        "total_rows": 18,
                        "open_rows": 18,
                        "progress_by_kind": {"membership": {"blocked_request_ids": ["M1"]}},
                    }
                ),
                encoding="utf-8",
            )
            closure.write_text(json.dumps({"missing_counts": {"membership": 7}}), encoding="utf-8")
            report = note_mod.build_report(
                "2026-05-14T04:00:00+09:00",
                delivery_verifier_path=delivery,
                fill_progress_path=progress,
                field_closure_path=closure,
            )

        self.assertEqual(report["status"], "PROVIDER_HANDOFF_REQUEST_NOTE_READY")
        self.assertEqual(report["delivery_zip"], "delivery.zip")
        self.assertEqual(report["open_request_ids_by_kind"]["membership"], ["M1"])
        self.assertIn("current snapshot only", report["rejected_shortcuts"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_request_note_blocks_unverified_delivery_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            delivery = root / "delivery.json"
            progress = root / "progress.json"
            closure = root / "closure.json"
            delivery.write_text(json.dumps({"status": "BLOCK"}), encoding="utf-8")
            progress.write_text(json.dumps({"open_rows": 18}), encoding="utf-8")
            closure.write_text(json.dumps({"missing_counts": {}}), encoding="utf-8")
            report = note_mod.build_report(
                "2026-05-14T04:00:00+09:00",
                delivery_verifier_path=delivery,
                fill_progress_path=progress,
                field_closure_path=closure,
            )

        self.assertEqual(report["status"], "BLOCK_PROVIDER_HANDOFF_REQUEST_NOTE")
        self.assertIn("delivery_zip_not_verified", report["blockers"])


if __name__ == "__main__":
    unittest.main()
