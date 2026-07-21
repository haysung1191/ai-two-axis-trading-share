from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\update_kis_pit_intake_row.py")
SPEC = importlib.util.spec_from_file_location("update_kis_pit_intake_row", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
update_mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = update_mod
SPEC.loader.exec_module(update_mod)


class KisPitIntakeRowUpdateTests(unittest.TestCase):
    def sample_work_order(self, target: Path) -> dict:
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

    def write_membership_template(self, path: Path) -> None:
        headers = [
            "symbol",
            "axis",
            "active_from",
            "listed_date",
            "source",
            "snapshot_id",
            "evidence_quality",
            "notes",
        ]
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerow({"symbol": "MU", "axis": "kis_us_stocks"})

    def valid_updates(self) -> dict[str, str]:
        return {
            "active_from": "2000-01-01",
            "listed_date": "2000-01-01",
            "source": "licensed_vendor_security_master:example_dataset",
            "snapshot_id": "example_dataset_2026-04-30_v3",
            "evidence_quality": "licensed_vendor",
            "notes": "reviewed evidence packet",
        }

    def test_dry_run_ready_does_not_mutate_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "membership.csv"
            self.write_membership_template(target)
            with patch.dict(update_mod.INTAKE_FILES_BY_EVIDENCE_TYPE, {"membership_interval": target}):
                report = update_mod.build_report(
                    "2026-05-16T11:00:00+09:00",
                    work_order=self.sample_work_order(target),
                    queue_id="KIS_SRC_001",
                    updates=self.valid_updates(),
                    apply=False,
                    confirmation=None,
                )
            with target.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(report["status"], "DRY_RUN_READY_FOR_INTAKE_ROW_UPDATE")
        self.assertFalse(report["intake_file_mutated"])
        self.assertEqual(rows[0]["active_from"], "")
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_blocks_generic_placeholder_values(self) -> None:
        updates = self.valid_updates()
        updates["source"] = "vendor"
        updates["snapshot_id"] = "snap"
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "membership.csv"
            self.write_membership_template(target)
            with patch.dict(update_mod.INTAKE_FILES_BY_EVIDENCE_TYPE, {"membership_interval": target}):
                report = update_mod.build_report(
                    "2026-05-16T11:00:00+09:00",
                    work_order=self.sample_work_order(target),
                    queue_id="KIS_SRC_001",
                    updates=updates,
                    apply=False,
                    confirmation=None,
                )

        self.assertEqual(report["status"], "BLOCK_INTAKE_ROW_UPDATE")
        self.assertIn("source_too_generic", report["blockers"])
        self.assertIn("snapshot_id_too_generic", report["blockers"])

    def test_apply_requires_confirmation_phrase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "membership.csv"
            self.write_membership_template(target)
            with patch.dict(update_mod.INTAKE_FILES_BY_EVIDENCE_TYPE, {"membership_interval": target}):
                report = update_mod.build_report(
                    "2026-05-16T11:00:00+09:00",
                    work_order=self.sample_work_order(target),
                    queue_id="KIS_SRC_001",
                    updates=self.valid_updates(),
                    apply=True,
                    confirmation="wrong",
                )

        self.assertEqual(report["status"], "BLOCK_INTAKE_ROW_UPDATE")
        self.assertIn("confirmation_phrase_missing", report["blockers"])
        self.assertFalse(report["intake_file_mutated"])

    def test_apply_updates_only_target_row_with_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "membership.csv"
            self.write_membership_template(target)
            with patch.dict(update_mod.INTAKE_FILES_BY_EVIDENCE_TYPE, {"membership_interval": target}):
                report = update_mod.build_report(
                    "2026-05-16T11:00:00+09:00",
                    work_order=self.sample_work_order(target),
                    queue_id="KIS_SRC_001",
                    updates=self.valid_updates(),
                    apply=True,
                    confirmation=update_mod.CONFIRMATION_PHRASE,
                )
            with target.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(report["status"], "APPLIED_INTAKE_ROW_UPDATE")
        self.assertTrue(report["intake_file_mutated"])
        self.assertEqual(rows[0]["source"], "licensed_vendor_security_master:example_dataset")
        self.assertEqual(rows[0]["evidence_quality"], "licensed_vendor")


if __name__ == "__main__":
    unittest.main()
