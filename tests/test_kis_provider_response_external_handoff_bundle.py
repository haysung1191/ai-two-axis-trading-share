from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_response_external_handoff_bundle.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_response_external_handoff_bundle", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
bundle_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle_mod)


class KisProviderResponseExternalHandoffBundleTests(unittest.TestCase):
    def test_bundle_copies_sources_and_writes_review_only_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_files = self.write_sources(root)
            handoff_dir = root / "handoff"
            report = bundle_mod.build_report(
                "2026-05-14T02:00:00+09:00",
                handoff_dir=handoff_dir,
                source_files=source_files,
            )
            readme_exists = (handoff_dir / "README.md").exists()
            readme_text = (handoff_dir / "README.md").read_text(encoding="utf-8")
            closure_plan_copied = (handoff_dir / source_files["field_closure_plan_json"].name).exists()

        self.assertEqual(report["status"], "EXTERNAL_HANDOFF_BUNDLE_READY")
        self.assertEqual(report["missing_files"], [])
        self.assertEqual(report["gap_summary"]["total_missing_response_rows"], 18)
        self.assertEqual(report["local_source_summary"]["total_usable_rows"], 0)
        self.assertTrue(closure_plan_copied)
        self.assertIn("kis_provider_response_field_closure_plan_latest.csv", readme_text)
        self.assertTrue(readme_exists)
        self.assertIn("review-only", readme_text)
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_bundle_blocks_when_required_source_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_files = self.write_sources(root)
            source_files["membership_request_csv"].unlink()
            report = bundle_mod.build_report(
                "2026-05-14T02:00:00+09:00",
                handoff_dir=root / "handoff",
                source_files=source_files,
            )

        self.assertEqual(report["status"], "BLOCK_EXTERNAL_HANDOFF_BUNDLE_NEEDS_REVIEW")
        self.assertIn("external_handoff_source_files_missing", report["blockers"])
        self.assertEqual(len(report["missing_files"]), 1)

    def test_bundle_does_not_overwrite_existing_edited_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_files = self.write_sources(root)
            handoff_dir = root / "handoff"
            handoff_dir.mkdir()
            target = handoff_dir / source_files["membership_draft_csv"].name
            target.write_text("provider-edited\n", encoding="utf-8")
            report = bundle_mod.build_report(
                "2026-05-14T02:00:00+09:00",
                handoff_dir=handoff_dir,
                source_files=source_files,
            )
            target_text = target.read_text(encoding="utf-8")

        self.assertEqual(report["status"], "BLOCK_EXTERNAL_HANDOFF_BUNDLE_NEEDS_REVIEW")
        self.assertIn("external_handoff_protected_existing_draft_edits", report["blockers"])
        self.assertEqual(len(report["protected_existing_edits"]), 1)
        self.assertEqual(target_text, "provider-edited\n")

    def write_sources(self, root: Path) -> dict[str, Path]:
        files = {key: root / f"{key}.txt" for key in bundle_mod.SOURCE_FILES}
        for key, path in files.items():
            if key == "gap_matrix_json":
                path.write_text(json.dumps({"status": "BLOCK", "total_missing_response_rows": 18, "missing_counts": {}}), encoding="utf-8")
            elif key == "field_closure_plan_json":
                path.write_text(json.dumps({"status": "BLOCK_PROVIDER_RESPONSE_FIELD_CLOSURE_ROWS_OPEN", "closure_row_count": 18}), encoding="utf-8")
            elif key == "local_source_audit_json":
                path.write_text(json.dumps({"status": "BLOCK", "total_usable_rows": 0, "usable_counts": {}}), encoding="utf-8")
            elif key == "draft_validator_json":
                path.write_text(json.dumps({"status": "BLOCK_PROVIDER_RESPONSE_DRAFT_INCOMPLETE"}), encoding="utf-8")
            else:
                path.write_text("content\n", encoding="utf-8")
        return files


if __name__ == "__main__":
    unittest.main()
