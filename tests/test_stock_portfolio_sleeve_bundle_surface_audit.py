from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_portfolio_sleeve_bundle_surface_audit.py")
SPEC = importlib.util.spec_from_file_location("build_stock_portfolio_sleeve_bundle_surface_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class StockPortfolioSleeveBundleSurfaceAuditTests(unittest.TestCase):
    def safe_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def sources(self) -> dict[str, dict]:
        item = {
            "decision_id": audit.DECISION_ID,
            "exact_phrase_to_record": audit.EXACT_PHRASE,
            "covered": True,
            "unsafe": False,
        }
        bundle = {
            "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
            "exact_phrase_to_record": audit.EXACT_PHRASE,
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": self.safe_assertions(),
        }
        return {
            "bundle": bundle,
            "board": {"items": [item]},
            "phrase": {"ready_phrases": [item]},
            "priority": {"ready_decisions": [item]},
            "queue": {"queue": [{"source_decision_id": audit.DECISION_ID}]},
            "coverage": {"coverage_rows": [item]},
            "dashboard": {
                "stock_portfolio_sleeve_gatekeeper_bundle_review": {
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "no_order_assertions": self.safe_assertions(),
                }
            },
            "public": {
                "stock_portfolio_sleeve_gatekeeper_bundle_review": {
                    "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                    "real_orders_allowed_by_this_report": False,
                }
            },
        }

    def test_passes_when_bundle_is_visible_everywhere(self) -> None:
        report = audit.build_report(self.sources())

        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["ready_for_review_surface"])
        self.assertEqual(report["blockers"], [])
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_fails_when_public_surface_is_missing(self) -> None:
        sources = self.sources()
        sources["public"]["stock_portfolio_sleeve_gatekeeper_bundle_review"] = {}

        report = audit.build_report(sources)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("PUBLIC_CONTAINS_BUNDLE", report["blockers"])
        self.assertFalse(report["ready_for_review_surface"])


if __name__ == "__main__":
    unittest.main()
