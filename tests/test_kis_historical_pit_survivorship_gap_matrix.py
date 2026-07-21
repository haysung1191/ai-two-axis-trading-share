from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_historical_pit_survivorship_gap_matrix.py")
SPEC = importlib.util.spec_from_file_location("build_kis_historical_pit_survivorship_gap_matrix", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
gap_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gap_mod)


class KisHistoricalPitSurvivorshipGapMatrixTests(unittest.TestCase):
    def test_current_snapshot_caveats_block_first_gate(self) -> None:
        report = gap_mod.build_gap_matrix(
            "2026-05-16T09:00:00+09:00",
            membership={
                "status": "PASS_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE",
                "all_files_exist": True,
                "all_schema_ok": True,
                "all_have_rows": True,
                "any_caveated_rows": True,
                "all_verified": False,
                "blockers": ["canonical_membership_evidence_quality_caveated_not_operation_ready"],
                "axis_reports": [
                    {
                        "axis": "kis_us_stocks",
                        "row_count": 10,
                        "schema_ok": True,
                        "has_rows": True,
                        "caveated_row_count": 10,
                        "operation_ready_quality_row_count": 0,
                        "verified": False,
                    }
                ],
            },
            event={"status": "BLOCK_DELISTING_EVENT_FILE_NOT_VERIFIED", "blockers": ["event_missing"]},
            no_event={"status": "BLOCK_DELISTING_NO_EVENT_COVERAGE_NOT_VERIFIED", "blockers": ["no_event_missing"]},
            replay={"status": "BLOCK_DELISTING_REPLAY_NOT_VERIFIED", "blockers": ["replay_missing"]},
            policy={"status": "BLOCKED_DELISTING_SYMBOL_POLICY_NOT_VERIFIED", "blockers": ["policy_missing"]},
            rebalance={
                "status": "BLOCK_REBALANCE_MEMBERSHIP_FILTER_NOT_PROVEN",
                "blockers": ["rebalance_not_proven"],
                "audit": {
                    "record_count": 1,
                    "pass_count": 0,
                    "blocked_count": 1,
                    "records": [
                        {
                            "symbol": "MU",
                            "axis": "kis_us_stocks",
                            "as_of": "2026-04-30",
                            "status": "BLOCK",
                            "membership_row_count": 1,
                            "active_operation_ready_membership_found": False,
                            "blockers": ["membership_rows_are_caveated_not_operation_ready"],
                        }
                    ],
                },
            },
            manifest={"status": "BLOCK_OPERATION_READY_MANIFEST", "operation_ready": False, "blockers": ["manifest_block"]},
            official_route={
                "status": "OFFICIAL_KIS_ROUTE_RESCOPED",
                "pipeline_decision": {"retire_default_external_provider_dispatch": True},
            },
        )

        self.assertEqual(report["status"], "BLOCK_HISTORICAL_PIT_SURVIVORSHIP_GAPS")
        self.assertFalse(report["operation_ready"])
        self.assertTrue(report["official_kis_current_readiness_active"])
        self.assertEqual(report["gate_summary"]["first_blocked_gate_id"], "G1_MEMBERSHIP_INTERVALS_OPERATION_READY")
        self.assertIn("canonical_membership_evidence_quality_caveated_not_operation_ready", report["remaining_blockers"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_all_gates_pass_when_operation_ready_evidence_exists(self) -> None:
        report = gap_mod.build_gap_matrix(
            "2026-05-16T09:00:00+09:00",
            membership={
                "status": "PASS_MEMBERSHIP_FILES_VERIFIED",
                "all_files_exist": True,
                "all_schema_ok": True,
                "all_have_rows": True,
                "any_caveated_rows": False,
                "all_verified": True,
                "axis_reports": [
                    {
                        "axis": "kis_us_stocks",
                        "row_count": 10,
                        "schema_ok": True,
                        "has_rows": True,
                        "caveated_row_count": 0,
                        "operation_ready_quality_row_count": 10,
                        "verified": True,
                    }
                ],
            },
            event={"status": "PASS_DELISTING_EVENT_FILE_VERIFIED"},
            no_event={"status": "BLOCK_DELISTING_NO_EVENT_COVERAGE_NOT_VERIFIED"},
            replay={"status": "PASS_DELISTING_REPLAY_VERIFIED", "inspection": {"covered_scenarios": ["ticker_change"]}},
            policy={"status": "PASS_DELISTING_SYMBOL_POLICY_VERIFIED"},
            rebalance={
                "status": "PASS_REBALANCE_MEMBERSHIP_FILTER_PROOF",
                "audit": {"record_count": 1, "pass_count": 1, "blocked_count": 0, "records": []},
            },
            manifest={"status": "PASS_OPERATION_READY_MANIFEST", "operation_ready": True},
            official_route={"status": "OFFICIAL_KIS_ROUTE_RESCOPED", "pipeline_decision": {"retire_default_external_provider_dispatch": True}},
        )

        self.assertEqual(report["status"], "PASS_HISTORICAL_PIT_SURVIVORSHIP_READY")
        self.assertTrue(report["operation_ready"])
        self.assertEqual(report["remaining_blockers"], [])
        self.assertEqual(report["gate_summary"]["passed_count"], 5)


if __name__ == "__main__":
    unittest.main()
