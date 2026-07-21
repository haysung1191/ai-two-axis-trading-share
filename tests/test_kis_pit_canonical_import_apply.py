from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\apply_kis_pit_intake_canonical_import.py")
SPEC = importlib.util.spec_from_file_location("apply_kis_pit_intake_canonical_import", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
apply_mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = apply_mod
SPEC.loader.exec_module(apply_mod)


class KisPitCanonicalImportApplyTests(unittest.TestCase):
    def ready_preflight(self, target: str) -> dict:
        row = {
            "symbol": "MU",
            "asset_type": "STOCK",
            "axis": "kis_us_stocks",
            "active_from": "2000-01-01",
            "active_to": "",
            "listed_date": "2000-01-01",
            "delisted_date": "",
            "source": "vendor",
            "snapshot_id": "snap",
            "evidence_quality": "licensed_vendor",
            "notes": "reviewed",
        }
        return {
            "status": "READY_FOR_MANUAL_CANONICAL_IMPORT_REVIEW",
            "ready_row_count": 1,
            "blocked_row_count": 0,
            "copy_plan": [
                {
                    "kind": "membership",
                    "row_number": 2,
                    "symbol": "MU",
                    "axis": "kis_us_stocks",
                    "target_file": target,
                    "action": "append_after_manual_review",
                }
            ],
            "ready_rows": [
                {
                    "row_number": 2,
                    "kind": "membership",
                    "symbol": "MU",
                    "axis": "kis_us_stocks",
                    "target_file": target,
                    "row": row,
                }
            ],
        }

    def passing_provenance(self) -> dict:
        return {"status": "PASS_INTAKE_SOURCE_PROVENANCE_VERIFIED", "blockers": []}

    def test_default_dry_run_does_not_mutate_canonical_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "membership.csv"
            report = apply_mod.build_report(
                "2026-05-16T10:00:00+09:00",
                preflight=self.ready_preflight(str(target)),
                provenance=self.passing_provenance(),
                apply=False,
                confirmation=None,
            )

            self.assertFalse(target.exists())

        self.assertEqual(report["status"], "DRY_RUN_READY_FOR_CANONICAL_IMPORT")
        self.assertFalse(report["canonical_files_mutated"])
        self.assertEqual(report["append_plan"][0]["row_count"], 1)
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_apply_requires_exact_confirmation_phrase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "membership.csv"
            report = apply_mod.build_report(
                "2026-05-16T10:00:00+09:00",
                preflight=self.ready_preflight(str(target)),
                provenance=self.passing_provenance(),
                apply=True,
                confirmation="wrong",
            )

            self.assertFalse(target.exists())

        self.assertEqual(report["status"], "BLOCK_CANONICAL_IMPORT_APPLY")
        self.assertIn("apply_confirmation_phrase_missing", report["blockers"])
        self.assertFalse(report["canonical_files_mutated"])

    def test_apply_with_confirmation_appends_rows_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "membership.csv"
            report = apply_mod.build_report(
                "2026-05-16T10:00:00+09:00",
                preflight=self.ready_preflight(str(target)),
                provenance=self.passing_provenance(),
                apply=True,
                confirmation=apply_mod.APPLY_CONFIRMATION,
            )
            with target.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(report["status"], "APPLIED_CANONICAL_IMPORT_REVIEWED")
        self.assertTrue(report["canonical_files_mutated"])
        self.assertEqual(rows[0]["symbol"], "MU")
        self.assertEqual(rows[0]["evidence_quality"], "licensed_vendor")

    def test_apply_is_idempotent_for_exact_duplicate_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "membership.csv"
            preflight = self.ready_preflight(str(target))
            first = apply_mod.build_report(
                "2026-05-16T10:00:00+09:00",
                preflight=preflight,
                provenance=self.passing_provenance(),
                apply=True,
                confirmation=apply_mod.APPLY_CONFIRMATION,
            )
            second = apply_mod.build_report(
                "2026-05-16T10:01:00+09:00",
                preflight=preflight,
                provenance=self.passing_provenance(),
                apply=True,
                confirmation=apply_mod.APPLY_CONFIRMATION,
            )
            with target.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(first["status"], "APPLIED_CANONICAL_IMPORT_REVIEWED")
        self.assertEqual(second["status"], "APPLIED_CANONICAL_IMPORT_REVIEWED")
        self.assertEqual(len(rows), 1)

    def test_current_blocked_preflight_blocks_import(self) -> None:
        report = apply_mod.build_report(
            "2026-05-16T10:00:00+09:00",
            preflight={"status": "BLOCK_INTAKE_IMPORT_PREFLIGHT", "ready_row_count": 0, "blocked_row_count": 18},
            provenance={"status": "BLOCK_INTAKE_SOURCE_PROVENANCE", "blockers": ["no_ready_rows_to_verify"]},
            apply=False,
            confirmation=None,
        )

        self.assertEqual(report["status"], "BLOCK_CANONICAL_IMPORT_APPLY")
        self.assertIn("intake_preflight_not_ready", report["blockers"])
        self.assertIn("source_provenance_not_verified", report["blockers"])
        self.assertFalse(report["canonical_files_mutated"])

    def test_ready_preflight_still_blocks_without_provenance_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "membership.csv"
            report = apply_mod.build_report(
                "2026-05-16T10:00:00+09:00",
                preflight=self.ready_preflight(str(target)),
                provenance={"status": "BLOCK_INTAKE_SOURCE_PROVENANCE", "blockers": ["source_too_generic"]},
            )

            self.assertFalse(target.exists())

        self.assertEqual(report["status"], "BLOCK_CANONICAL_IMPORT_APPLY")
        self.assertIn("source_provenance_not_verified", report["blockers"])
        self.assertIn("source_too_generic", report["blockers"])


if __name__ == "__main__":
    unittest.main()
