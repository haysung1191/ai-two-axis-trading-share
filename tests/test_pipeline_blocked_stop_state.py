from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_pipeline_blocked_stop_state.py")
SPEC = importlib.util.spec_from_file_location("build_pipeline_blocked_stop_state", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
stop_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stop_state)


class PipelineBlockedStopStateTests(unittest.TestCase):
    def test_stop_state_lists_only_external_or_human_unblock_inputs(self) -> None:
        report = stop_state.build_report(
            {"status": "PASS"},
            {"status": "WAITING_FOR_HUMAN_BITHUMB_DECISION", "command_kind": "human_decision", "safety": {"live_enabled": False}},
            {
                "direct_blocker_count": 2,
                "direct_blockers": [
                    {
                        "axis": "BITHUMB_KRW",
                        "candidate_id": "sweep2154",
                        "required_decisions": ["APPROVE_SHADOW_REVIEW_ONLY", "REJECT", "DEFER"],
                        "current_blockers": ["HUMAN_GATEKEEPER_SHADOW_DECISION_INVALID"],
                    },
                    {
                        "axis": "KIS_COMBINED_KRW",
                        "blocked_worklist_row_count": 16444,
                        "current_blockers": ["reviewed_axis_wide_source_export_missing"],
                    },
                ],
            },
            {
                "objective_restatement": "two-axis pipeline",
                "completion_decision": "NOT_COMPLETE",
                "stage13_complete": False,
            },
        )

        self.assertEqual(report["status"], "STOPPED_BLOCKED_ON_EXTERNAL_OR_HUMAN_INPUT")
        self.assertEqual(len(report["unblock_inputs"]), 2)
        self.assertEqual(report["unblock_inputs"][0]["candidate_id"], "sweep2154")
        self.assertIn("do_not_enable_live", report["must_not_do"])
        self.assertEqual(report["safety"]["live_enabled"], False)


if __name__ == "__main__":
    unittest.main()
