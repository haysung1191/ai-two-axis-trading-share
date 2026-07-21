from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_oos_stability_plateau_review.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_oos_stability_plateau_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class BtcEthIntradayOosStabilityPlateauReviewTests(unittest.TestCase):
    def safe_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def source(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": "OOS_STABILITY_ITERATE",
            "current_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "best_candidate_id": "btc_eth_intraday_momentum_btc_4h__stability_001",
            "evaluated_trial_count": 20,
            "stability_pass_count": 3,
            "current_worst_fold_mdd": -0.16791650341473752,
            "best_worst_fold_mdd": -0.16791650341473752,
            "current_average_fold_cagr": 0.26930593366095223,
            "best_average_fold_cagr": 0.26930593366095223,
            "best_improves_current": False,
            "no_order_assertions": self.safe_assertions(),
        }
        payload.update(overrides)
        return payload

    def test_ready_when_stability_passes_do_not_improve_current_candidate(self) -> None:
        report = review.build_report(self.source())

        self.assertEqual(report["status"], "BTC_ETH_INTRADAY_OOS_STABILITY_PLATEAU_REVIEW_READY")
        self.assertEqual(report["recommended_action"], review.RECOMMENDED_ACTION)
        self.assertEqual(report["stability_pass_count"], 3)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["mutation_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocked_when_best_variant_improves_current(self) -> None:
        report = review.build_report(self.source(best_improves_current=True))

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("BEST_VARIANT_DOES_NOT_CONFIRM_PLATEAU", report["blockers"])

    def test_blocked_when_no_stability_pass_variant_exists(self) -> None:
        report = review.build_report(self.source(stability_pass_count=0))

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("NO_STABILITY_PASS_VARIANTS", report["blockers"])


if __name__ == "__main__":
    unittest.main()
