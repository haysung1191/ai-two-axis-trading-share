from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\apply_kis_axis_wide_membership_import.py")
SPEC = importlib.util.spec_from_file_location("apply_kis_axis_wide_membership_import", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
import_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(import_mod)


class KisAxisWideMembershipImportTests(unittest.TestCase):
    def ready_validator(self) -> dict:
        return {
            "status": "READY_AXIS_WIDE_MEMBERSHIP_IMPORT_REVIEW",
            "valid_row_count": 1,
            "blocked_row_count": 0,
            "valid_rows": [
                {
                    "request_id": "KIS_AXIS_001",
                    "axis": "kis_us_stocks",
                    "symbol": "ABC",
                    "row": {
                        "request_id": "KIS_AXIS_001",
                        "axis": "kis_us_stocks",
                        "symbol": "ABC",
                        "asset_type": "STOCK",
                        "active_from": "2000-01-01",
                        "active_to": "",
                        "listed_date": "2000-01-01",
                        "delisted_date": "",
                        "source": "licensed_vendor_security_master:dataset",
                        "snapshot_id": "snap_20260516",
                        "evidence_quality": "licensed_vendor",
                        "notes": "reviewed",
                    },
                }
            ],
            "blockers": [],
        }

    def ready_package(self, target: str) -> dict:
        return {
            "status": "READY_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE",
            "request_rows": [
                {
                    "request_id": "KIS_AXIS_001",
                    "axis": "kis_us_stocks",
                    "canonical_target_file": target,
                }
            ],
        }

    def test_dry_run_ready_does_not_mutate_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "membership.csv"
            report = import_mod.build_report(
                "2026-05-16T12:00:00+09:00",
                validator=self.ready_validator(),
                package=self.ready_package(str(target)),
                apply=False,
            )

            self.assertFalse(target.exists())

        self.assertEqual(report["status"], "DRY_RUN_READY_FOR_AXIS_WIDE_MEMBERSHIP_IMPORT")
        self.assertFalse(report["canonical_files_mutated"])
        self.assertEqual(report["append_plan"][0]["row_count"], 1)
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_apply_requires_confirmation_phrase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "membership.csv"
            report = import_mod.build_report(
                "2026-05-16T12:00:00+09:00",
                validator=self.ready_validator(),
                package=self.ready_package(str(target)),
                apply=True,
                confirmation="wrong",
            )

            self.assertFalse(target.exists())

        self.assertEqual(report["status"], "BLOCK_AXIS_WIDE_MEMBERSHIP_IMPORT")
        self.assertIn("apply_confirmation_phrase_missing", report["blockers"])

    def test_apply_with_confirmation_appends_valid_rows_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "membership.csv"
            report = import_mod.build_report(
                "2026-05-16T12:00:00+09:00",
                validator=self.ready_validator(),
                package=self.ready_package(str(target)),
                apply=True,
                confirmation=import_mod.APPLY_CONFIRMATION,
            )
            with target.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(report["status"], "APPLIED_AXIS_WIDE_MEMBERSHIP_IMPORT_REVIEWED")
        self.assertTrue(report["canonical_files_mutated"])
        self.assertEqual(report["append_plan"][0]["appended_row_count"], 1)
        self.assertEqual(rows[0]["symbol"], "ABC")
        self.assertEqual(rows[0]["evidence_quality"], "licensed_vendor")

    def test_apply_is_idempotent_for_exact_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "membership.csv"
            validator = self.ready_validator()
            package = self.ready_package(str(target))
            first = import_mod.build_report(
                "2026-05-16T12:00:00+09:00",
                validator=validator,
                package=package,
                apply=True,
                confirmation=import_mod.APPLY_CONFIRMATION,
            )
            second = import_mod.build_report(
                "2026-05-16T12:01:00+09:00",
                validator=validator,
                package=package,
                apply=True,
                confirmation=import_mod.APPLY_CONFIRMATION,
            )
            with target.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(first["append_plan"][0]["appended_row_count"], 1)
        self.assertEqual(second["append_plan"][0]["appended_row_count"], 0)
        self.assertEqual(len(rows), 1)

    def test_replace_caveated_blocks_when_replacement_rows_are_insufficient(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "membership.csv"
            with target.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=import_mod.MEMBERSHIP_CANONICAL_HEADERS)
                writer.writeheader()
                writer.writerow(
                    {
                        "symbol": "OLD1",
                        "asset_type": "STOCK",
                        "axis": "kis_us_stocks",
                        "active_from": "2000-01-01",
                        "active_to": "",
                        "listed_date": "",
                        "delisted_date": "",
                        "source": "current_snapshot",
                        "snapshot_id": "old",
                        "evidence_quality": "current_snapshot_caveated",
                        "notes": "",
                    }
                )
                writer.writerow(
                    {
                        "symbol": "OLD2",
                        "asset_type": "STOCK",
                        "axis": "kis_us_stocks",
                        "active_from": "2000-01-01",
                        "active_to": "",
                        "listed_date": "",
                        "delisted_date": "",
                        "source": "current_snapshot",
                        "snapshot_id": "old",
                        "evidence_quality": "current_snapshot_caveated",
                        "notes": "",
                    }
                )

            report = import_mod.build_report(
                "2026-05-16T12:00:00+09:00",
                validator=self.ready_validator(),
                package=self.ready_package(str(target)),
                apply=True,
                confirmation=import_mod.APPLY_CONFIRMATION,
                replace_caveated_axis=True,
            )
            with target.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(report["status"], "BLOCK_AXIS_WIDE_MEMBERSHIP_IMPORT")
        self.assertTrue(report["replace_caveated_axis"])
        self.assertIn("replacement_rows_less_than_caveated_rows:", " ".join(report["blockers"]))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["evidence_quality"], "current_snapshot_caveated")

    def test_replace_caveated_with_confirmation_removes_caveated_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "membership.csv"
            with target.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=import_mod.MEMBERSHIP_CANONICAL_HEADERS)
                writer.writeheader()
                writer.writerow(
                    {
                        "symbol": "KEEP",
                        "asset_type": "STOCK",
                        "axis": "kis_us_stocks",
                        "active_from": "1999-01-01",
                        "active_to": "",
                        "listed_date": "1999-01-01",
                        "delisted_date": "",
                        "source": "licensed_vendor_security_master:dataset",
                        "snapshot_id": "snap_keep",
                        "evidence_quality": "licensed_vendor",
                        "notes": "already reviewed",
                    }
                )
                for symbol in ["OLD1", "OLD2"]:
                    writer.writerow(
                        {
                            "symbol": symbol,
                            "asset_type": "STOCK",
                            "axis": "kis_us_stocks",
                            "active_from": "2000-01-01",
                            "active_to": "",
                            "listed_date": "",
                            "delisted_date": "",
                            "source": "current_snapshot",
                            "snapshot_id": "old",
                            "evidence_quality": "current_snapshot_caveated",
                            "notes": "",
                        }
                    )
            validator = self.ready_validator()
            second_valid = dict(validator["valid_rows"][0])
            second_valid["symbol"] = "DEF"
            second_valid["row"] = dict(second_valid["row"])
            second_valid["row"]["symbol"] = "DEF"
            validator["valid_rows"].append(second_valid)
            validator["valid_row_count"] = 2

            report = import_mod.build_report(
                "2026-05-16T12:00:00+09:00",
                validator=validator,
                package=self.ready_package(str(target)),
                apply=True,
                confirmation=import_mod.APPLY_CONFIRMATION,
                replace_caveated_axis=True,
            )
            with target.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(report["status"], "APPLIED_AXIS_WIDE_MEMBERSHIP_REPLACE_CAVEATED_IMPORT_REVIEWED")
        self.assertTrue(report["canonical_files_mutated"])
        self.assertEqual(report["append_plan"][0]["removed_caveated_row_count"], 2)
        self.assertEqual({row["symbol"] for row in rows}, {"KEEP", "ABC", "DEF"})
        self.assertNotIn("current_snapshot_caveated", {row["evidence_quality"] for row in rows})

    def test_blocks_when_validator_not_ready(self) -> None:
        report = import_mod.build_report(
            "2026-05-16T12:00:00+09:00",
            validator={
                "status": "BLOCK_AXIS_WIDE_MEMBERSHIP_RESPONSE",
                "valid_row_count": 0,
                "blocked_row_count": 4,
                "valid_rows": [],
                "blockers": ["no_valid_axis_membership_rows"],
            },
            package={"status": "READY_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE", "request_rows": []},
        )

        self.assertEqual(report["status"], "BLOCK_AXIS_WIDE_MEMBERSHIP_IMPORT")
        self.assertIn("axis_wide_response_validator_not_ready", report["blockers"])
        self.assertIn("no_valid_axis_membership_rows", report["blockers"])
        self.assertFalse(report["canonical_files_mutated"])


if __name__ == "__main__":
    unittest.main()
