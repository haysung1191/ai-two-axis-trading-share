from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_axis_wide_membership_coverage_progress.py")
SPEC = importlib.util.spec_from_file_location("build_kis_axis_wide_membership_coverage_progress", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
progress = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(progress)


class KisAxisWideMembershipCoverageProgressTests(unittest.TestCase):
    def membership_verifier(self, verified: bool = False) -> dict:
        return {
            "axis_reports": [
                {
                    "axis": "kis_us_stocks",
                    "path": r"C:\AI\data_snapshots\kis_pit_membership\kis_us_stocks_membership_intervals.csv",
                    "row_count": 100,
                    "caveated_row_count": 95 if not verified else 0,
                    "operation_ready_quality_row_count": 5 if not verified else 100,
                    "schema_ok": True,
                    "verified": verified,
                }
            ]
        }

    def handoff_package(self) -> dict:
        return {
            "status": "READY_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE",
            "request_rows": [
                {
                    "request_id": "KIS_AXIS_001",
                    "axis": "kis_us_stocks",
                    "canonical_target_file": r"C:\AI\data_snapshots\kis_pit_membership\kis_us_stocks_membership_intervals.csv",
                    "current_row_count": 100,
                    "current_caveated_row_count": 95,
                    "current_operation_ready_row_count": 5,
                }
            ],
        }

    def test_blank_response_rows_block_axis_progress(self) -> None:
        report = progress.build_report(
            "2026-05-16T13:00:00+09:00",
            membership_verifier=self.membership_verifier(),
            handoff_package=self.handoff_package(),
            response_validator={
                "status": "BLOCK_AXIS_WIDE_MEMBERSHIP_RESPONSE",
                "valid_rows": [],
                "blocked_rows": [{"axis": "kis_us_stocks"}],
                "next_safe_action": "fill enough replacement rows",
                "replacement_coverage_rows": [
                    {
                        "axis": "kis_us_stocks",
                        "required_replacement_row_count": 95,
                        "valid_replacement_row_count": 0,
                        "remaining_replacement_row_count": 95,
                        "replacement_coverage_sufficient": False,
                    }
                ],
            },
            import_report={"status": "BLOCK_AXIS_WIDE_MEMBERSHIP_IMPORT", "append_plan": []},
        )

        self.assertEqual(report["status"], "BLOCK_AXIS_WIDE_MEMBERSHIP_COVERAGE_PROGRESS")
        self.assertEqual(report["ready_axis_count"], 0)
        self.assertEqual(report["blocked_axis_count"], 1)
        self.assertEqual(report["blocked_response_row_count"], 1)
        self.assertIn("blocked_axes_present", report["blockers"])
        self.assertIn("no_valid_axis_wide_response_rows", report["blockers"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertEqual(report["axis_rows"][0]["remaining_replacement_row_count"], 95)
        self.assertEqual(report["single_next_action"], "fill enough replacement rows")
        self.assertEqual(
            report["axis_rows"][0]["remaining_required_action"],
            "Fill authoritative/licensed membership response rows for this axis.",
        )

    def test_import_review_ready_is_partial_progress_without_mutating(self) -> None:
        target = r"C:\AI\data_snapshots\kis_pit_membership\kis_us_stocks_membership_intervals.csv"
        report = progress.build_report(
            "2026-05-16T13:00:00+09:00",
            membership_verifier=self.membership_verifier(),
            handoff_package=self.handoff_package(),
            response_validator={
                "status": "READY_AXIS_WIDE_MEMBERSHIP_IMPORT_REVIEW",
                "valid_rows": [{"axis": "kis_us_stocks"}],
                "blocked_rows": [],
            },
            import_report={
                "status": "DRY_RUN_READY_FOR_AXIS_WIDE_MEMBERSHIP_IMPORT",
                "append_plan": [{"target_file": target, "row_count": 1, "appended_row_count": 0}],
            },
        )

        self.assertEqual(report["status"], "PARTIAL_AXIS_WIDE_MEMBERSHIP_PROGRESS")
        self.assertEqual(report["import_review_ready_axis_count"], 1)
        self.assertEqual(report["blocked_axis_count"], 0)
        self.assertEqual(report["valid_response_row_count"], 1)
        self.assertEqual(report["axis_rows"][0]["status"], "IMPORT_REVIEW_READY")
        self.assertEqual(report["axis_rows"][0]["import_plan_row_count"], 1)
        self.assertEqual(
            report["single_next_action"],
            "Review and apply axis-wide membership import with the guarded confirmation phrase.",
        )

    def test_replace_caveated_import_review_ready_is_partial_progress(self) -> None:
        target = r"C:\AI\data_snapshots\kis_pit_membership\kis_us_stocks_membership_intervals.csv"
        report = progress.build_report(
            "2026-05-16T13:00:00+09:00",
            membership_verifier=self.membership_verifier(),
            handoff_package=self.handoff_package(),
            response_validator={
                "status": "READY_AXIS_WIDE_MEMBERSHIP_IMPORT_REVIEW",
                "valid_rows": [{"axis": "kis_us_stocks"}],
                "blocked_rows": [],
            },
            import_report={
                "status": "DRY_RUN_READY_FOR_AXIS_WIDE_MEMBERSHIP_REPLACE_CAVEATED_IMPORT",
                "append_plan": [
                    {
                        "target_file": target,
                        "row_count": 95,
                        "appended_row_count": 0,
                        "replace_caveated_axis": True,
                    }
                ],
            },
        )

        self.assertEqual(report["status"], "PARTIAL_AXIS_WIDE_MEMBERSHIP_PROGRESS")
        self.assertEqual(report["axis_rows"][0]["status"], "IMPORT_REVIEW_READY")

    def test_verified_axis_is_operation_ready(self) -> None:
        report = progress.build_report(
            "2026-05-16T13:00:00+09:00",
            membership_verifier=self.membership_verifier(verified=True),
            handoff_package=self.handoff_package(),
            response_validator={"status": "READY_AXIS_WIDE_MEMBERSHIP_IMPORT_REVIEW", "valid_rows": [], "blocked_rows": []},
            import_report={"status": "BLOCK_AXIS_WIDE_MEMBERSHIP_IMPORT", "append_plan": []},
        )

        self.assertEqual(report["status"], "BLOCK_AXIS_WIDE_MEMBERSHIP_COVERAGE_PROGRESS")
        self.assertEqual(report["ready_axis_count"], 1)
        self.assertEqual(report["blocked_axis_count"], 0)
        self.assertEqual(report["axis_rows"][0]["status"], "COMPLETE_OPERATION_READY")
        self.assertIn("not_all_axes_operation_ready", report["blockers"])

    def test_markdown_renders_axis_table(self) -> None:
        report = progress.build_report(
            "2026-05-16T13:00:00+09:00",
            membership_verifier=self.membership_verifier(),
            handoff_package=self.handoff_package(),
            response_validator={
                "status": "BLOCK_AXIS_WIDE_MEMBERSHIP_RESPONSE",
                "valid_rows": [],
                "blocked_rows": [{"axis": "kis_us_stocks"}],
            },
            import_report={"status": "BLOCK_AXIS_WIDE_MEMBERSHIP_IMPORT", "append_plan": []},
        )
        md = progress.render_md(report)

        self.assertIn("KIS Axis-Wide Membership Coverage Progress", md)
        self.assertIn("kis_us_stocks", md)
        self.assertIn("BLOCK_RESPONSE_REQUIRED", md)


if __name__ == "__main__":
    unittest.main()
