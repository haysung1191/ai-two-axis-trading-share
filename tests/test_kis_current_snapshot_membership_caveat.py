from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_current_snapshot_membership_caveat.py")
SPEC = importlib.util.spec_from_file_location("build_kis_current_snapshot_membership_caveat", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)


class KisCurrentSnapshotMembershipCaveatTests(unittest.TestCase):
    def test_build_snapshot_writes_caveated_membership_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "universe.csv"
            output = tmp_path / "membership.csv"
            source.write_text("symbol,name\nAAA,A\nBBB,B\nAAA,A again\n", encoding="utf-8")
            report = snapshot.build_snapshot(
                datetime(2026, 5, 13, tzinfo=timezone.utc),
                {
                    "kis_us_stocks": {
                        "path": source,
                        "asset_type": "us_stock",
                        "output": output,
                    }
                },
            )

            with output.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(report["status"], "CAVEATED_CURRENT_SNAPSHOT_WRITTEN")
        self.assertEqual(report["total_rows"], 2)
        self.assertFalse(report["operation_ready"])
        self.assertEqual(rows[0]["evidence_quality"], "current_snapshot_caveated")
        self.assertEqual({row["symbol"] for row in rows}, {"AAA", "BBB"})
        self.assertFalse(report["safety"]["order_intent_created"])


if __name__ == "__main__":
    unittest.main()
