from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_authoritative_data_request_packet.py")
SPEC = importlib.util.spec_from_file_location("build_kis_authoritative_data_request_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
request_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(request_mod)


class KisAuthoritativeDataRequestPacketTests(unittest.TestCase):
    def test_packet_writes_request_csvs_without_claiming_data_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packet = request_mod.build_packet(
                "2026-05-14T00:00:00+09:00",
                self.requirements(),
                {"recommended_next_action_id": "fill_kis_pit_authoritative_intake"},
                {
                    "templates": {
                        "membership": "membership_intake.csv",
                        "event": "event_intake.csv",
                        "replay": "replay_intake.csv",
                    }
                },
                tmp_path,
            )

            membership_rows = self.read_rows(tmp_path / "cand022_membership_request.csv")
            event_rows = self.read_rows(tmp_path / "cand022_event_or_no_event_request.csv")
            replay_rows = self.read_rows(tmp_path / "cand022_replay_request.csv")

        self.assertEqual(packet["status"], "PROVIDER_REQUEST_READY_BLOCKED_AWAITING_EXTERNAL_DATA")
        self.assertEqual(packet["request_counts"], {"membership_rows": 1, "event_or_no_event_rows": 1, "replay_rows": 1})
        self.assertEqual(membership_rows[0]["symbol"], "MU")
        self.assertEqual(event_rows[0]["accepted_coverage_status"], "event_recorded|no_event_found")
        self.assertEqual(replay_rows[0]["scenario"], "ticker_change")
        self.assertFalse(packet["safety"]["order_intent_created"])

    def requirements(self) -> dict:
        return {
            "membership_requirements": [
                {
                    "symbol": "MU",
                    "name": "Micron Technology",
                    "route": "kis_us_stock",
                    "market": "US",
                    "asset_type": "STOCK",
                    "axis": "kis_us_stocks",
                    "rebalance_date_to_cover": "2026-04-30",
                    "required_row": {
                        "active_from": "<= 2026-04-30",
                        "active_to": "blank or >= 2026-04-30",
                        "listed_date": "<= 2026-04-30",
                        "delisted_date": "blank or >= 2026-04-30",
                    },
                }
            ],
            "delisting_replay_requirements": {
                "scenario_row_requirements": {
                    "ticker_change": {
                        "event_type": "ticker_change",
                        "required_fields": ["case_id", "symbol", "successor_symbol"],
                    }
                }
            },
        }

    def read_rows(self, path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))


if __name__ == "__main__":
    unittest.main()
