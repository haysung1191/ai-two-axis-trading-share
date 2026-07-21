from __future__ import annotations

import csv
import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_pit_source_artifact_registry_verifier.py")
SPEC = importlib.util.spec_from_file_location("build_kis_pit_source_artifact_registry_verifier", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
reg_mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = reg_mod
SPEC.loader.exec_module(reg_mod)


class KisPitSourceArtifactRegistryVerifierTests(unittest.TestCase):
    def ready_preflight(self) -> dict:
        return {
            "status": "READY_FOR_MANUAL_CANONICAL_IMPORT_REVIEW",
            "ready_rows": [
                {
                    "row": {
                        "source": "licensed_vendor_security_master:example_dataset",
                        "snapshot_id": "example_dataset_2026-04-30_v3",
                        "evidence_quality": "licensed_vendor",
                    }
                }
            ],
        }

    def write_registry(self, path: Path, artifact: Path, sha: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=reg_mod.REGISTRY_HEADERS)
            writer.writeheader()
            writer.writerow(
                {
                    "source": "licensed_vendor_security_master:example_dataset",
                    "snapshot_id": "example_dataset_2026-04-30_v3",
                    "evidence_quality": "licensed_vendor",
                    "artifact_path": str(artifact),
                    "sha256": sha,
                    "reviewed_at": "2026-05-16",
                    "notes": "test",
                }
            )

    def test_current_blocked_preflight_creates_registry_template_and_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "registry.csv"
            report = reg_mod.build_report(
                "2026-05-16T11:30:00+09:00",
                preflight={"status": "BLOCK_INTAKE_IMPORT_PREFLIGHT", "ready_rows": []},
                registry_path=registry,
            )

            self.assertTrue(registry.exists())

        self.assertEqual(report["status"], "BLOCK_SOURCE_ARTIFACT_REGISTRY")
        self.assertTrue(report["registry_created"])
        self.assertIn("intake_preflight_not_ready", report["blockers"])
        self.assertIn("no_ready_rows_to_match_artifacts", report["blockers"])

    def test_ready_row_blocks_without_matching_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "registry.csv"
            report = reg_mod.build_report(
                "2026-05-16T11:30:00+09:00",
                preflight=self.ready_preflight(),
                registry_path=registry,
            )

        self.assertIn("ready_row_source_artifact_not_verified", report["blockers"])
        self.assertEqual(report["ready_row_count"], 1)

    def test_passes_when_artifact_hash_matches_ready_row_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "evidence.csv"
            artifact.write_text("symbol,active_from\nMU,2000-01-01\n", encoding="utf-8")
            sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
            registry = root / "registry.csv"
            self.write_registry(registry, artifact, sha)

            report = reg_mod.build_report(
                "2026-05-16T11:30:00+09:00",
                preflight=self.ready_preflight(),
                registry_path=registry,
            )

        self.assertEqual(report["status"], "PASS_SOURCE_ARTIFACT_REGISTRY_VERIFIED")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["passed_registry_row_count"], 1)

    def test_blocks_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "evidence.csv"
            artifact.write_text("symbol,active_from\nMU,2000-01-01\n", encoding="utf-8")
            registry = root / "registry.csv"
            self.write_registry(registry, artifact, "0" * 64)

            report = reg_mod.build_report(
                "2026-05-16T11:30:00+09:00",
                preflight=self.ready_preflight(),
                registry_path=registry,
            )

        self.assertIn("artifact_sha256_mismatch", report["blockers"])
        self.assertIn("ready_row_source_artifact_not_verified", report["blockers"])


if __name__ == "__main__":
    unittest.main()
