from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_pit_intake_source_provenance_verifier.py")
SPEC = importlib.util.spec_from_file_location("build_kis_pit_intake_source_provenance_verifier", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
prov_mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prov_mod
SPEC.loader.exec_module(prov_mod)


class KisPitIntakeSourceProvenanceVerifierTests(unittest.TestCase):
    def ready_row(self, *, source: str, snapshot_id: str, evidence_quality: str = "licensed_vendor") -> dict:
        return {
            "row_number": 2,
            "kind": "membership",
            "symbol": "MU",
            "axis": "kis_us_stocks",
            "row": {
                "source": source,
                "snapshot_id": snapshot_id,
                "evidence_quality": evidence_quality,
                "notes": "reviewed source package",
            },
        }

    def test_blocks_current_state_with_no_ready_rows(self) -> None:
        report = prov_mod.build_report(
            "2026-05-16T10:30:00+09:00",
            preflight={"status": "BLOCK_INTAKE_IMPORT_PREFLIGHT", "ready_rows": [], "blocked_row_count": 18},
            source_artifact_registry={
                "status": "BLOCK_SOURCE_ARTIFACT_REGISTRY",
                "blockers": ["no_ready_rows_to_match_artifacts"],
            },
        )

        self.assertEqual(report["status"], "BLOCK_INTAKE_SOURCE_PROVENANCE")
        self.assertIn("intake_preflight_not_ready", report["blockers"])
        self.assertIn("no_ready_rows_to_verify", report["blockers"])
        self.assertIn("source_artifact_registry_not_verified", report["blockers"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_blocks_generic_placeholder_source_values(self) -> None:
        report = prov_mod.build_report(
            "2026-05-16T10:30:00+09:00",
            preflight={
                "status": "READY_FOR_MANUAL_CANONICAL_IMPORT_REVIEW",
                "ready_rows": [self.ready_row(source="vendor", snapshot_id="snap")],
                "blocked_row_count": 0,
            },
            source_artifact_registry={"status": "PASS_SOURCE_ARTIFACT_REGISTRY_VERIFIED", "blockers": []},
        )

        self.assertEqual(report["status"], "BLOCK_INTAKE_SOURCE_PROVENANCE")
        self.assertIn("source_too_generic", report["blockers"])
        self.assertIn("snapshot_id_too_generic", report["blockers"])

    def test_blocks_rejected_source_markers(self) -> None:
        report = prov_mod.build_report(
            "2026-05-16T10:30:00+09:00",
            preflight={
                "status": "READY_FOR_MANUAL_CANONICAL_IMPORT_REVIEW",
                "ready_rows": [
                    self.ready_row(
                        source="current_snapshot_caveated_universe",
                        snapshot_id="dataset-2026-05-16-v1",
                    )
                ],
                "blocked_row_count": 0,
            },
            source_artifact_registry={"status": "PASS_SOURCE_ARTIFACT_REGISTRY_VERIFIED", "blockers": []},
        )

        self.assertIn("rejected_source_marker_present", report["blockers"])
        self.assertEqual(report["blocked_ready_row_count"], 1)

    def test_passes_specific_operation_ready_source_reference(self) -> None:
        report = prov_mod.build_report(
            "2026-05-16T10:30:00+09:00",
            preflight={
                "status": "READY_FOR_MANUAL_CANONICAL_IMPORT_REVIEW",
                "ready_rows": [
                    self.ready_row(
                        source="licensed_vendor_security_master:example_dataset",
                        snapshot_id="example_dataset_2026-04-30_v3",
                    )
                ],
                "blocked_row_count": 0,
            },
            source_artifact_registry={"status": "PASS_SOURCE_ARTIFACT_REGISTRY_VERIFIED", "blockers": []},
        )

        self.assertEqual(report["status"], "PASS_INTAKE_SOURCE_PROVENANCE_VERIFIED")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["passed_ready_row_count"], 1)

    def test_blocks_specific_source_when_artifact_registry_is_missing(self) -> None:
        report = prov_mod.build_report(
            "2026-05-16T10:30:00+09:00",
            preflight={
                "status": "READY_FOR_MANUAL_CANONICAL_IMPORT_REVIEW",
                "ready_rows": [
                    self.ready_row(
                        source="licensed_vendor_security_master:example_dataset",
                        snapshot_id="example_dataset_2026-04-30_v3",
                    )
                ],
                "blocked_row_count": 0,
            },
            source_artifact_registry={
                "status": "BLOCK_SOURCE_ARTIFACT_REGISTRY",
                "blockers": ["ready_row_source_artifact_not_verified"],
            },
        )

        self.assertEqual(report["status"], "BLOCK_INTAKE_SOURCE_PROVENANCE")
        self.assertIn("source_artifact_registry_not_verified", report["blockers"])
        self.assertIn("ready_row_source_artifact_not_verified", report["blockers"])


if __name__ == "__main__":
    unittest.main()
