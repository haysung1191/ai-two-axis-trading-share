from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_operational_monitor_report.py")
SPEC = importlib.util.spec_from_file_location("build_operational_monitor_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
monitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(monitor)


class OperationalMonitorReportTests(unittest.TestCase):
    def test_stale_velocity_monitor_warns_when_older_than_sources(self) -> None:
        warnings = monitor.stale_derived_report_warnings(
            [
                {
                    "name": "paper_evidence_velocity_monitor",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T01:00:00+00:00",
                },
                {
                    "name": "paper_promotion_evidence",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T01:01:00+00:00",
                },
                {
                    "name": "paper_evidence_acceleration",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T00:59:00+00:00",
                },
            ]
        )

        self.assertIn(
            "STALE_DERIVED_REPORT:paper_evidence_velocity_monitor:OLDER_THAN:paper_promotion_evidence",
            warnings,
        )

    def test_fresh_velocity_monitor_does_not_warn(self) -> None:
        warnings = monitor.stale_derived_report_warnings(
            [
                {
                    "name": "paper_evidence_velocity_monitor",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T01:02:00+00:00",
                },
                {
                    "name": "paper_promotion_evidence",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T01:01:00+00:00",
                },
                {
                    "name": "paper_evidence_acceleration",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T01:01:30+00:00",
                },
            ]
        )

        self.assertEqual(warnings, [])

    def test_small_timestamp_race_does_not_warn(self) -> None:
        warnings = monitor.stale_derived_report_warnings(
            [
                {
                    "name": "paper_evidence_velocity_monitor",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T01:00:00+00:00",
                },
                {
                    "name": "paper_promotion_evidence",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T01:00:05+00:00",
                },
            ]
        )

        self.assertEqual(warnings, [])

    def test_stale_public_export_warns_when_older_than_dashboard(self) -> None:
        warnings = monitor.stale_derived_report_warnings(
            [
                {
                    "name": "pipeline_dashboard",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:10:00+00:00",
                },
                {
                    "name": "public_dashboard_export",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:09:00+00:00",
                },
            ]
        )

        self.assertIn(
            "STALE_DERIVED_REPORT:public_dashboard_export:OLDER_THAN:pipeline_dashboard",
            warnings,
        )

    def test_stale_model_factory_warns_when_older_than_paper_evidence(self) -> None:
        warnings = monitor.stale_derived_report_warnings(
            [
                {
                    "name": "model_factory_pull_through",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:00:00+00:00",
                },
                {
                    "name": "paper_promotion_evidence",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:01:00+00:00",
                },
                {
                    "name": "paper_evidence_velocity_monitor",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:01:00+00:00",
                },
            ]
        )

        self.assertIn(
            "STALE_DERIVED_REPORT:model_factory_pull_through:OLDER_THAN:paper_promotion_evidence",
            warnings,
        )

    def test_stale_stock_risk_conversion_queue_warns_when_older_than_pull_through(self) -> None:
        warnings = monitor.stale_derived_report_warnings(
            [
                {
                    "name": "stock_risk_conversion_queue",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:00:00+00:00",
                },
                {
                    "name": "model_factory_pull_through",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:01:00+00:00",
                },
                {
                    "name": "realtime_risk_guard",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:00:30+00:00",
                },
            ]
        )

        self.assertIn(
            "STALE_DERIVED_REPORT:stock_risk_conversion_queue:OLDER_THAN:model_factory_pull_through",
            warnings,
        )

    def test_stale_model_factory_experiment_queue_warns_when_older_than_queue_sources(self) -> None:
        warnings = monitor.stale_derived_report_warnings(
            [
                {
                    "name": "model_factory_experiment_queue",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:00:00+00:00",
                },
                {
                    "name": "model_factory_pull_through",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:01:00+00:00",
                },
                {
                    "name": "stock_risk_conversion_queue",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:01:00+00:00",
                },
                {
                    "name": "realtime_risk_guard",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:00:30+00:00",
                },
            ]
        )

        self.assertIn(
            "STALE_DERIVED_REPORT:model_factory_experiment_queue:OLDER_THAN:model_factory_pull_through",
            warnings,
        )
        self.assertIn(
            "STALE_DERIVED_REPORT:model_factory_experiment_queue:OLDER_THAN:stock_risk_conversion_queue",
            warnings,
        )

    def test_stale_queue_coverage_audit_warns_when_older_than_experiment_queue(self) -> None:
        warnings = monitor.stale_derived_report_warnings(
            [
                {
                    "name": "model_factory_queue_coverage_audit",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:00:00+00:00",
                },
                {
                    "name": "model_factory_experiment_queue",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:01:00+00:00",
                },
            ]
        )

        self.assertIn(
            "STALE_DERIVED_REPORT:model_factory_queue_coverage_audit:OLDER_THAN:model_factory_experiment_queue",
            warnings,
        )

    def test_stale_dashboard_warns_when_older_than_experiment_queue(self) -> None:
        warnings = monitor.stale_derived_report_warnings(
            [
                {
                    "name": "pipeline_dashboard",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:00:00+00:00",
                },
                {
                    "name": "model_factory_experiment_queue",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:01:00+00:00",
                },
            ]
        )

        self.assertIn(
            "STALE_DERIVED_REPORT:pipeline_dashboard:OLDER_THAN:model_factory_experiment_queue",
            warnings,
        )

    def test_stale_stock_conversion_packet_warns_when_older_than_queue(self) -> None:
        warnings = monitor.stale_derived_report_warnings(
            [
                {
                    "name": "stock_conversion_gatekeeper_review_packet",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:00:00+00:00",
                },
                {
                    "name": "stock_risk_conversion_queue",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:01:00+00:00",
                },
                {
                    "name": "model_factory_pull_through",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:00:30+00:00",
                },
                {
                    "name": "realtime_risk_guard",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:00:15+00:00",
                },
            ]
        )

        self.assertIn(
            "STALE_DERIVED_REPORT:stock_conversion_gatekeeper_review_packet:OLDER_THAN:stock_risk_conversion_queue",
            warnings,
        )

    def test_stale_live_preflight_reconfiguration_warns_when_older_than_lane_packets(self) -> None:
        warnings = monitor.stale_derived_report_warnings(
            [
                {
                    "name": "pipeline_live_preflight_reconfiguration",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:00:00+00:00",
                },
                {
                    "name": "crypto_live_preflight",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:01:00+00:00",
                },
                {
                    "name": "stock_live_preflight",
                    "exists": True,
                    "last_write_time_utc": "2026-05-03T02:00:30+00:00",
                },
            ]
        )

        self.assertIn(
            "STALE_DERIVED_REPORT:pipeline_live_preflight_reconfiguration:OLDER_THAN:crypto_live_preflight",
            warnings,
        )

    def test_report_status_reads_loop_summary_status_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            crypto_path = tmp_path / "crypto.json"
            latest_path = tmp_path / "latest.json"
            crypto_path.write_text(json.dumps({"last_cycle": {"status": "ok"}, "last_task_status": "ok"}), encoding="utf-8")
            latest_path.write_text(json.dumps({"loop_status": "green", "last_cycle_status": "ok"}), encoding="utf-8")

            self.assertEqual(monitor.report_status("crypto_recursive_improvement", crypto_path)["status"], "ok")
            self.assertEqual(monitor.report_status("latest_run_summary", latest_path)["status"], "ok")

    def test_report_status_treats_known_loop_partial_snapshot_as_initializing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop_path = Path(tmp) / "gatekeeper_dispatch_loop_latest.json"
            loop_path.write_text(
                json.dumps({"generated_at_utc": "2026-05-03T11:30:00+00:00", "mode": "gatekeeper_dispatch_loop"}),
                encoding="utf-8",
            )

            status = monitor.report_status("gatekeeper_dispatch_loop", loop_path)

        self.assertEqual(status["status"], "INITIALIZING")

    def test_known_loop_initializing_snapshot_is_not_actionable_warning(self) -> None:
        statuses = [
            {"name": "gatekeeper_dispatch_loop", "exists": True, "status": "INITIALIZING"},
            {"name": "goal_requirement_checklist", "exists": True, "status": "NOT_COMPLETE"},
        ]
        with (
            patch.object(monitor, "process_snapshot", return_value=[]),
            patch.object(monitor, "report_status", side_effect=statuses),
            patch.object(
                monitor,
                "REPORTS",
                {
                    "gatekeeper_dispatch_loop": Path("gatekeeper_dispatch_loop_latest.json"),
                    "goal_requirement_checklist": Path("goal_requirement_checklist.json"),
                },
            ),
            patch.object(monitor, "EXPECTED_PROCESS_PATTERNS", []),
        ):
            report = monitor.build_report()

        self.assertNotIn("UNKNOWN_STATUS:gatekeeper_dispatch_loop", report["warnings"])
        self.assertEqual(report["actionable_warnings"], [])

    def test_build_report_warns_on_existing_unknown_status(self) -> None:
        statuses = [
            {"name": "known_report", "exists": True, "status": "PASS"},
            {"name": "unknown_report", "exists": True, "status": "UNKNOWN"},
            {"name": "goal_requirement_checklist", "exists": True, "status": "NOT_COMPLETE"},
        ]
        with (
            patch.object(monitor, "process_snapshot", return_value=[]),
            patch.object(monitor, "report_status", side_effect=statuses),
            patch.object(
                monitor,
                "REPORTS",
                {
                    "known_report": Path("known.json"),
                    "unknown_report": Path("unknown.json"),
                    "goal_requirement_checklist": Path("goal_requirement_checklist.json"),
                },
            ),
            patch.object(monitor, "EXPECTED_PROCESS_PATTERNS", []),
        ):
            report = monitor.build_report()

        self.assertIn("UNKNOWN_STATUS:unknown_report", report["warnings"])
        self.assertIn("NON_PASS_STATUS:goal_requirement_checklist:NOT_COMPLETE", report["warnings"])
        self.assertIn("UNKNOWN_STATUS:unknown_report", report["actionable_warnings"])
        self.assertIn(
            "NON_PASS_STATUS:goal_requirement_checklist:NOT_COMPLETE",
            report["expected_collect_evidence_warnings"],
        )

    def test_classify_warnings_separates_expected_collection_state_from_actionable(self) -> None:
        classified = monitor.classify_warnings(
            [
                "NON_PASS_STATUS:paper_promotion_evidence:KEEP_PAPER_COLLECT_EVIDENCE",
                "NON_PASS_STATUS:realtime_risk_guard:WARN",
                "NON_PASS_STATUS:capital_allocator_decision:KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE",
                "NON_PASS_STATUS:goal_requirement_checklist:NOT_COMPLETE",
                "NON_PASS_STATUS:crypto_live_preflight:BLOCKED",
                "NON_PASS_STATUS:stock_live_preflight:BLOCKED",
                "NON_PASS_STATUS:pipeline_live_preflight_reconfiguration:RECONFIGURED_WITH_BLOCKERS",
                "STALE_DERIVED_REPORT:public_dashboard_export:OLDER_THAN:pipeline_dashboard",
                "MISSING_PROCESS:run_gatekeeper_refresh_loop.py",
            ]
        )

        self.assertEqual(len(classified["expected_collect_evidence_warnings"]), 7)
        self.assertEqual(len(classified["actionable_warnings"]), 2)
        self.assertIn(
            "STALE_DERIVED_REPORT:public_dashboard_export:OLDER_THAN:pipeline_dashboard",
            classified["actionable_warnings"],
        )

    def test_risk_freshness_only_paper_demotion_is_expected_collection_state(self) -> None:
        risk = {
            "status": "WARN",
            "halt_count": 0,
            "checks": [
                {"name": "live_disabled", "status": "PASS"},
                {"name": "private_submit_unused", "status": "PASS"},
                {"name": "real_orders_zero", "status": "PASS"},
                {"name": "broker_submit_scope", "status": "PASS"},
                {"name": "latest_run", "status": "WARN"},
            ],
        }
        paper = {"blockers": ["RISK_GUARD_NOT_PASS"]}
        statuses = [
            {"name": "paper_promotion_evidence", "exists": True, "status": "DEMOTION_REVIEW"},
            {"name": "realtime_risk_guard", "exists": True, "status": "WARN"},
        ]
        with (
            patch.object(monitor, "process_snapshot", return_value=[]),
            patch.object(monitor, "report_status", side_effect=statuses),
            patch.object(
                monitor,
                "REPORTS",
                {
                    "paper_promotion_evidence": Path("paper_promotion_evidence.json"),
                    "realtime_risk_guard": Path("realtime_risk_guard.json"),
                },
            ),
            patch.object(monitor, "EXPECTED_PROCESS_PATTERNS", []),
            patch.object(monitor, "read_json", side_effect=[risk, paper]),
        ):
            report = monitor.build_report()

        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["actionable_warnings"], [])
        self.assertIn(
            "NON_PASS_STATUS:paper_promotion_evidence:DEMOTION_REVIEW",
            report["expected_collect_evidence_warnings"],
        )
        self.assertIn("NON_PASS_STATUS:realtime_risk_guard:WARN", report["expected_collect_evidence_warnings"])


if __name__ == "__main__":
    unittest.main()
