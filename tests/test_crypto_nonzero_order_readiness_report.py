from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_crypto_nonzero_order_readiness_report.py")
SPEC = importlib.util.spec_from_file_location("build_crypto_nonzero_order_readiness_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
crypto_readiness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(crypto_readiness)


class CryptoNonzeroOrderReadinessReportTests(unittest.TestCase):
    def test_report_blocks_flat_hold_without_enabling_order_paths(self) -> None:
        report = crypto_readiness.build_report(
            {
                "simulated_orders": [
                    {
                        "asset": "crypto",
                        "symbol": "KRW-BTC",
                        "variant": "bridge_28_relief",
                        "action": "HOLD",
                        "target_weight": 0.0,
                        "delta_weight": 0.0,
                        "reason": "btc_model_signal_flat",
                        "executable": True,
                    }
                ],
                "live_enabled_flag": False,
                "real_orders": 0,
                "private_submit_used": False,
            },
            {
                "evidence": {
                    "signal_evidence": {
                        "current_order_actions": ["HOLD"],
                        "current_signal_sides": ["flat"],
                    },
                    "combined_evidence": {
                        "combined_non_flat_signal_count": 2,
                        "combined_executable_order_evidence_count": 2,
                    },
                }
            },
            {"suggested_sleeves": [{"lane": "bithumb_crypto", "candidate_id": "bridge_28_relief"}]},
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["current_order_candidate"]["has_nonzero_order"])
        self.assertIn("CURRENT_CRYPTO_ACTION_NOT_BUY_OR_SELL", report["blockers"])
        self.assertIn("CURRENT_CRYPTO_TARGET_WEIGHT_ZERO", report["blockers"])
        self.assertIn("CURRENT_CRYPTO_DELTA_WEIGHT_ZERO", report["blockers"])
        self.assertFalse(report["safety"]["does_call_bithumb_api"])
        self.assertFalse(report["safety"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["safety"]["private_submit_allowed_by_this_report"])
        self.assertFalse(report["safety"]["real_orders_allowed_by_this_report"])

    def test_report_is_ready_for_recheck_with_nonzero_buy_signal(self) -> None:
        report = crypto_readiness.build_report(
            {
                "simulated_orders": [
                    {
                        "asset": "crypto",
                        "symbol": "KRW-BTC",
                        "variant": "bridge_28_relief",
                        "action": "BUY",
                        "target_weight": 0.15,
                        "delta_weight": 0.15,
                        "reason": "btc_model_signal_long",
                        "executable": True,
                    }
                ],
                "live_enabled_flag": False,
                "real_orders": 0,
                "private_submit_used": False,
            },
            {},
            {},
        )

        self.assertEqual(report["status"], "READY_FOR_CRYPTO_PREFLIGHT_RECHECK")
        self.assertTrue(report["current_order_candidate"]["has_nonzero_order"])
        self.assertEqual(report["blockers"], [])


if __name__ == "__main__":
    unittest.main()
