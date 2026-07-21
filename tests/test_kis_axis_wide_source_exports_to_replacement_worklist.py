from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\apply_kis_axis_wide_source_exports_to_replacement_worklist.py")
SPEC = importlib.util.spec_from_file_location("apply_kis_axis_wide_source_exports_to_replacement_worklist", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class KisAxisWideSourceExportsToReplacementWorklistTests(unittest.TestCase):
    def worklist_row(self, target: str = "response.csv") -> dict[str, str]:
        return {
            "request_id": "KIS_AXIS_003",
            "axis": "kis_korea_stocks",
            "symbol": "000020",
            "asset_type": "korea_stock",
            "target_response_shard": target,
            "replacement_symbol": "000020",
            "replacement_asset_type": "korea_stock",
            "replacement_active_from": "",
            "replacement_active_to": "",
            "replacement_listed_date": "",
            "replacement_delisted_date": "",
            "replacement_source": "",
            "replacement_snapshot_id": "",
            "replacement_evidence_quality": "",
            "replacement_notes": "",
        }

    def export_row(self) -> dict[str, str]:
        return {
            "axis": "kis_korea_stocks",
            "symbol": "000020",
            "asset_type": "korea_stock",
            "active_from": "1976-06-30",
            "active_to": "",
            "listed_date": "1976-06-30",
            "delisted_date": "",
            "source": "KRX Data Marketplace",
            "snapshot_id": "krx_export_20260516",
            "evidence_quality": "exchange_official",
            "source_artifact_path": "exports/krx.csv",
            "license_scope": "reviewed_internal_research",
            "exchange": "KRX",
            "issuer_name": "sample",
            "security_id": "KR7000020008",
            "notes": "reviewed",
        }

    def write_export(self, path: Path, rows: list[dict[str, str]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    def test_blocks_without_ready_export_contract(self) -> None:
        report = module.build_report(
            "2026-05-16T00:00:00+09:00",
            worklist_rows=[self.worklist_row()],
            contract_report={"status": "BLOCK_SOURCE_EXPORT_INTAKE", "export_reports": []},
        )

        self.assertEqual(report["status"], "BLOCK_SOURCE_EXPORTS_TO_REPLACEMENT_WORKLIST")
        self.assertIn("source_export_intake_not_ready", report["blockers"])
        self.assertIn("no_valid_source_export_files", report["blockers"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_dry_run_matches_export_without_mutating_worklist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "export.csv"
            self.write_export(export_path, [self.export_row()])
            report = module.build_report(
                "2026-05-16T00:00:00+09:00",
                worklist_rows=[self.worklist_row()],
                contract_report={
                    "status": "READY_SOURCE_EXPORTS_FOR_REPLACEMENT_MAPPING",
                    "export_reports": [
                        {
                            "valid_for_operation_ready_intake": True,
                            "file_info": {"path": str(export_path)},
                        }
                    ],
                },
            )

        self.assertEqual(report["status"], "DRY_RUN_READY_TO_APPLY_FULL_SOURCE_EXPORTS_TO_WORKLIST")
        self.assertEqual(report["matched_worklist_row_count"], 1)
        self.assertEqual(report["unmatched_worklist_row_count"], 0)
        self.assertEqual(report["coverage_ratio"], 1.0)
        self.assertTrue(report["full_coverage_ready"])
        self.assertFalse(report["worklist_mutated"])

    def test_apply_requires_confirmation_phrase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "export.csv"
            self.write_export(export_path, [self.export_row()])
            report = module.build_report(
                "2026-05-16T00:00:00+09:00",
                worklist_rows=[self.worklist_row()],
                contract_report={
                    "status": "READY_SOURCE_EXPORTS_FOR_REPLACEMENT_MAPPING",
                    "export_reports": [
                        {
                            "valid_for_operation_ready_intake": True,
                            "file_info": {"path": str(export_path)},
                        }
                    ],
                },
                apply=True,
                confirmation="wrong",
            )

        self.assertEqual(report["status"], "BLOCK_SOURCE_EXPORTS_TO_REPLACEMENT_WORKLIST")
        self.assertIn("apply_confirmation_phrase_missing", report["blockers"])

    def test_apply_writes_combined_and_axis_worklists_with_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            worklist_dir = Path(tmp) / "worklists"
            combined = worklist_dir / "combined.csv"
            export_path = Path(tmp) / "export.csv"
            self.write_export(export_path, [self.export_row()])
            columns = list(self.worklist_row().keys())
            worklist_dir.mkdir(parents=True)
            with combined.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                writer.writerow(self.worklist_row())
            with patch.object(module, "WORKLIST_DIR", worklist_dir), patch.object(module, "COMBINED_WORKLIST", combined):
                report = module.build_report(
                    "2026-05-16T00:00:00+09:00",
                    worklist_rows=[self.worklist_row()],
                    contract_report={
                        "status": "READY_SOURCE_EXPORTS_FOR_REPLACEMENT_MAPPING",
                        "export_reports": [
                            {
                                "valid_for_operation_ready_intake": True,
                                "file_info": {"path": str(export_path)},
                            }
                        ],
                    },
                    apply=True,
                    confirmation=module.APPLY_CONFIRMATION,
                )
                with combined.open("r", encoding="utf-8-sig", newline="") as f:
                    rows = list(csv.DictReader(f))

        self.assertEqual(report["status"], "APPLIED_FULL_SOURCE_EXPORTS_TO_REPLACEMENT_WORKLIST_REVIEWED")
        self.assertTrue(report["worklist_mutated"])
        self.assertEqual(rows[0]["replacement_source"], "KRX Data Marketplace")
        self.assertEqual(rows[0]["replacement_evidence_quality"], "exchange_official")

    def test_partial_export_is_distinct_from_full_coverage_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "export.csv"
            self.write_export(export_path, [self.export_row()])
            unmatched = self.worklist_row()
            unmatched["symbol"] = "000040"
            unmatched["replacement_symbol"] = "000040"
            report = module.build_report(
                "2026-05-16T00:00:00+09:00",
                worklist_rows=[self.worklist_row(), unmatched],
                contract_report={
                    "status": "READY_SOURCE_EXPORTS_FOR_REPLACEMENT_MAPPING",
                    "export_reports": [
                        {
                            "valid_for_operation_ready_intake": True,
                            "file_info": {"path": str(export_path)},
                        }
                    ],
                },
            )

        self.assertEqual(report["status"], "DRY_RUN_READY_TO_APPLY_SOURCE_EXPORTS_TO_WORKLIST")
        self.assertEqual(report["matched_worklist_row_count"], 1)
        self.assertEqual(report["unmatched_worklist_row_count"], 1)
        self.assertEqual(report["coverage_ratio"], 0.5)
        self.assertFalse(report["full_coverage_ready"])

    def test_duplicate_export_keys_block_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "export.csv"
            self.write_export(export_path, [self.export_row(), self.export_row()])
            report = module.build_report(
                "2026-05-16T00:00:00+09:00",
                worklist_rows=[self.worklist_row()],
                contract_report={
                    "status": "READY_SOURCE_EXPORTS_FOR_REPLACEMENT_MAPPING",
                    "export_reports": [
                        {
                            "valid_for_operation_ready_intake": True,
                            "file_info": {"path": str(export_path)},
                        }
                    ],
                },
            )

        self.assertEqual(report["status"], "BLOCK_SOURCE_EXPORTS_TO_REPLACEMENT_WORKLIST")
        self.assertIn("duplicate_export_keys", report["blockers"])


if __name__ == "__main__":
    unittest.main()
