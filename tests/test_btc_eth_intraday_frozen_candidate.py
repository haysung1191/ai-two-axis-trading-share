from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_frozen_candidate.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_frozen_candidate", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
frozen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(frozen)


class BtcEthIntradayFrozenCandidateTests(unittest.TestCase):
    def test_build_candidate_freezes_sweep_without_order_paths(self) -> None:
        candidate = frozen.build_candidate(
            {
                "candidate_id": "btc_eth_intraday_momentum_btc_4h",
                "market": "KRW-BTC",
                "timeframe": "4h",
                "best_parameters": {"momentum_threshold": 0.002},
                "best_metrics": {"cagr": 0.08, "mdd": -0.16, "trade_count": 77},
            }
        )

        self.assertEqual(candidate["candidate_id"], "btc_eth_intraday_momentum_btc_4h_sweep001")
        self.assertEqual(candidate["current_gate"], "G04_OOS_WALKFORWARD")
        self.assertEqual(candidate["status"], "READY_FOR_OOS_RESEARCH_REVIEW")
        self.assertFalse(candidate["promotion_allowed_by_this_report"])
        self.assertFalse(candidate["live_allowed_by_this_report"])
        self.assertFalse(candidate["broker_submit_allowed_by_this_report"])
        self.assertFalse(candidate["real_orders_allowed_by_this_report"])

    def test_report_requires_safe_sweep_before_freezing(self) -> None:
        original = frozen.read_json
        try:
            frozen.read_json = lambda _path, _default: {
                "pass_like_count": 1,
                "top_sweep": {
                    "candidate_id": "btc_eth_intraday_momentum_btc_4h",
                    "market": "KRW-BTC",
                    "timeframe": "4h",
                    "best_parameters": {"momentum_threshold": 0.002},
                    "best_metrics": {"cagr": 0.08, "mdd": -0.16, "trade_count": 77},
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
            report = frozen.build_report()
        finally:
            frozen.read_json = original

        self.assertEqual(report["status"], "READY_FOR_OOS_RESEARCH_REVIEW")
        self.assertEqual(report["frozen_candidate_count"], 1)
        self.assertFalse(report["no_order_assertions"]["promotion_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
