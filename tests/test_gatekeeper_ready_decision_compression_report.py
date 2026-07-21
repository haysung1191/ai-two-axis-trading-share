from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_gatekeeper_ready_decision_compression_report.py")
SPEC = importlib.util.spec_from_file_location("build_gatekeeper_ready_decision_compression_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
compression = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compression)


class GatekeeperReadyDecisionCompressionReportTests(unittest.TestCase):
    def priority_packet(self) -> dict:
        decisions = [
            {"decision_id": decision_id, "lane": "portfolio"}
            for decision_id in compression.PORTFOLIO_SOURCE_DECISIONS
        ]
        decisions.append({"decision_id": "stock_portfolio_sleeve_gatekeeper_bundle_review", "lane": "portfolio"})
        decisions.append({"decision_id": "paper_smoke_review", "lane": "portfolio"})
        return {
            "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
            "ready_decisions": decisions,
        }

    def audit_packet(self) -> dict:
        return {"status": "PASS", "ready_for_review_surface": True}

    def test_compresses_portfolio_bundle_review(self) -> None:
        report = compression.build_report(self.priority_packet(), self.audit_packet())

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["ready_decision_count"], 11)
        self.assertEqual(report["compression_group_count"], 1)
        self.assertEqual(report["compressed_source_decision_count"], 9)
        self.assertEqual(report["estimated_review_rows_after_compression"], 3)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_when_bundle_audit_is_not_pass(self) -> None:
        report = compression.build_report(self.priority_packet(), {"status": "FAIL", "ready_for_review_surface": False})

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("PORTFOLIO_BUNDLE_NOT_READY_FOR_COMPRESSION", report["blockers"])


if __name__ == "__main__":
    unittest.main()
