from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_cost_friction_repair_stop_condition_review.py")
SPEC = importlib.util.spec_from_file_location(
    "build_btc_eth_intraday_cost_friction_repair_stop_condition_review", MODULE_PATH
)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class BtcEthIntradayCostFrictionRepairStopConditionReviewTests(unittest.TestCase):
    def safe_assertions(self) -> dict[str, bool]:
        return dict(review.SAFE_ASSERTIONS)

    def spec(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": "READY_FOR_RESEARCH_SPEC_REVIEW",
            "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": self.safe_assertions(),
        }
        payload.update(overrides)
        return payload

    def sweep(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": "COST_FRICTION_REPAIR_SWEEP_ITERATE",
            "base_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "seed_count": 3,
            "trial_count": 648,
            "evaluated_oos_pass_trial_count": 159,
            "repair_pass_count": 0,
            "best_candidate_id": "best_child",
            "best_seed_id": "costrepair_profitlock_002",
            "best_pass_count": 4,
            "best_cost_pass_count": 0,
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": self.safe_assertions(),
        }
        payload.update(overrides)
        return payload

    def test_ready_stop_condition_when_sweep_finds_oos_children_but_no_cost_pass(self) -> None:
        report = review.build_report(self.spec(), self.sweep())

        self.assertEqual(report["status"], "BTC_ETH_COST_FRICTION_REPAIR_STOP_CONDITION_READY")
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertEqual(report["trial_count"], 648)
        self.assertEqual(report["evaluated_oos_pass_trial_count"], 159)
        self.assertEqual(report["repair_pass_count"], 0)
        self.assertEqual(
            report["recommended_branch_action"],
            "STOP_COST_FRICTION_REPAIR_GRID_REQUIRE_NEW_SIGNAL_OR_EXECUTION_ASSUMPTION",
        )
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocked_when_sweep_has_repair_pass(self) -> None:
        report = review.build_report(self.spec(), self.sweep(repair_pass_count=1, best_cost_pass_count=2))

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("SWEEP_STILL_HAS_COST_FRICTION_REPAIR_CHILD", report["blockers"])
        self.assertFalse(report["ready_for_gatekeeper_review"])

    def test_blocked_when_source_order_path_is_unsafe(self) -> None:
        report = review.build_report(self.spec(no_order_assertions={"broker_submit_allowed_by_this_report": True}), self.sweep())

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("SOURCE_SPEC_ORDER_PATH_NOT_SAFE", report["blockers"])


if __name__ == "__main__":
    unittest.main()
