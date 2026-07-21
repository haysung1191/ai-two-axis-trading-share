from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\apply_kis_axis_wide_membership_worklist_to_shards.py")
SPEC = importlib.util.spec_from_file_location("apply_kis_axis_wide_membership_worklist_to_shards", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
apply_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(apply_mod)


class KisAxisWideMembershipWorklistToShardsTests(unittest.TestCase):
    def valid_row(self, target: str) -> dict[str, str]:
        return {
            "request_id": "KIS_AXIS_001",
            "axis": "kis_us_stocks",
            "symbol": "AAA",
            "asset_type": "STOCK",
            "target_response_shard": target,
            "replacement_symbol": "AAA",
            "replacement_asset_type": "STOCK",
            "replacement_active_from": "2000-01-01",
            "replacement_active_to": "",
            "replacement_listed_date": "2000-01-01",
            "replacement_delisted_date": "",
            "replacement_source": "licensed_vendor_security_master:dataset",
            "replacement_snapshot_id": "snap_20260516",
            "replacement_evidence_quality": "licensed_vendor",
            "replacement_notes": "reviewed",
        }

    def test_dry_run_ready_does_not_write_shard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = str(Path(tmp) / "response.csv")
            report = apply_mod.build_report(
                "2026-05-16T13:00:00+09:00",
                worklist_rows=[self.valid_row(target)],
            )
            self.assertFalse(Path(target).exists())

        self.assertEqual(report["status"], "DRY_RUN_READY_TO_APPLY_WORKLIST_ROWS_TO_RESPONSE_SHARDS")
        self.assertEqual(report["valid_worklist_row_count"], 1)
        self.assertEqual(report["blocked_worklist_row_count"], 0)
        self.assertFalse(report["response_shards_mutated"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_apply_requires_confirmation_phrase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = str(Path(tmp) / "response.csv")
            report = apply_mod.build_report(
                "2026-05-16T13:00:00+09:00",
                worklist_rows=[self.valid_row(target)],
                apply=True,
                confirmation="wrong",
            )
            self.assertFalse(Path(target).exists())

        self.assertEqual(report["status"], "BLOCK_WORKLIST_TO_RESPONSE_SHARDS")
        self.assertIn("apply_confirmation_phrase_missing", report["blockers"])

    def test_apply_writes_response_shard_with_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "response.csv"
            report = apply_mod.build_report(
                "2026-05-16T13:00:00+09:00",
                worklist_rows=[self.valid_row(str(target))],
                apply=True,
                confirmation=apply_mod.APPLY_CONFIRMATION,
            )
            with target.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(report["status"], "APPLIED_WORKLIST_ROWS_TO_RESPONSE_SHARDS_REVIEWED")
        self.assertTrue(report["response_shards_mutated"])
        self.assertEqual(rows[0]["symbol"], "AAA")
        self.assertEqual(rows[0]["evidence_quality"], "licensed_vendor")

    def test_missing_replacement_fields_block_row(self) -> None:
        row = self.valid_row("response.csv")
        row["replacement_source"] = ""
        report = apply_mod.build_report(
            "2026-05-16T13:00:00+09:00",
            worklist_rows=[row],
        )

        self.assertEqual(report["status"], "BLOCK_WORKLIST_TO_RESPONSE_SHARDS")
        self.assertIn("blocked_worklist_rows_present", report["blockers"])
        self.assertIn("replacement_required_fields_missing", report["blocked_rows_sample"][0]["blockers"])


if __name__ == "__main__":
    unittest.main()
