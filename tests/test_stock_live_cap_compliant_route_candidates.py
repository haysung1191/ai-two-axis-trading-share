from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_live_cap_compliant_route_candidates.py")
SPEC = importlib.util.spec_from_file_location("build_stock_live_cap_compliant_route_candidates", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
routes = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(routes)


class StockLiveCapCompliantRouteCandidatesTests(unittest.TestCase):
    def test_builds_review_only_routes_for_oversized_min_lot(self) -> None:
        report = routes.build_report(
            {"approval_caps": {"stock_cap_krw": 100000, "max_order_krw": 10000}},
            {
                "status": "NO_CAP_COMPLIANT_ORDERS",
                "planned_count": 1,
                "cap_compliant_order_count": 0,
                "excluded_order_count": 1,
                "excluded_orders": [{"symbol": "DOW", "estimated_order_notional_krw": 60111.56}],
            },
            {
                "candidates": [
                    {
                        "candidate_id": "stock_a",
                        "lane": "kis_etfs",
                        "account_weight_from_portfolio_review": 0.02,
                        "estimated_cagr": 0.45,
                        "estimated_mdd": -0.19,
                    }
                ]
            },
        )

        self.assertEqual(report["status"], "ROUTE_CANDIDATES_READY_FOR_REVIEW")
        self.assertEqual(report["current_cap_fit"]["required_max_order_krw_for_current_plan"], 60112)
        self.assertEqual(len(report["route_candidates"]), 3)
        self.assertIn("STOCK_LIVE_ROUTE_NEEDS_CAP_COMPLIANT_RERANK_OR_HUMAN_CAP_REVIEW", report["blockers"])
        self.assertFalse(report["safety"]["live_allowed_by_this_report"])
        self.assertFalse(report["safety"]["broker_submit_allowed_by_this_report"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_reports_existing_cap_compliant_route_without_order_permission(self) -> None:
        report = routes.build_report(
            {"approval_caps": {"stock_cap_krw": 100000, "max_order_krw": 10000}},
            {
                "status": "HAS_CAP_COMPLIANT_ORDERS",
                "planned_count": 1,
                "cap_compliant_order_count": 1,
                "excluded_order_count": 0,
                "excluded_orders": [],
            },
            {"candidates": []},
        )

        self.assertEqual(report["status"], "HAS_CAP_COMPLIANT_ROUTE")
        self.assertEqual(report["blockers"], [])
        self.assertFalse(report["safety"]["real_orders_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
