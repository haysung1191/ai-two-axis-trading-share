from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_pit_survivorship_upgrade_plan.py")
SPEC = importlib.util.spec_from_file_location("build_kis_pit_survivorship_upgrade_plan", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
plan_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plan_mod)


class KisPitSurvivorshipUpgradePlanTests(unittest.TestCase):
    def test_build_plan_blocks_without_membership_intervals(self) -> None:
        axis_evidence = [
            {
                "axis": axis,
                "exists": True,
                "has_authoritative_membership_intervals": False,
                "membership_interval_columns_found": [],
            }
            for axis in ("kis_us_stocks", "kis_us_etfs", "kis_korea_stocks", "kis_korea_etfs")
        ]
        pit_audit = {
            "decision": "BLOCK",
            "checks": {
                "candidate_existing_point_in_time_verified": False,
                "candidate_existing_survivorship_verified": False,
            },
            "hard_blockers": ["point_in_time_universe_not_verified"],
        }
        data_registry = {
            "universes": [
                {
                    "universe_id": "KIS_COMBINED_KRW",
                    "operation_ready": False,
                    "operation_readiness_state": "DATA_BLOCKED",
                    "allowed_max_stage": "Stage 5: Robustness/OOS Validation (conditional)",
                }
            ]
        }

        plan = plan_mod.build_plan(
            "2026-05-13T00:00:00+09:00",
            pit_audit,
            {"decision": {"operation_ready": False}},
            data_registry,
            axis_evidence,
            {
                "status": "BLOCK_INCOMPLETE_MEMBERSHIP_DATA",
                "all_files_exist": True,
                "all_schema_ok": True,
                "all_have_rows": False,
                "any_caveated_rows": False,
            },
            {"status": "BLOCKED_DELISTING_SYMBOL_POLICY_NOT_VERIFIED"},
            {"status": "BLOCK_REBALANCE_MEMBERSHIP_FILTER_NOT_PROVEN"},
            {"status": "BLOCK_OPERATION_READY_MANIFEST", "operation_ready": False},
        )

        self.assertEqual(plan["status"], "BLOCKED_DATA_UPGRADE_REQUIRED")
        self.assertFalse(plan["operation_ready_now"])
        self.assertTrue(plan["canonical_membership_schema_ok"])
        self.assertIn("authoritative_pit_membership_history_missing_for_kis_combined", plan["remaining_blockers"])
        self.assertIn("Populate the four canonical PIT membership CSV files", plan["safe_next_action"])
        self.assertFalse(plan["safety"]["order_intent_created"])

    def test_build_plan_allows_registry_review_only_after_evidence_flags_clear(self) -> None:
        axis_evidence = [
            {
                "axis": axis,
                "exists": True,
                "has_authoritative_membership_intervals": True,
                "membership_interval_columns_found": ["active_from", "active_to"],
            }
            for axis in ("kis_us_stocks", "kis_us_etfs", "kis_korea_stocks", "kis_korea_etfs")
        ]
        pit_audit = {
            "decision": "PASS",
            "checks": {
                "candidate_existing_point_in_time_verified": True,
                "candidate_existing_survivorship_verified": True,
                "delisting_return_treatment_verified": True,
                "rebalance_membership_filter_verified": True,
            },
            "hard_blockers": [],
        }
        data_registry = {
            "universes": [
                {
                    "universe_id": "KIS_COMBINED_KRW",
                    "operation_ready": True,
                    "operation_readiness_state": "DATA_OPERATION_READY",
                    "allowed_max_stage": "Stage 6: Shadow",
                }
            ]
        }

        plan = plan_mod.build_plan(
            "2026-05-13T00:00:00+09:00",
            pit_audit,
            {"decision": {"operation_ready": True}},
            data_registry,
            axis_evidence,
            {
                "status": "PASS_MEMBERSHIP_FILES_VERIFIED",
                "all_files_exist": True,
                "all_schema_ok": True,
                "all_have_rows": True,
                "any_caveated_rows": False,
            },
            {"status": "PASS_DELISTING_SYMBOL_POLICY_VERIFIED"},
            {"status": "PASS_REBALANCE_MEMBERSHIP_FILTER_PROOF"},
            {"status": "PASS_OPERATION_READY_MANIFEST", "operation_ready": True},
        )

        self.assertEqual(plan["status"], "READY_FOR_REGISTRY_REVIEW")
        self.assertEqual(plan["remaining_blockers"], [])
        self.assertFalse(plan["safety"]["broker_submit_allowed"])

    def test_caveated_membership_rows_shift_next_action_to_authoritative_upgrade(self) -> None:
        axis_evidence = [
            {
                "axis": axis,
                "exists": True,
                "has_authoritative_membership_intervals": False,
                "membership_interval_columns_found": [],
            }
            for axis in ("kis_us_stocks", "kis_us_etfs", "kis_korea_stocks", "kis_korea_etfs")
        ]
        pit_audit = {
            "decision": "BLOCK",
            "checks": {
                "candidate_existing_point_in_time_verified": False,
                "candidate_existing_survivorship_verified": False,
            },
            "hard_blockers": ["point_in_time_universe_not_verified"],
        }
        data_registry = {
            "universes": [
                {
                    "universe_id": "KIS_COMBINED_KRW",
                    "operation_ready": False,
                    "operation_readiness_state": "DATA_BLOCKED",
                    "allowed_max_stage": "Stage 5: Robustness/OOS Validation (conditional)",
                }
            ]
        }

        plan = plan_mod.build_plan(
            "2026-05-13T00:00:00+09:00",
            pit_audit,
            {"decision": {"operation_ready": False}},
            data_registry,
            axis_evidence,
            {
                "status": "PASS_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE",
                "all_files_exist": True,
                "all_schema_ok": True,
                "all_have_rows": True,
                "any_caveated_rows": True,
            },
            {"status": "BLOCKED_DELISTING_SYMBOL_POLICY_NOT_VERIFIED"},
            {"status": "BLOCK_REBALANCE_MEMBERSHIP_FILTER_NOT_PROVEN"},
            {"status": "BLOCK_OPERATION_READY_MANIFEST", "operation_ready": False},
        )

        self.assertTrue(plan["canonical_membership_has_caveated_rows"])
        self.assertEqual(plan["delisting_symbol_policy_status"], "BLOCKED_DELISTING_SYMBOL_POLICY_NOT_VERIFIED")
        self.assertEqual(plan["rebalance_membership_filter_status"], "BLOCK_REBALANCE_MEMBERSHIP_FILTER_NOT_PROVEN")
        self.assertEqual(plan["snapshot_manifest_status"], "BLOCK_OPERATION_READY_MANIFEST")
        self.assertFalse(plan["snapshot_manifest_operation_ready"])
        self.assertIn("authoritative historical membership intervals", plan["safe_next_action"])
        self.assertIn("delisting/symbol-change policy", plan["safe_next_action"])

    def test_passed_component_reports_clear_closed_non_membership_blockers(self) -> None:
        axis_evidence = [
            {
                "axis": axis,
                "exists": True,
                "has_authoritative_membership_intervals": False,
                "membership_interval_columns_found": [],
            }
            for axis in ("kis_us_stocks", "kis_us_etfs", "kis_korea_stocks", "kis_korea_etfs")
        ]
        pit_audit = {
            "decision": "BLOCK",
            "checks": {
                "candidate_existing_point_in_time_verified": False,
                "candidate_existing_survivorship_verified": False,
                "delisting_return_treatment_verified": False,
                "rebalance_membership_filter_verified": False,
            },
            "hard_blockers": ["point_in_time_universe_not_verified"],
        }
        data_registry = {
            "universes": [
                {
                    "universe_id": "KIS_COMBINED_KRW",
                    "operation_ready": False,
                    "operation_readiness_state": "DATA_BLOCKED",
                    "allowed_max_stage": "Stage 5: Robustness/OOS Validation (conditional)",
                }
            ]
        }

        plan = plan_mod.build_plan(
            "2026-05-13T00:00:00+09:00",
            pit_audit,
            {"decision": {"operation_ready": False}},
            data_registry,
            axis_evidence,
            {
                "status": "PASS_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE",
                "all_files_exist": True,
                "all_schema_ok": True,
                "all_have_rows": True,
                "any_caveated_rows": True,
            },
            {"status": "PASS_DELISTING_SYMBOL_POLICY_VERIFIED"},
            {"status": "PASS_REBALANCE_MEMBERSHIP_FILTER_PROOF"},
            {"status": "BLOCK_OPERATION_READY_MANIFEST", "operation_ready": False},
        )

        self.assertTrue(plan["delisting_return_treatment_verified_now"])
        self.assertTrue(plan["rebalance_membership_filter_verified_now"])
        self.assertNotIn("delisting_return_treatment_not_verified", plan["remaining_blockers"])
        self.assertNotIn("strategy_manifest_does_not_prove_rebalance_membership_filter", plan["remaining_blockers"])
        self.assertIn("authoritative_pit_membership_history_missing_for_kis_combined", plan["remaining_blockers"])

    def test_registry_review_ready_does_not_require_registry_pre_marked_operation_ready(self) -> None:
        axis_evidence = [
            {
                "axis": axis,
                "exists": True,
                "has_authoritative_membership_intervals": False,
                "membership_interval_columns_found": [],
            }
            for axis in ("kis_us_stocks", "kis_us_etfs", "kis_korea_stocks", "kis_korea_etfs")
        ]
        pit_audit = {
            "decision": "BLOCK",
            "checks": {
                "candidate_existing_point_in_time_verified": False,
                "candidate_existing_survivorship_verified": False,
                "delisting_return_treatment_verified": False,
                "rebalance_membership_filter_verified": False,
            },
            "hard_blockers": ["data_operation_ready_not_verified"],
        }
        data_registry = {
            "universes": [
                {
                    "universe_id": "KIS_COMBINED_KRW",
                    "operation_ready": False,
                    "operation_readiness_state": "DATA_BLOCKED",
                    "allowed_max_stage": "Stage 5: Robustness/OOS Validation (conditional)",
                }
            ]
        }

        plan = plan_mod.build_plan(
            "2026-05-13T00:00:00+09:00",
            pit_audit,
            {"decision": {"operation_ready": False}},
            data_registry,
            axis_evidence,
            {
                "status": "PASS_MEMBERSHIP_FILES_VERIFIED",
                "all_files_exist": True,
                "all_schema_ok": True,
                "all_have_rows": True,
                "any_caveated_rows": False,
            },
            {"status": "PASS_DELISTING_SYMBOL_POLICY_VERIFIED"},
            {"status": "PASS_REBALANCE_MEMBERSHIP_FILTER_PROOF"},
            {"status": "BLOCK_OPERATION_READY_MANIFEST", "operation_ready": False},
        )

        self.assertEqual(plan["status"], "READY_FOR_REGISTRY_REVIEW")
        self.assertEqual(plan["remaining_blockers"], [])
        self.assertFalse(plan["operation_ready_now"])
        self.assertFalse(plan["safety"]["broker_submit_allowed"])


if __name__ == "__main__":
    unittest.main()
