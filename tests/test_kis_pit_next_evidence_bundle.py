from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\apply_kis_pit_next_evidence_bundle.py")
SPEC = importlib.util.spec_from_file_location("apply_kis_pit_next_evidence_bundle", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
bundle_mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = bundle_mod
SPEC.loader.exec_module(bundle_mod)


class KisPitNextEvidenceBundleTests(unittest.TestCase):
    def work_order(self) -> dict:
        return {
            "tasks": [
                {
                    "queue_id": "KIS_SRC_001",
                    "lane": "minimal_cand022_unblock",
                    "evidence_type": "membership_interval",
                    "symbol": "MU",
                    "axis": "kis_us_stocks",
                    "accepted_evidence_quality": "authoritative|exchange_official|licensed_vendor",
                    "intake_row_numbers": [2],
                    "missing_fields": ["active_from", "listed_date", "source", "snapshot_id", "evidence_quality"],
                }
            ]
        }

    def write_template(self, path: Path) -> None:
        headers = ["symbol", "axis", "active_from", "listed_date", "source", "snapshot_id", "evidence_quality", "notes"]
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerow({"symbol": "MU", "axis": "kis_us_stocks"})

    def write_event_template(self, path: Path) -> None:
        headers = [
            "symbol",
            "axis",
            "coverage_start",
            "coverage_end",
            "coverage_status",
            "event_type",
            "event_date",
            "successor_symbol",
            "terminal_price_policy",
            "cash_recovery_ratio",
            "source",
            "snapshot_id",
            "evidence_quality",
            "notes",
        ]
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerow({"symbol": "MU", "axis": "kis_us_stocks"})

    def kwargs(self, artifact: Path) -> dict:
        return {
            "queue_id": "KIS_SRC_001",
            "source": "licensed_vendor_security_master:example_dataset",
            "snapshot_id": "example_dataset_2026-04-30_v3",
            "evidence_quality": "licensed_vendor",
            "artifact_path": str(artifact),
            "active_from": "2000-01-01",
            "listed_date": "2000-01-01",
            "reviewed_at": "2026-05-16",
            "notes": "reviewed",
        }

    def event_work_order(self) -> dict:
        return {
            "tasks": [
                {
                    "queue_id": "KIS_SRC_008",
                    "lane": "minimal_cand022_unblock",
                    "evidence_type": "event_or_no_event_coverage",
                    "symbol": "MU",
                    "axis": "kis_us_stocks",
                    "accepted_evidence_quality": "authoritative|exchange_official|licensed_vendor",
                    "intake_row_numbers": [2],
                    "missing_fields": [
                        "coverage_start",
                        "coverage_end",
                        "coverage_status",
                        "source",
                        "snapshot_id",
                        "evidence_quality",
                    ],
                }
            ]
        }

    def test_default_missing_inputs_blocks_without_mutation(self) -> None:
        report = bundle_mod.build_report(
            "2026-05-16T12:30:00+09:00",
            queue_id="KIS_SRC_001",
            source="",
            snapshot_id="",
            evidence_quality="",
            artifact_path="",
            active_from="",
            listed_date="",
            reviewed_at="",
            notes="",
            apply=False,
            confirmation=None,
            work_order=self.work_order(),
        )

        self.assertEqual(report["status"], "BLOCK_KIS_PIT_NEXT_EVIDENCE_BUNDLE")
        self.assertFalse(report["files_mutated"])
        self.assertIn("registry_update_blocked", report["blockers"])
        self.assertIn("intake_row_update_blocked", report["blockers"])
        self.assertFalse(report["safety"]["live_enabled"])

    def test_dry_run_ready_with_valid_inputs_does_not_mutate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "evidence.csv"
            artifact.write_text("symbol,active_from\nMU,2000-01-01\n", encoding="utf-8")
            registry = root / "registry.csv"
            intake = root / "membership.csv"
            self.write_template(intake)
            with patch.object(bundle_mod.registry_update, "REGISTRY_PATH", registry), patch.object(
                bundle_mod.intake_update, "WORK_ORDER_PATH", root / "unused.json"
            ), patch.dict(bundle_mod.intake_update.INTAKE_FILES_BY_EVIDENCE_TYPE, {"membership_interval": intake}):
                report = bundle_mod.build_report(
                    "2026-05-16T12:30:00+09:00",
                    **self.kwargs(artifact),
                    apply=False,
                    confirmation=None,
                    work_order=self.work_order(),
                )

            self.assertFalse(registry.exists())

        self.assertEqual(report["status"], "DRY_RUN_READY_FOR_KIS_PIT_NEXT_EVIDENCE_BUNDLE")
        self.assertFalse(report["files_mutated"])

    def test_apply_requires_bundle_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "evidence.csv"
            artifact.write_text("symbol,active_from\nMU,2000-01-01\n", encoding="utf-8")
            registry = root / "registry.csv"
            intake = root / "membership.csv"
            self.write_template(intake)
            with patch.object(bundle_mod.registry_update, "REGISTRY_PATH", registry), patch.dict(
                bundle_mod.intake_update.INTAKE_FILES_BY_EVIDENCE_TYPE, {"membership_interval": intake}
            ):
                report = bundle_mod.build_report(
                    "2026-05-16T12:30:00+09:00",
                    **self.kwargs(artifact),
                    apply=True,
                    confirmation="wrong",
                    work_order=self.work_order(),
                )

            self.assertFalse(registry.exists())

        self.assertEqual(report["status"], "BLOCK_KIS_PIT_NEXT_EVIDENCE_BUNDLE")
        self.assertIn("bundle_confirmation_phrase_missing", report["blockers"])

    def test_apply_updates_registry_and_intake_with_bundle_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "evidence.csv"
            artifact.write_text("symbol,active_from\nMU,2000-01-01\n", encoding="utf-8")
            registry = root / "registry.csv"
            intake = root / "membership.csv"
            self.write_template(intake)
            with patch.object(bundle_mod.registry_update, "REGISTRY_PATH", registry), patch.dict(
                bundle_mod.intake_update.INTAKE_FILES_BY_EVIDENCE_TYPE, {"membership_interval": intake}
            ):
                report = bundle_mod.build_report(
                    "2026-05-16T12:30:00+09:00",
                    **self.kwargs(artifact),
                    apply=True,
                    confirmation=bundle_mod.CONFIRMATION_PHRASE,
                    work_order=self.work_order(),
                )
            with registry.open("r", encoding="utf-8-sig", newline="") as f:
                registry_rows = list(csv.DictReader(f))
            with intake.open("r", encoding="utf-8-sig", newline="") as f:
                intake_rows = list(csv.DictReader(f))

        self.assertEqual(report["status"], "APPLIED_KIS_PIT_NEXT_EVIDENCE_BUNDLE")
        self.assertTrue(report["files_mutated"])
        self.assertEqual(registry_rows[0]["source"], "licensed_vendor_security_master:example_dataset")
        self.assertEqual(intake_rows[0]["source"], "licensed_vendor_security_master:example_dataset")
        self.assertEqual(intake_rows[0]["active_from"], "2000-01-01")

    def test_apply_updates_event_coverage_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "evidence.md"
            artifact.write_text("source backed event coverage\n", encoding="utf-8")
            registry = root / "registry.csv"
            event_intake = root / "event.csv"
            self.write_event_template(event_intake)
            with patch.object(bundle_mod.registry_update, "REGISTRY_PATH", registry), patch.dict(
                bundle_mod.intake_update.INTAKE_FILES_BY_EVIDENCE_TYPE,
                {"event_or_no_event_coverage": event_intake},
            ):
                report = bundle_mod.build_report(
                    "2026-05-16T12:30:00+09:00",
                    queue_id="KIS_SRC_008",
                    source="micron_ir_sec_filings_no_event_review",
                    snapshot_id="micron_ir_sec_filings_2026-05-16",
                    evidence_quality="authoritative",
                    artifact_path=str(artifact),
                    active_from="",
                    listed_date="",
                    coverage_start="2024-04-30",
                    coverage_end="2026-04-30",
                    coverage_status="no_event_found",
                    reviewed_at="2026-05-16",
                    notes="reviewed",
                    apply=True,
                    confirmation=bundle_mod.CONFIRMATION_PHRASE,
                    work_order=self.event_work_order(),
                )
            with event_intake.open("r", encoding="utf-8-sig", newline="") as f:
                event_rows = list(csv.DictReader(f))

        self.assertEqual(report["status"], "APPLIED_KIS_PIT_NEXT_EVIDENCE_BUNDLE")
        self.assertEqual(event_rows[0]["coverage_status"], "no_event_found")
        self.assertEqual(event_rows[0]["coverage_start"], "2024-04-30")
        self.assertEqual(event_rows[0]["coverage_end"], "2026-04-30")


if __name__ == "__main__":
    unittest.main()
