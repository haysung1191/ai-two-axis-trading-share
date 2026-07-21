from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_robustness_registry_record.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_robustness_registry_record", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class Cand022RobustnessRegistryRecordTests(unittest.TestCase):
    def test_build_record_preserves_execution_blockers_when_stage5_internal_passes(self) -> None:
        candidate = {
            "candidate_id": "CAND-022",
            "candidate_name": "compressed_broe60_sroe80",
            "candidate_state": "G2_CONVERSION_CANDIDATE",
            "universe_id": "KIS_COMBINED_KRW",
            "account": "KIS",
            "is_account_level": True,
            "is_component_signal": False,
            "is_single_asset": False,
            "metrics": {"cagr": 0.661, "mdd": -0.246, "sharpe": 1.753, "oos_mdd": -0.117},
            "blockers": [
                "data_operation_ready_not_verified",
                "human_mandate_incomplete",
                "survivorship_free_status_not_verified",
            ],
            "caveats": ["stage5_internal_checks_passed_but_operation_data_blocked"],
            "robustness_evidence": {
                "stage5_evidence_passed": True,
                "oos_parameters_defined": True,
                "primary_oos_metrics_complete": True,
                "rolling_walkforward_complete": True,
                "parameter_sensitivity_present": True,
                "parameter_sensitivity_passed": True,
                "cost_sensitivity_present": True,
                "cost_sensitivity_passed": True,
                "operation_data_ready": False,
                "survivorship_free_verified": False,
                "point_in_time_universe_verified": False,
                "shadow_queue_allowed": False,
                "tiny_live_ready": False,
            },
        }

        record = builder.build_record(candidate, "2026-05-14T00:00:00+09:00")

        self.assertEqual(record["evidence_status"], "PASSED")
        self.assertEqual(record["candidate_state_recommendation"], "ROBUSTNESS_PASSED")
        self.assertIn("data_operation_ready_not_verified", record["blockers"])
        self.assertIn("human_mandate_incomplete", record["blockers"])
        self.assertFalse(record["promotion_allowed"])
        self.assertFalse(record["operation_ready"])
        self.assertTrue(record["paper_blocked"])
        self.assertTrue(record["live_blocked"])
        self.assertTrue(record["broker_submit_blocked"])
        self.assertEqual(record["safety"]["pretrade_firewall_default_decision"], "BLOCK")

    def test_upsert_replaces_existing_cand022_record(self) -> None:
        old = {"candidate_id": "CAND-022", "evidence_status": "INCOMPLETE"}
        other = {"candidate_id": "CAND-001", "evidence_status": "PASSED"}
        new = {"candidate_id": "CAND-022", "evidence_status": "PASSED"}

        rows, action = builder.upsert_record([other, old], new)

        self.assertEqual(action, "updated")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["evidence_status"], "PASSED")


if __name__ == "__main__":
    unittest.main()
