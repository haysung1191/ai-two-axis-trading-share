from __future__ import annotations

import csv
import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\update_kis_pit_source_artifact_registry.py")
SPEC = importlib.util.spec_from_file_location("update_kis_pit_source_artifact_registry", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
update_mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = update_mod
SPEC.loader.exec_module(update_mod)


class KisPitSourceArtifactRegistryUpdateTests(unittest.TestCase):
    def valid_args(self, artifact: Path) -> dict:
        return {
            "source": "licensed_vendor_security_master:example_dataset",
            "snapshot_id": "example_dataset_2026-04-30_v3",
            "evidence_quality": "licensed_vendor",
            "artifact_path": str(artifact),
            "reviewed_at": "2026-05-16",
            "notes": "reviewed",
        }

    def test_dry_run_calculates_hash_without_mutating_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "registry.csv"
            artifact = root / "evidence.csv"
            artifact.write_text("symbol,active_from\nMU,2000-01-01\n", encoding="utf-8")
            expected_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
            report = update_mod.build_report(
                "2026-05-16T12:00:00+09:00",
                **self.valid_args(artifact),
                apply=False,
                confirmation=None,
                registry_path=registry,
            )

            self.assertFalse(registry.exists())

        self.assertEqual(report["status"], "DRY_RUN_READY_FOR_SOURCE_ARTIFACT_REGISTRY_UPDATE")
        self.assertFalse(report["registry_file_mutated"])
        self.assertEqual(report["proposed_row"]["sha256"], expected_hash)
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_blocks_generic_source_and_missing_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "registry.csv"
            report = update_mod.build_report(
                "2026-05-16T12:00:00+09:00",
                source="vendor",
                snapshot_id="snap",
                evidence_quality="licensed_vendor",
                artifact_path=str(Path(tmp) / "missing.csv"),
                reviewed_at="2026-05-16",
                notes="",
                apply=False,
                confirmation=None,
                registry_path=registry,
            )

        self.assertEqual(report["status"], "BLOCK_SOURCE_ARTIFACT_REGISTRY_UPDATE")
        self.assertIn("source_too_generic", report["blockers"])
        self.assertIn("snapshot_id_too_generic", report["blockers"])
        self.assertIn("artifact_file_missing", report["blockers"])

    def test_apply_requires_confirmation_phrase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "registry.csv"
            artifact = root / "evidence.csv"
            artifact.write_text("symbol,active_from\nMU,2000-01-01\n", encoding="utf-8")
            expected_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
            report = update_mod.build_report(
                "2026-05-16T12:00:00+09:00",
                **self.valid_args(artifact),
                apply=True,
                confirmation="wrong",
                registry_path=registry,
            )

            self.assertFalse(registry.exists())

        self.assertEqual(report["status"], "BLOCK_SOURCE_ARTIFACT_REGISTRY_UPDATE")
        self.assertIn("confirmation_phrase_missing", report["blockers"])

    def test_apply_writes_registry_row_with_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "registry.csv"
            artifact = root / "evidence.csv"
            artifact.write_text("symbol,active_from\nMU,2000-01-01\n", encoding="utf-8")
            expected_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
            report = update_mod.build_report(
                "2026-05-16T12:00:00+09:00",
                **self.valid_args(artifact),
                apply=True,
                confirmation=update_mod.CONFIRMATION_PHRASE,
                registry_path=registry,
            )
            with registry.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(report["status"], "APPLIED_SOURCE_ARTIFACT_REGISTRY_UPDATE")
        self.assertTrue(report["registry_file_mutated"])
        self.assertEqual(rows[0]["source"], "licensed_vendor_security_master:example_dataset")
        self.assertEqual(rows[0]["sha256"], expected_hash)


if __name__ == "__main__":
    unittest.main()
