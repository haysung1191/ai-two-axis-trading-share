from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_low_turnover_signal_rebuild_spec.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_low_turnover_signal_rebuild_spec", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
spec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spec)


class BtcEthIntradayLowTurnoverSignalRebuildSpecTests(unittest.TestCase):
    def stop(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": "BTC_ETH_COST_FRICTION_REPAIR_STOP_CONDITION_READY",
            "base_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "market": "KRW-BTC",
            "timeframe": "4h",
            "trial_count": 648,
            "evaluated_oos_pass_trial_count": 159,
            "repair_pass_count": 0,
            "best_cost_pass_count": 0,
            "recommended_next_research_action": "REBUILD_INTRADAY_SIGNAL_FOR_LOWER_TURNOVER_OR_SKIP_SHADOW_UNTIL_COST_PASS",
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": dict(spec.SAFE_ASSERTIONS),
        }
        payload.update(overrides)
        return payload

    def test_builds_research_only_signal_rebuild_spec(self) -> None:
        report = spec.build_spec(self.stop())

        self.assertEqual(report["status"], "READY_FOR_RESEARCH_SPEC_REVIEW")
        self.assertEqual(report["rebuild_target_count"], 3)
        self.assertEqual(
            report["frozen_scope"]["scope"],
            "btc_eth_intraday_low_turnover_signal_rebuild_research_only_no_order_paths",
        )
        self.assertIn("order_execution_path", report["frozen_scope"]["forbidden_changes"])
        self.assertIn("private_submit_path", report["frozen_scope"]["forbidden_changes"])
        self.assertEqual(report["acceptance_checks"]["min_cost_pass_count"], 2)
        self.assertEqual(report["acceptance_checks"]["target_round_trip_cost_rates"], [0.003, 0.004])
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["mutation_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])
        target_ids = {row["target_id"] for row in report["rebuild_targets"]}
        self.assertEqual(
            target_ids,
            {"low_turnover_trend_confirmation", "volatility_filtered_momentum", "payoff_asymmetric_reentry"},
        )

    def test_blocks_when_stop_condition_is_not_ready(self) -> None:
        report = spec.build_spec(self.stop(status="BLOCKED"))

        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["rebuild_target_count"], 0)
        self.assertIn("COST_FRICTION_STOP_CONDITION_NOT_READY", report["blockers"])

    def test_blocks_unsafe_stop_condition(self) -> None:
        report = spec.build_spec(self.stop(no_order_assertions={"broker_submit_allowed_by_this_report": True}))

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("STOP_CONDITION_ORDER_PATH_NOT_SAFE", report["blockers"])


if __name__ == "__main__":
    unittest.main()
