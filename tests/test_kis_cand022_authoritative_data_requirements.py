from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_cand022_authoritative_data_requirements.py")
SPEC = importlib.util.spec_from_file_location("build_kis_cand022_authoritative_data_requirements", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
req_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(req_mod)


class KisCand022AuthoritativeDataRequirementsTests(unittest.TestCase):
    def test_membership_requirements_are_row_level_and_blocked(self) -> None:
        mapping = {
            "candidate_name": "compressed_broe60_sroe80",
            "latest_signal_date": "2026-04-30",
            "latest_position_count": 1,
            "mapping_records": [
                {
                    "route": "kis_us_stock",
                    "market": "US",
                    "asset_type": "STOCK",
                    "symbol": "MU",
                    "name": "Micron Technology",
                }
            ],
        }
        rebalance_audit = {
            "status": "BLOCK_REBALANCE_MEMBERSHIP_FILTER_NOT_PROVEN",
            "audit": {
                "records": [
                    {
                        "symbol": "MU",
                        "status": "BLOCK",
                        "blockers": [
                            "membership_rows_are_caveated_not_operation_ready",
                            "no_active_operation_ready_membership_interval_for_rebalance_date",
                        ],
                    }
                ]
            },
        }
        event_report = {
            "status": "BLOCK_DELISTING_EVENT_FILE_NOT_VERIFIED",
            "inspection": {"row_count": 0},
            "blockers": ["kis_delisting_symbol_change_events_empty"],
            "required_columns": ["symbol", "axis", "event_type"],
        }
        replay_report = {
            "status": "BLOCK_DELISTING_REPLAY_NOT_VERIFIED",
            "inspection": {"row_count": 0, "missing_scenarios": ["ticker_change"]},
            "blockers": ["kis_delisting_replay_cases_empty"],
            "required_columns": ["case_id", "symbol", "axis"],
            "required_scenarios": ["ticker_change"],
        }

        report = req_mod.build_report(
            "2026-05-14T00:00:00+09:00",
            mapping,
            rebalance_audit,
            event_report,
            replay_report,
            {"status": "BLOCKED_DATA_UPGRADE_REQUIRED"},
        )

        self.assertEqual(report["status"], "BLOCKED_AWAITING_AUTHORITATIVE_DATA_ROWS")
        self.assertEqual(len(report["membership_requirements"]), 1)
        row = report["membership_requirements"][0]["required_row"]
        self.assertEqual(row["symbol"], "MU")
        self.assertEqual(row["active_from"], "<= 2026-04-30")
        self.assertIn("authoritative", row["evidence_quality"])
        self.assertIn("ticker_change", report["delisting_replay_requirements"]["scenario_row_requirements"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_route_axis_mapping_covers_korean_etf(self) -> None:
        axis = req_mod.route_to_axis("kis_korea_etf", "ETF")
        self.assertEqual(axis, "kis_korea_etfs")
        target = req_mod.membership_file_for_axis(axis)
        self.assertIsNotNone(target)
        self.assertTrue(str(target).endswith("kis_korea_etfs_membership_intervals.csv"))


if __name__ == "__main__":
    unittest.main()
