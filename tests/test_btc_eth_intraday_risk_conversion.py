from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_risk_conversion.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_risk_conversion", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
risk = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(risk)


class BtcEthIntradayRiskConversionTests(unittest.TestCase):
    def test_exposure_cap_reduces_mdd_to_target(self) -> None:
        cap = risk.exposure_cap_for_mdd(-0.24, target_mdd_abs=0.12)

        self.assertAlmostEqual(cap, 0.5)

    def test_report_keeps_all_order_permissions_false(self) -> None:
        original = risk.read_json
        try:
            risk.read_json = lambda _path, _default: {
                "status": "OOS_WALKFORWARD_PASS",
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "market": "KRW-BTC",
                "timeframe": "4h",
                "aggregate": {
                    "pass_fold_count": 2,
                    "positive_fold_count": 2,
                    "worst_fold_mdd": -0.16,
                    "average_fold_cagr": 0.08,
                    "total_trade_count": 74,
                },
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
        self.assertEqual(report["next_gate"], "G07_SHADOW_REVIEW_RESEARCH_ONLY")
        self.assertFalse(report["no_order_assertions"]["promotion_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
