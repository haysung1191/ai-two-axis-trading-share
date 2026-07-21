from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_rebalance_membership_filter_audit.py")
SPEC = importlib.util.spec_from_file_location("build_kis_rebalance_membership_filter_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_mod)


class KisRebalanceMembershipFilterAuditTests(unittest.TestCase):
    def write_mapping(self, path: Path) -> None:
        path.write_text(
            json.dumps(
                {
                    "latest_signal_date": "2026-04-30",
                    "mapping_records": [
                        {
                            "route": "kis_us_stock",
                            "asset_type": "STOCK",
                            "symbol": "AAA",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def test_caveated_membership_does_not_prove_rebalance_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            mapping_path = tmp_path / "mapping.json"
            self.write_mapping(mapping_path)
            membership_path = tmp_path / "membership.csv"
            membership_path.write_text(
                "symbol,asset_type,axis,active_from,active_to,listed_date,delisted_date,source,snapshot_id,evidence_quality,notes\n"
                "AAA,us_stock,kis_us_stocks,2026-04-01,,2026-04-01,,snapshot,snap,current_snapshot_caveated,test\n",
                encoding="utf-8",
            )
            report = audit_mod.build_report(
                "2026-05-13T00:00:00+09:00",
                mapping_path,
                {"kis_us_stocks": membership_path},
            )

        self.assertEqual(report["status"], "BLOCK_REBALANCE_MEMBERSHIP_FILTER_NOT_PROVEN")
        self.assertEqual(report["audit"]["blocked_count"], 1)
        self.assertIn("membership_rows_are_caveated_not_operation_ready", report["audit"]["records"][0]["blockers"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_authoritative_active_membership_proves_latest_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            mapping_path = tmp_path / "mapping.json"
            self.write_mapping(mapping_path)
            membership_path = tmp_path / "membership.csv"
            membership_path.write_text(
                "symbol,asset_type,axis,active_from,active_to,listed_date,delisted_date,source,snapshot_id,evidence_quality,notes\n"
                "AAA,us_stock,kis_us_stocks,2020-01-01,,2020-01-01,,vendor,snap,authoritative,test\n",
                encoding="utf-8",
            )
            report = audit_mod.build_report(
                "2026-05-13T00:00:00+09:00",
                mapping_path,
                {"kis_us_stocks": membership_path},
            )

        self.assertEqual(report["status"], "PASS_REBALANCE_MEMBERSHIP_FILTER_PROOF")
        self.assertEqual(report["audit"]["pass_count"], 1)
        self.assertEqual(report["blockers"], [])
        self.assertFalse(report["safety"]["live_enabled"])


if __name__ == "__main__":
    unittest.main()
