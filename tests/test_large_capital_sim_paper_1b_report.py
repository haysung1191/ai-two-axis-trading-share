from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_large_capital_sim_paper_1b_report.py")
SPEC = importlib.util.spec_from_file_location("build_large_capital_sim_paper_1b_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
large_sim = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = large_sim
SPEC.loader.exec_module(large_sim)


class LargeCapitalSimPaper1BReportTests(unittest.TestCase):
    def test_builds_review_only_1b_profile_from_portfolio_sleeves(self) -> None:
        report = large_sim.build_report(
            {
                "suggested_sleeves": [
                    {
                        "candidate_id": "crypto_a",
                        "asset_class": "BITHUMB_KRW_CRYPTO_MULTI",
                        "lane": "bithumb_crypto",
                        "status": "VALIDATION_QUEUE",
                        "promotion_permission": "MAY_ENTER_VALIDATION",
                        "model_cagr": 0.25,
                        "model_mdd": -0.10,
                        "model_mdd_abs": 0.10,
                        "model_sharpe": 1.5,
                        "suggested_account_weight": 0.2,
                    }
                ]
            },
            {"queue": []},
            {"top_oos": {"candidate_id": "crypto_oos", "market": "KRW-ORCA", "source_conversion": {"estimated_cagr": 1.2}}},
            {"status": "WARN"},
            {"live_enabled": False, "paper_enabled": False},
        )

        self.assertEqual(report["status"], "READY_FOR_SIM_REVIEW")
        self.assertEqual(report["profile"], "large_capital_sim_paper_1b")
        self.assertEqual(report["sleeves"][0]["sim_notional_krw"], 200000000.0)
        self.assertEqual(report["summary"]["expected_account_cagr_linear"], 0.05)
        self.assertFalse(report["safety"]["counts_as_paper_or_live_readiness"])
        self.assertFalse(report["safety"]["live_allowed_by_this_report"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_blocks_without_portfolio_sleeves(self) -> None:
        report = large_sim.build_report({}, {}, {}, {"status": "PASS"}, {"live_enabled": False})

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("NO_PORTFOLIO_SLEEVES", report["blockers"])
        self.assertFalse(report["safety"]["broker_submit_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
