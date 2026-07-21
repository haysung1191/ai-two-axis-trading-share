from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_stage6_shadow_readiness_packet.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_stage6_shadow_readiness_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
stage6_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stage6_mod)


class Cand022Stage6ShadowReadinessPacketTests(unittest.TestCase):
    def test_gatekeeper_transition_written_but_blocked_is_not_reported_as_missing(self) -> None:
        transition = {
            "transition_id": "ROBUSTNESS_TO_SHADOW::CAND-022",
            "decision": "BLOCK",
            "failed_checks": ["stage5_blockers_present"],
        }

        passed, failed, decision = stage6_mod.classify_gatekeeper_transition(transition)

        self.assertEqual(decision, "BLOCK")
        self.assertIn("gatekeeper_stage5_to_stage6_transition_written", passed)
        self.assertIn("gatekeeper_stage5_to_stage6_transition_blocked", failed)
        self.assertNotIn("gatekeeper_stage5_to_stage6_transition_not_written", failed)

    def test_gatekeeper_transition_missing_is_reported_as_not_written(self) -> None:
        passed, failed, decision = stage6_mod.classify_gatekeeper_transition({})

        self.assertEqual(decision, "NOT_WRITTEN")
        self.assertEqual(passed, [])
        self.assertEqual(failed, ["gatekeeper_stage5_to_stage6_transition_not_written"])

    def test_find_stage5_to_stage6_transition_reads_cand022_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "transition_decisions.jsonl"
            path.write_text(
                "\n".join(
                    [
                        json.dumps({"transition_id": "ROBUSTNESS_TO_SHADOW::CAND-001", "decision": "PASS_TO_NEXT_QUEUE"}),
                        json.dumps({"transition_id": "ROBUSTNESS_TO_SHADOW::CAND-022", "decision": "BLOCK"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            row = stage6_mod.find_stage5_to_stage6_transition("CAND-022", path)

        self.assertEqual(row["transition_id"], "ROBUSTNESS_TO_SHADOW::CAND-022")
        self.assertEqual(row["decision"], "BLOCK")

    def test_freshness_days_parses_iso_date(self) -> None:
        self.assertEqual(stage6_mod.freshness_days("2026-05-12", date(2026, 5, 14)), 2)
        self.assertIsNone(stage6_mod.freshness_days(None, date(2026, 5, 14)))
        self.assertIsNone(stage6_mod.freshness_days("bad-date", date(2026, 5, 14)))

    def test_operation_readiness_blockers_remove_mapping_blocker_after_current_mapping_pass(self) -> None:
        kis_ready = {
            "blockers": [
                "data_operation_ready_not_verified",
                "tradable_symbol_mapping_not_verified",
                "operation_controls_not_verified",
                "point_in_time_universe_not_verified",
            ]
        }

        blockers = stage6_mod.operation_readiness_blockers(kis_ready, local_mapping_ok=True)

        self.assertNotIn("tradable_symbol_mapping_not_verified", blockers)
        self.assertIn("operation_controls_not_verified", blockers)
        self.assertIn("data_operation_ready_not_verified", blockers)
        self.assertIn("point_in_time_universe_not_verified", blockers)

    def test_operation_readiness_blockers_remove_operation_controls_after_no_submit_controls_pass(self) -> None:
        kis_ready = {
            "blockers": [
                "data_operation_ready_not_verified",
                "tradable_symbol_mapping_not_verified",
                "operation_controls_not_verified",
                "point_in_time_universe_not_verified",
            ]
        }

        blockers = stage6_mod.operation_readiness_blockers(
            kis_ready,
            local_mapping_ok=True,
            api_tradability_ok=True,
        )

        self.assertNotIn("tradable_symbol_mapping_not_verified", blockers)
        self.assertNotIn("operation_controls_not_verified", blockers)
        self.assertIn("data_operation_ready_not_verified", blockers)
        self.assertIn("point_in_time_universe_not_verified", blockers)

    def test_operation_readiness_blockers_preserve_mapping_blocker_until_mapping_passes(self) -> None:
        kis_ready = {"blockers": ["tradable_symbol_mapping_not_verified"]}

        blockers = stage6_mod.operation_readiness_blockers(kis_ready, local_mapping_ok=False)

        self.assertEqual(blockers, ["tradable_symbol_mapping_not_verified"])

    def test_valid_shadow_exception_acceptance_requires_no_submit_scope_and_queue(self) -> None:
        acceptance = {
            "candidate_id": "CAND-022",
            "accepted_policy": "shadow_only_exception",
            "scope": "NO_SUBMIT_REVIEW_ONLY",
            "required_exact_instruction": "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY",
            "is_approval": False,
            "safety": stage6_mod.SAFETY,
        }
        queue_rows = [{"candidate_id": "CAND-022", "decision": "PASS_TO_NEXT_QUEUE"}]

        result = stage6_mod.validate_shadow_exception_acceptance(acceptance, queue_rows)

        self.assertTrue(result["active"])
        self.assertEqual(result["failed_checks"], [])

    def test_shadow_exception_acceptance_rejects_missing_queue_row(self) -> None:
        acceptance = {
            "candidate_id": "CAND-022",
            "accepted_policy": "shadow_only_exception",
            "scope": "NO_SUBMIT_REVIEW_ONLY",
            "required_exact_instruction": "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY",
            "is_approval": False,
            "safety": stage6_mod.SAFETY,
        }

        result = stage6_mod.validate_shadow_exception_acceptance(acceptance, [])

        self.assertFalse(result["active"])
        self.assertIn("queue_contains_cand022_pass", result["failed_checks"])

    def test_latest_candidate_registry_payload_rebuilds_records_from_jsonl_rows(self) -> None:
        existing = {
            "schema_version": "1.1.0",
            "records": [{"candidate_id": "CAND-001", "candidate_state": "OLD"}],
            "candidates": [{"candidate_id": "legacy"}],
        }
        rows = [
            {
                "candidate_id": "CAND-001",
                "candidate_state": "ROBUSTNESS_PASSED",
                "universe_id": "KIS_COMBINED_KRW",
                "operation_ready": False,
                "paper_blocked": True,
                "live_blocked": True,
                "broker_submit_blocked": True,
                "promotion_allowed": False,
            },
            {
                "candidate_id": "CAND-022",
                "candidate_state": "G2_CONVERSION_CANDIDATE",
                "universe_id": "KIS_COMBINED_KRW",
                "operation_ready": False,
                "paper_blocked": True,
                "live_blocked": True,
                "broker_submit_blocked": True,
                "promotion_allowed": False,
            },
        ]

        payload = stage6_mod.build_latest_candidate_registry_payload(
            existing,
            rows,
            "2026-05-14T15:00:00+09:00",
        )

        self.assertEqual(payload["total_records"], 2)
        self.assertEqual({row["candidate_id"] for row in payload["records"]}, {"CAND-001", "CAND-022"})
        self.assertEqual(payload["paper_blocked_count"], 2)
        self.assertEqual(payload["live_blocked_count"], 2)
        self.assertEqual(payload["broker_submit_blocked_count"], 2)
        self.assertEqual(payload["promotion_allowed_count"], 0)
        self.assertEqual(payload["candidates"], [{"candidate_id": "legacy"}])

    def test_human_mandate_is_not_a_stage6_no_submit_shadow_blocker(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")

        self.assertIn('"human_mandate_incomplete_blocks_no_submit_shadow": False', source)
        self.assertIn('"human_mandate_incomplete_blocks_paper_live_order_intent": True', source)
        self.assertNotIn('failed_checks.append("human_mandate_incomplete")', source)


if __name__ == "__main__":
    unittest.main()
