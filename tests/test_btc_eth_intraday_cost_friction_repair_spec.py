from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_cost_friction_repair_spec.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_cost_friction_repair_spec", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
spec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spec)


class BtcEthIntradayCostFrictionRepairSpecTests(unittest.TestCase):
    def review(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": "BTC_ETH_INTRADAY_COST_FRICTION_REVIEW_READY",
            "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "market": "KRW-BTC",
            "timeframe": "4h",
            "pass_count": 4,
            "cost_pass_count": 0,
            "cost_case_count": 2,
            "recommended_action": "KEEP_RESEARCH_ONLY_REQUIRE_COST_FRICTION_REPAIR_BEFORE_SHADOW_OR_PAPER_USE",
            "counts_as_paper_or_live_evidence": False,
            "cost_cases": [
                {"case_id": "cost_30bps", "status": "STRESS_ITERATE"},
                {"case_id": "cost_40bps", "status": "STRESS_ITERATE"},
            ],
            "no_order_assertions": dict(spec.SAFE_ASSERTIONS),
        }
        payload.update(overrides)
        return payload

    def test_ready_spec_creates_three_research_only_repair_seeds(self) -> None:
        report = spec.build_spec(self.review())

        self.assertEqual(report["status"], "READY_FOR_RESEARCH_SPEC_REVIEW")
        self.assertEqual(report["repair_seed_count"], 3)
        self.assertEqual(report["target_round_trip_cost_rates"], [0.003, 0.004])
        self.assertEqual(
            report["frozen_scope"]["scope"],
            "btc_eth_intraday_cost_friction_repair_research_only_no_order_paths",
        )
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["mutation_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])
        self.assertTrue(
            all(seed["candidate_id"].startswith("btc_eth_intraday_momentum_btc_4h_sweep001_costrepair_")
                for seed in report["repair_seeds"])
        )

    def test_blocked_when_source_does_not_require_repair(self) -> None:
        report = spec.build_spec(self.review(cost_pass_count=1))

        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["repair_seed_count"], 0)
        self.assertIn("SOURCE_ALREADY_HAS_COST_PASS", report["blockers"])

    def test_blocked_when_source_order_path_is_unsafe(self) -> None:
        report = spec.build_spec(self.review(no_order_assertions={"broker_submit_allowed_by_this_report": True}))

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("SOURCE_ORDER_PATH_NOT_SAFE", report["blockers"])


if __name__ == "__main__":
    unittest.main()
