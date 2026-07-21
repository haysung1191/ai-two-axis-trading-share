from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_frozen_candidate.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_frozen_candidate", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
frozen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(frozen)


class BithumbCurrentActionableFrozenCandidateTests(unittest.TestCase):
    def test_build_candidate_freezes_current_actionable_without_order_paths(self) -> None:
        candidate = frozen.build_candidate(
            {
                "candidate_id": "bithumb_current_actionable_bio_1d_long",
                "market": "KRW-BIO",
                "timeframe": "1d",
                "hypothesis_family": "bithumb_multi_asset_momentum",
                "current_signal_side": "long",
                "current_target_weight": 0.02,
                "momentum_threshold": 0.02,
                "volume_ratio": 1.3,
            }
        )

        self.assertEqual(candidate["candidate_id"], "bithumb_current_actionable_bio_1d_long_freeze001")
        self.assertEqual(candidate["current_gate"], "G03_BACKTEST_SCREEN")
        self.assertEqual(candidate["status"], "READY_FOR_BACKTEST_SCREEN")
        self.assertEqual(candidate["frozen_parameters"]["momentum_threshold"], 0.02)
        self.assertFalse(candidate["promotion_allowed_by_this_report"])
        self.assertFalse(candidate["live_allowed_by_this_report"])
        self.assertFalse(candidate["broker_submit_allowed_by_this_report"])
        self.assertFalse(candidate["real_orders_allowed_by_this_report"])

    def test_report_freezes_safe_current_actionable_candidates(self) -> None:
        original = frozen.read_json
        try:
            frozen.read_json = lambda _path, _default: {
                "top_current_actionable": [
                    {
                        "candidate_id": "bithumb_current_actionable_bio_1d_long",
                        "market": "KRW-BIO",
                        "timeframe": "1d",
                        "hypothesis_family": "bithumb_multi_asset_momentum",
                        "current_actionable": True,
                        "current_signal_side": "long",
                        "current_target_weight": 0.02,
                        "momentum_threshold": 0.02,
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
            report = frozen.build_report()
        finally:
            frozen.read_json = original

        self.assertEqual(report["status"], "READY_FOR_BACKTEST_SCREEN")
        self.assertEqual(report["frozen_candidate_count"], 1)
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
