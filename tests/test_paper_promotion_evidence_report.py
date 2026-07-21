from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_paper_promotion_evidence_report.py")
SPEC = importlib.util.spec_from_file_location("build_paper_promotion_evidence_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
paper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(paper)


class PaperPromotionEvidenceReportTests(unittest.TestCase):
    def test_historical_replay_promotion_flag_becomes_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paper.PAPER_LOOP = root / "paper_loop.json"
            paper.PAPER_REPORT = root / "paper_report.json"
            paper.ACCELERATION_REPORT = root / "acceleration.json"
            paper.RISK_GUARD = root / "risk.json"
            paper.DATA_GUARD = root / "data.json"
            paper.PORTFOLIO_REVIEW = root / "portfolio.json"

            paper.PAPER_LOOP.write_text(json.dumps({"last_status": "ok", "cycles_completed": 288}), encoding="utf-8")
            paper.PAPER_REPORT.write_text(
                json.dumps(
                    {
                        "profile": "small_account_growth_paper",
                        "live_enabled_flag": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                    }
                ),
                encoding="utf-8",
            )
            paper.ACCELERATION_REPORT.write_text(
                json.dumps(
                    {
                        "summary": {
                            "eligible_non_flat_signal_count": 5,
                            "virtual_executable_order_count": 5,
                            "seen_signal_count": 288,
                        },
                        "historical_replay": {
                            "non_flat_count": 999,
                            "counts_as_live_paper_evidence": True,
                        },
                    }
                ),
                encoding="utf-8",
            )
            paper.RISK_GUARD.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
            paper.DATA_GUARD.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
            paper.PORTFOLIO_REVIEW.write_text(json.dumps({"portfolio_summary": {"status": "PASS"}}), encoding="utf-8")

            report = paper.build_report()

        self.assertEqual(report["decision"], "DEMOTION_REVIEW")
        self.assertIn("HISTORICAL_REPLAY_MARKED_AS_PROMOTION_EVIDENCE", report["blockers"])
        self.assertFalse(report["evidence_gaps"])
        self.assertEqual(
            report["evidence"]["acceleration_evidence"]["historical_replay_non_flat_count_excluded"],
            999,
        )

    def test_historical_replay_count_is_excluded_from_combined_promotion_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paper.PAPER_LOOP = root / "paper_loop.json"
            paper.PAPER_REPORT = root / "paper_report.json"
            paper.ACCELERATION_REPORT = root / "acceleration.json"
            paper.RISK_GUARD = root / "risk.json"
            paper.DATA_GUARD = root / "data.json"
            paper.PORTFOLIO_REVIEW = root / "portfolio.json"

            paper.PAPER_LOOP.write_text(json.dumps({"last_status": "ok", "cycles_completed": 288}), encoding="utf-8")
            paper.PAPER_REPORT.write_text(
                json.dumps(
                    {
                        "profile": "small_account_growth_paper",
                        "live_enabled_flag": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                        "targets": [],
                        "simulated_orders": [],
                    }
                ),
                encoding="utf-8",
            )
            paper.ACCELERATION_REPORT.write_text(
                json.dumps(
                    {
                        "summary": {
                            "eligible_non_flat_signal_count": 2,
                            "virtual_executable_order_count": 2,
                            "seen_signal_count": 288,
                        },
                        "historical_replay": {
                            "non_flat_count": 999,
                            "counts_as_live_paper_evidence": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            paper.RISK_GUARD.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
            paper.DATA_GUARD.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
            paper.PORTFOLIO_REVIEW.write_text(json.dumps({"portfolio_summary": {"status": "PASS"}}), encoding="utf-8")

            report = paper.build_report()

        self.assertEqual(report["decision"], "KEEP_PAPER_COLLECT_EVIDENCE")
        self.assertEqual(report["evidence"]["combined_evidence"]["combined_non_flat_signal_count"], 2)
        self.assertEqual(report["evidence"]["combined_evidence"]["combined_executable_order_evidence_count"], 2)
        self.assertEqual(report["evidence"]["evidence_deficit"]["non_flat_signals_missing"], 3)
        self.assertEqual(report["evidence"]["evidence_deficit"]["executable_orders_missing"], 3)
        self.assertEqual(report["replay_policy"]["historical_replay_non_flat_count_excluded"], 999)
        self.assertTrue(report["replay_policy"]["historical_replay_excluded"])
        self.assertIn("INSUFFICIENT_NON_FLAT_SIGNAL_EVIDENCE", report["evidence_gaps"])
        self.assertIn("INSUFFICIENT_EXECUTABLE_ORDER_EVIDENCE", report["evidence_gaps"])

    def test_cycle_deficit_blocks_until_paper_loop_cycle_threshold_is_met(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paper.PAPER_LOOP = root / "paper_loop.json"
            paper.PAPER_REPORT = root / "paper_report.json"
            paper.ACCELERATION_REPORT = root / "acceleration.json"
            paper.RISK_GUARD = root / "risk.json"
            paper.DATA_GUARD = root / "data.json"
            paper.PORTFOLIO_REVIEW = root / "portfolio.json"

            paper.PAPER_LOOP.write_text(json.dumps({"last_status": "ok", "cycles_completed": 280}), encoding="utf-8")
            paper.PAPER_REPORT.write_text(
                json.dumps(
                    {
                        "profile": "small_account_growth_paper",
                        "live_enabled_flag": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                    }
                ),
                encoding="utf-8",
            )
            paper.ACCELERATION_REPORT.write_text(
                json.dumps(
                    {
                        "summary": {
                            "eligible_non_flat_signal_count": 5,
                            "virtual_executable_order_count": 5,
                            "seen_signal_count": 288,
                        },
                        "historical_replay": {
                            "non_flat_count": 0,
                            "counts_as_live_paper_evidence": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            paper.RISK_GUARD.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
            paper.DATA_GUARD.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
            paper.PORTFOLIO_REVIEW.write_text(json.dumps({"portfolio_summary": {"status": "PASS"}}), encoding="utf-8")

            report = paper.build_report()

        deficit = report["evidence"]["evidence_deficit"]
        self.assertEqual(deficit["paper_loop_cycles_missing"], 8)
        self.assertEqual(deficit["review_cycle_evidence_count"], 288)
        self.assertEqual(deficit["review_cycle_evidence_missing"], 0)
        self.assertEqual(report["decision"], "KEEP_PAPER_COLLECT_EVIDENCE")
        self.assertIn("INSUFFICIENT_PAPER_CYCLES", report["evidence_gaps"])

    def test_activation_packet_blocked_cycle_is_collect_evidence_not_loop_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paper.PAPER_LOOP = root / "paper_loop.json"
            paper.PAPER_REPORT = root / "paper_report.json"
            paper.ACCELERATION_REPORT = root / "acceleration.json"
            paper.RISK_GUARD = root / "risk.json"
            paper.DATA_GUARD = root / "data.json"
            paper.PORTFOLIO_REVIEW = root / "portfolio.json"

            paper.PAPER_LOOP.write_text(
                json.dumps(
                    {
                        "last_status": "fail",
                        "cycles_completed": 252,
                        "executor_safety": {
                            "status": "blocked",
                            "real_orders": 0,
                            "broker_submit_allowed": True,
                            "broker_submit_scope": "paper_only",
                            "private_submit_used": False,
                            "live_enabled_flag": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            paper.PAPER_REPORT.write_text(
                json.dumps(
                    {
                        "profile": "small_account_growth_paper",
                        "status": "blocked",
                        "live_enabled_flag": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                        "broker_submit_allowed": True,
                        "broker_submit_scope": "paper_only",
                    }
                ),
                encoding="utf-8",
            )
            paper.ACCELERATION_REPORT.write_text(
                json.dumps(
                    {
                        "summary": {
                            "eligible_non_flat_signal_count": 52,
                            "virtual_executable_order_count": 52,
                            "seen_signal_count": 688,
                        },
                        "historical_replay": {
                            "non_flat_count": 7621,
                            "counts_as_live_paper_evidence": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            paper.RISK_GUARD.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
            paper.DATA_GUARD.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
            paper.PORTFOLIO_REVIEW.write_text(json.dumps({"portfolio_summary": {"status": "PASS"}}), encoding="utf-8")

            report = paper.build_report()

        self.assertEqual(report["decision"], "KEEP_PAPER_COLLECT_EVIDENCE")
        self.assertNotIn("PAPER_LOOP_NOT_OK", report["blockers"])
        self.assertEqual(report["evidence"]["evidence_deficit"]["paper_loop_cycles_missing"], 36)

    def test_risk_guard_freshness_warn_is_not_promotion_blocker_when_hard_safety_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paper.PAPER_LOOP = root / "paper_loop.json"
            paper.PAPER_REPORT = root / "paper_report.json"
            paper.ACCELERATION_REPORT = root / "acceleration.json"
            paper.RISK_GUARD = root / "risk.json"
            paper.DATA_GUARD = root / "data.json"
            paper.PORTFOLIO_REVIEW = root / "portfolio.json"

            paper.PAPER_LOOP.write_text(json.dumps({"last_status": "ok", "cycles_completed": 252}), encoding="utf-8")
            paper.PAPER_REPORT.write_text(
                json.dumps(
                    {
                        "profile": "small_account_growth_paper",
                        "live_enabled_flag": False,
                        "private_submit_used": False,
                        "real_orders": 0,
                        "broker_submit_allowed": True,
                        "broker_submit_scope": "paper_only",
                    }
                ),
                encoding="utf-8",
            )
            paper.ACCELERATION_REPORT.write_text(
                json.dumps(
                    {
                        "summary": {
                            "eligible_non_flat_signal_count": 52,
                            "virtual_executable_order_count": 52,
                            "seen_signal_count": 688,
                        },
                        "historical_replay": {
                            "non_flat_count": 7621,
                            "counts_as_live_paper_evidence": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            paper.RISK_GUARD.write_text(
                json.dumps(
                    {
                        "status": "WARN",
                        "halt_count": 0,
                        "warn_count": 1,
                        "checks": [
                            {"name": "live_disabled", "status": "PASS"},
                            {"name": "private_submit_unused", "status": "PASS"},
                            {"name": "real_orders_zero", "status": "PASS"},
                            {"name": "broker_submit_scope", "status": "PASS"},
                            {"name": "latest_run", "status": "WARN"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            paper.DATA_GUARD.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
            paper.PORTFOLIO_REVIEW.write_text(json.dumps({"portfolio_summary": {"status": "PASS"}}), encoding="utf-8")

            report = paper.build_report()

        self.assertEqual(report["decision"], "KEEP_PAPER_COLLECT_EVIDENCE")
        self.assertEqual(report["blockers"], [])
        self.assertTrue(report["evidence"]["risk_guard_hard_safety_ok"])
        self.assertIn("INSUFFICIENT_PAPER_CYCLES", report["evidence_gaps"])

    def test_risk_guard_hard_safety_failure_remains_promotion_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paper.PAPER_LOOP = root / "paper_loop.json"
            paper.PAPER_REPORT = root / "paper_report.json"
            paper.ACCELERATION_REPORT = root / "acceleration.json"
            paper.RISK_GUARD = root / "risk.json"
            paper.DATA_GUARD = root / "data.json"
            paper.PORTFOLIO_REVIEW = root / "portfolio.json"

            paper.PAPER_LOOP.write_text(json.dumps({"last_status": "ok", "cycles_completed": 288}), encoding="utf-8")
            paper.PAPER_REPORT.write_text(
                json.dumps({"profile": "small_account_growth_paper", "live_enabled_flag": False, "private_submit_used": False, "real_orders": 0}),
                encoding="utf-8",
            )
            paper.ACCELERATION_REPORT.write_text(
                json.dumps(
                    {
                        "summary": {
                            "eligible_non_flat_signal_count": 5,
                            "virtual_executable_order_count": 5,
                            "seen_signal_count": 288,
                        },
                        "historical_replay": {"counts_as_live_paper_evidence": False},
                    }
                ),
                encoding="utf-8",
            )
            paper.RISK_GUARD.write_text(
                json.dumps(
                    {
                        "status": "HALT_RECOMMENDED",
                        "halt_count": 1,
                        "checks": [{"name": "real_orders_zero", "status": "HALT"}],
                    }
                ),
                encoding="utf-8",
            )
            paper.DATA_GUARD.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
            paper.PORTFOLIO_REVIEW.write_text(json.dumps({"portfolio_summary": {"status": "PASS"}}), encoding="utf-8")

            report = paper.build_report()

        self.assertEqual(report["decision"], "DEMOTION_REVIEW")
        self.assertIn("RISK_GUARD_HARD_SAFETY_NOT_PASS", report["blockers"])
        self.assertFalse(report["evidence"]["risk_guard_hard_safety_ok"])


if __name__ == "__main__":
    unittest.main()
