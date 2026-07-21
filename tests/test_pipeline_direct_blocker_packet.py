from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_pipeline_direct_blocker_packet.py")
SPEC = importlib.util.spec_from_file_location("build_pipeline_direct_blocker_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
packet_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_mod)


class PipelineDirectBlockerPacketTests(unittest.TestCase):
    def test_packet_keeps_only_bithumb_and_kis_direct_blockers(self) -> None:
        packet = packet_mod.build_packet(
            {
                "completion_decision": "NOT_COMPLETE",
                "stage13_complete": False,
                "external_input_blockers": ["reviewed_axis_wide_source_export_missing"],
                "prompt_to_artifact_checklist": [
                    {
                        "stage_id": "axis_bithumb_krw",
                        "missing_or_blocked": ["HUMAN_GATEKEEPER_SHADOW_DECISION_INVALID"],
                        "observed": {
                            "shadow_preflight_candidate_id": "sweep2154",
                            "top_triggered_candidate": {"market": "KRW-ORCA"},
                        },
                    }
                ],
            },
            {"status": "READY_TO_WRITE_DECISION", "candidate_id": "sweep2154", "file_mutated": False},
            {"next_phrase": {"candidate_id": "sweep2154", "exact_phrase_to_record": "APPROVE_SHADOW_REVIEW_ONLY"}},
            {
                "blocked_worklist_row_count": 16444,
                "valid_export_count": 0,
                "raw_drop_dir": "raw",
                "normalized_export_dir": "exports",
                "paths": {"manifest": "manifest.csv"},
                "required_normalized_columns": ["axis", "symbol"],
                "accepted_evidence_quality": ["exchange_official"],
                "commands_after_files_are_placed": ["python intake.py"],
                "guarded_apply_commands_after_review": ["python apply.py --apply"],
            },
        )

        self.assertEqual(packet["status"], "BLOCKED_ON_EXTERNAL_OR_HUMAN_INPUT")
        self.assertEqual(packet["direct_blocker_count"], 2)
        axes = [row["axis"] for row in packet["direct_blockers"]]
        self.assertEqual(axes, ["BITHUMB_KRW", "KIS_COMBINED_KRW"])
        self.assertIn("--write", packet["direct_blockers"][0]["command_if_human_approves_shadow_review_only"])
        self.assertEqual(packet["direct_blockers"][1]["blocked_worklist_row_count"], 16444)
        self.assertFalse(packet["safety"]["paper_enabled"])
        self.assertFalse(packet["safety"]["live_enabled"])
        self.assertFalse(packet["safety"]["broker_submit_allowed"])
        self.assertEqual(packet["safety"]["real_orders"], 0)


if __name__ == "__main__":
    unittest.main()
