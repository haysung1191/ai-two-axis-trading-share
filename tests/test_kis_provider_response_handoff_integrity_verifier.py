from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_response_handoff_integrity_verifier.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_response_handoff_integrity_verifier", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
verifier_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier_mod)


class KisProviderResponseHandoffIntegrityVerifierTests(unittest.TestCase):
    def test_integrity_passes_when_handoff_files_match_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "handoff"
            handoff.mkdir()
            source_files = {
                "a.csv": root / "source_a.csv",
                "b.json": root / "source_b.json",
            }
            for filename, source in source_files.items():
                source.write_text(f"{filename}\n", encoding="utf-8")
                (handoff / filename).write_text(f"{filename}\n", encoding="utf-8")
            (handoff / "README.md").write_text("review-only\n", encoding="utf-8")
            report = verifier_mod.build_report(
                "2026-05-14T02:10:00+09:00",
                handoff_dir=handoff,
                source_files=source_files,
            )

        self.assertEqual(report["status"], "PASS_EXTERNAL_HANDOFF_INTEGRITY")
        self.assertEqual(report["matched_count"], 2)
        self.assertEqual(report["file_count"], 2)
        self.assertEqual(report["blockers"], [])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_integrity_blocks_stale_handoff_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "handoff"
            handoff.mkdir()
            source_files = {"a.csv": root / "source_a.csv"}
            source_files["a.csv"].write_text("new\n", encoding="utf-8")
            (handoff / "a.csv").write_text("old\n", encoding="utf-8")
            (handoff / "README.md").write_text("review-only\n", encoding="utf-8")
            report = verifier_mod.build_report(
                "2026-05-14T02:10:00+09:00",
                handoff_dir=handoff,
                source_files=source_files,
            )

        self.assertEqual(report["status"], "BLOCK_EXTERNAL_HANDOFF_INTEGRITY")
        self.assertIn("handoff_target_files_stale_or_mismatched", report["blockers"])
        self.assertEqual(len(report["mismatched"]), 1)


if __name__ == "__main__":
    unittest.main()
