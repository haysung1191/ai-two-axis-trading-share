from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_pipeline_direct_next_command.py")
SPEC = importlib.util.spec_from_file_location("build_pipeline_direct_next_command", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
next_command = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(next_command)


class PipelineDirectNextCommandTests(unittest.TestCase):
    def test_prefers_human_bithumb_decision_and_keeps_safety_closed(self) -> None:
        report = next_command.build_report(
            {
                "stage13_complete": False,
                "direct_blockers": [
                    {
                        "axis": "BITHUMB_KRW",
                        "status": "BLOCKED_WAITING_FOR_HUMAN_DECISION",
                        "candidate_id": "sweep2154",
                        "current_blockers": ["HUMAN_GATEKEEPER_SHADOW_DECISION_INVALID"],
                        "command_if_human_approves_shadow_review_only": "python record.py --write",
                    },
                    {
                        "axis": "KIS_COMBINED_KRW",
                        "status": "BLOCKED_WAITING_FOR_REVIEWED_AXIS_WIDE_SOURCE_EXPORT",
                        "commands_after_files_are_placed": ["python kis.py"],
                    },
                ],
                "excluded_work": ["generic research"],
            }
        )

        self.assertEqual(report["status"], "WAITING_FOR_HUMAN_BITHUMB_DECISION")
        self.assertEqual(report["command_kind"], "human_decision_record_command_after_explicit_human_choice")
        self.assertEqual(report["next_command"], "python record.py --write")
        self.assertIn("generic research", report["excluded_work"])
        self.assertFalse(report["safety"]["paper_enabled"])
        self.assertFalse(report["safety"]["live_enabled"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_uses_kis_commands_when_bithumb_is_not_waiting(self) -> None:
        report = next_command.build_report(
            {
                "stage13_complete": False,
                "direct_blockers": [
                    {
                        "axis": "KIS_COMBINED_KRW",
                        "status": "BLOCKED_WAITING_FOR_REVIEWED_AXIS_WIDE_SOURCE_EXPORT",
                        "current_blockers": ["reviewed_axis_wide_source_export_missing"],
                        "commands_after_files_are_placed": ["python normalize.py", "python intake.py"],
                    }
                ],
            }
        )

        self.assertEqual(report["status"], "WAITING_FOR_KIS_REVIEWED_SOURCE_EXPORT")
        self.assertIn("python normalize.py", report["next_command"])
        self.assertIn("reviewed_axis_wide_source_export_missing", report["blockers"])

    def test_stage9_waits_for_live_approval_without_shadow_or_paper_work(self) -> None:
        report = next_command.build_report(
            {
                "stage13_complete": False,
                "direct_blockers": [
                    {
                        "axis": "PIPELINE_STAGE9",
                        "status": "BLOCKED_WAITING_FOR_EXACT_LIVE_APPROVAL_OR_NO_SUBMIT_POLICY",
                        "current_blockers": ["order_intent_not_created", "pretrade_firewall_not_passed"],
                        "required_phrase_format": "LIVE APPROVE <max_krw> <max_daily_loss_krw> <max_total_loss_krw>",
                    }
                ],
            }
        )

        self.assertEqual(report["status"], "WAITING_FOR_EXACT_LIVE_APPROVAL_OR_NO_SUBMIT_POLICY")
        self.assertEqual(report["command_kind"], "operator_live_approval_phrase_required_before_order_intent")
        self.assertIn("LIVE APPROVE", report["next_command"])
        self.assertNotIn("record_explicit_human_bithumb_shadow_review_decision", report["allowed_work"])
        self.assertNotIn("ingest_reviewed_kis_axis_wide_source_export", report["allowed_work"])

    def test_stage10_reports_global_disable_after_pretrade_pass(self) -> None:
        report = next_command.build_report(
            {
                "stage13_complete": False,
                "direct_blockers": [
                    {
                        "axis": "PIPELINE_STAGE10",
                        "status": "BLOCKED_BY_GLOBAL_DISABLE_OR_SUBMIT_GUARD",
                        "current_blockers": ["global_disable_all_trading_present"],
                    }
                ],
            }
        )

        self.assertEqual(report["status"], "TINY_LIVE_PREFLIGHT_PASSED_BROKER_SUBMIT_BLOCKED_BY_GLOBAL_DISABLE")
        self.assertIn("DISABLE_ALL_TRADING", report["next_command"])
        self.assertIn("global_disable_all_trading_present", report["blockers"])


if __name__ == "__main__":
    unittest.main()
