from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_cand022_kis_tradable_mapping_audit.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_kis_tradable_mapping_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
mapping_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mapping_mod)


class Cand022KisTradableMappingAuditTests(unittest.TestCase):
    def test_latest_api_records_by_symbol_requires_cand022_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "api.json"
            path.write_text(
                json.dumps(
                    {
                        "candidate_id": "OTHER",
                        "records": [{"symbol": "DOW", "kis_api_tradability_verified": True}],
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(mapping_mod.latest_api_records_by_symbol(path), {})

    def test_merge_latest_api_evidence_updates_mapping_without_marking_unverified_constraints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            api_path = Path(tmp) / "CAND-022_kis_api_tradability.latest.json"
            rows = [
                {
                    "symbol": "DOW",
                    "local_mapping_pass": True,
                    "operation_mapping_pass": False,
                    "checks": {
                        "kis_api_tradability_verified": False,
                        "kis_order_constraints_verified": False,
                    },
                },
                {
                    "symbol": "MU",
                    "local_mapping_pass": True,
                    "operation_mapping_pass": False,
                    "checks": {
                        "kis_api_tradability_verified": False,
                        "kis_order_constraints_verified": False,
                    },
                },
            ]
            api_records = {
                "DOW": {
                    "symbol": "DOW",
                    "quote_lookup_pass": True,
                    "product_info_lookup_pass": False,
                    "kis_api_tradability_verified": True,
                    "kis_order_constraints_verified": True,
                    "one_share_cost_krw": 59209.54,
                    "max_order_krw_pass_for_one_share": True,
                },
                "MU": {
                    "symbol": "MU",
                    "quote_lookup_pass": True,
                    "product_info_lookup_pass": True,
                    "kis_api_tradability_verified": True,
                    "kis_order_constraints_verified": False,
                    "one_share_cost_krw": 1176314.13,
                    "max_order_krw_pass_for_one_share": False,
                },
            }

            with patch.object(mapping_mod, "KIS_API_TRADABILITY", api_path):
                mapping_mod.merge_latest_api_evidence(rows, api_records)

        by_symbol = {row["symbol"]: row for row in rows}
        self.assertTrue(by_symbol["DOW"]["checks"]["kis_api_tradability_verified"])
        self.assertTrue(by_symbol["DOW"]["checks"]["kis_order_constraints_verified"])
        self.assertTrue(by_symbol["DOW"]["operation_mapping_pass"])
        self.assertTrue(by_symbol["MU"]["checks"]["kis_api_tradability_verified"])
        self.assertFalse(by_symbol["MU"]["checks"]["kis_order_constraints_verified"])
        self.assertFalse(by_symbol["MU"]["operation_mapping_pass"])
        self.assertEqual(by_symbol["MU"]["one_share_cost_krw"], 1176314.13)

    def test_current_signal_observation_positions_requires_signal_only_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "current_signal.json"
            path.write_text(
                json.dumps(
                    {
                        "candidate_id": "CAND-022",
                        "scope": "signal_only_no_submit",
                        "status": "PASS",
                        "latest_signal_date": "2026-04-30",
                        "observation_date": "2026-05-14",
                        "records": [
                            {
                                "market": "US",
                                "asset_type": "STOCK",
                                "symbol": "DOW",
                                "asset_key": "US:STOCK:DOW",
                                "name": "Dow",
                                "sector": "Materials",
                                "target_weight": 0.2,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            positions = mapping_mod.current_signal_observation_positions(path)

        self.assertEqual(len(positions), 1)
        self.assertEqual(positions["SignalDate"].iloc[0], "2026-04-30")
        self.assertEqual(positions["NextDate"].iloc[0], "2026-05-14")
        self.assertEqual(positions["Symbol"].iloc[0], "DOW")

    def test_current_signal_observation_positions_rejects_non_signal_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "current_signal.json"
            path.write_text(
                json.dumps(
                    {
                        "candidate_id": "CAND-022",
                        "scope": "broker_submit",
                        "status": "PASS",
                        "records": [{"symbol": "DOW"}],
                    }
                ),
                encoding="utf-8",
            )

            positions = mapping_mod.current_signal_observation_positions(path)

        self.assertTrue(positions.empty)


if __name__ == "__main__":
    unittest.main()
