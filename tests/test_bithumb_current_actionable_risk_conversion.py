from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_risk_conversion.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_risk_conversion", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
risk = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(risk)


class BithumbCurrentActionableRiskConversionTests(unittest.TestCase):
    def test_exposure_cap_reduces_mdd_to_target(self) -> None:
        cap = risk.exposure_cap_for_mdd(-0.40, target_mdd_abs=0.20)

        self.assertAlmostEqual(cap, 0.5)

    def test_report_keeps_all_order_permissions_false(self) -> None:
        original = risk.read_json
        try:
            risk.read_json = lambda _path, _default: {
                "status": "BACKTEST_SCREEN_COMPLETE",
                "screens": [
                    {
                        "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
                        "parent_candidate_id": "bithumb_current_actionable_pola_1d_long",
                        "market": "KRW-POLA",
                        "timeframe": "1d",
                        "status": "BACKTEST_SCREEN_ITERATE",
                        "metrics": {
                            "cagr": 0.42,
                            "total_return": 0.21,
                            "mdd": -0.40,
                            "trade_count": 11,
                            "profit_factor": 1.79,
                        },
                    }
                ],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            }
            report = risk.build_report()
        finally:
            risk.read_json = original

        self.assertEqual(report["status"], "READY_FOR_GATEKEEPER_REVIEW")
        self.assertEqual(report["pass_count"], 1)
        self.assertEqual(report["top_conversion"]["next_gate"], "G05_GATEKEEPER_REVIEW_RESEARCH_ONLY")
        self.assertFalse(report["no_order_assertions"]["promotion_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_weak_return_after_cap_stays_iterate(self) -> None:
        converted = risk.convert_screen(
            {
                "candidate_id": "weak",
                "market": "KRW-WEAK",
                "timeframe": "1d",
                "metrics": {
                    "cagr": 0.16,
                    "total_return": 0.08,
                    "mdd": -0.40,
                    "trade_count": 12,
                    "profit_factor": 1.8,
                },
            }
        )

        self.assertEqual(converted["status"], "RISK_CONVERSION_ITERATE")
        self.assertEqual(converted["next_gate"], "G03_RESEARCH_ITERATE")


if __name__ == "__main__":
    unittest.main()
