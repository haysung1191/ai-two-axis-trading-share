from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_low_turnover_rebuild_gatekeeper_packet.py")
SPEC = importlib.util.spec_from_file_location(
    "build_btc_eth_intraday_low_turnover_rebuild_gatekeeper_packet",
    MODULE_PATH,
)
assert SPEC is not None
assert SPEC.loader is not None
packet_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_builder)


SAFE_SWEEP_ASSERTIONS = {
    "promotion_allowed_by_this_report": False,
    "paper_enabled_by_this_report": False,
    "live_allowed_by_this_report": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders_allowed_by_this_report": False,
}


class BtcEthIntradayLowTurnoverRebuildGatekeeperPacketTests(unittest.TestCase):
    def sweep(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": "LOW_TURNOVER_SIGNAL_REBUILD_SWEEP_PASS",
            "base_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "market": "KRW-BTC",
            "timeframe": "4h",
            "target_count": 3,
            "trial_count": 162,
            "evaluated_oos_pass_trial_count": 38,
            "rebuild_pass_count": 1,
            "best_candidate_id": "child080",
            "target_oos_pass_counts": {"volatility_filtered_momentum": 18},
            "target_rebuild_pass_counts": {"volatility_filtered_momentum": 1},
            "counts_as_paper_or_live_evidence": False,
            "mutation_allowed_by_this_report": False,
            "no_order_assertions": SAFE_SWEEP_ASSERTIONS,
            "candidate_results": [
                {
                    "candidate_id": "child080",
                    "target_id": "volatility_filtered_momentum",
                    "entry_signal_family": "volatility_expansion_momentum",
                    "status": "LOW_TURNOVER_SIGNAL_REBUILD_SWEEP_PASS",
                    "parameters": {"lookback_bars": 3, "hold_bars": 10},
                    "conceptual_parameters": {"atr_window": 20},
                    "screen_metrics": {
                        "total_return": 0.12,
                        "cagr": 0.26,
                        "mdd": -0.16,
                        "win_rate": 0.5,
                        "profit_factor": 1.35,
                        "trade_count": 46,
                    },
                    "oos_aggregate": {
                        "fold_count": 3,
                        "pass_fold_count": 2,
                        "positive_fold_count": 2,
                        "worst_fold_mdd": -0.16,
                        "average_fold_cagr": 0.7,
                        "total_trade_count": 45,
                    },
                    "case_count": 7,
                    "pass_count": 6,
                    "cost_pass_count": 2,
                }
            ],
        }
        payload.update(overrides)
        return payload

    def test_builds_review_ready_packet_without_order_permissions(self) -> None:
        packet = packet_builder.build_packet(self.sweep(), {"status": "PASS", "halt_count": 0})

        self.assertEqual(packet["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertEqual(packet["candidate_id"], "child080")
        self.assertEqual(packet["parent_candidate_id"], "btc_eth_intraday_momentum_btc_4h_sweep001")
        self.assertEqual(packet["exact_phrase_to_record"], "REVIEW_BTC_ETH_INTRADAY_LOW_TURNOVER_REBUILD_ONLY")
        self.assertIn("does not approve promotion", packet["review_only_effect"])
        self.assertEqual(packet["evidence_summary"]["best_cost_pass_count"], 2)
        self.assertEqual(packet["evidence_summary"]["oos_pass_fold_count"], 2)
        self.assertEqual(packet["parameters"]["hold_bars"], 10)
        self.assertFalse(packet["no_order_assertions"]["shadow_registration_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["broker_submit_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["real_orders_allowed_by_this_packet"])

    def test_allows_warn_when_hard_safety_passes(self) -> None:
        packet = packet_builder.build_packet(
            self.sweep(),
            {
                "status": "WARN",
                "halt_count": 0,
                "checks": [
                    {"name": "live_disabled", "status": "PASS"},
                    {"name": "private_submit_unused", "status": "PASS"},
                    {"name": "real_orders_zero", "status": "PASS"},
                    {"name": "broker_submit_scope", "status": "PASS"},
                    {"name": "latest_run", "status": "WARN"},
                ],
            },
        )

        self.assertEqual(packet["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertTrue(packet["readiness_checks"]["risk_guard_hard_safety_pass"])
        self.assertEqual(packet["blockers"], [])

    def test_blocks_unsafe_sweep_flags(self) -> None:
        sweep = self.sweep(
            no_order_assertions={**SAFE_SWEEP_ASSERTIONS, "broker_submit_allowed_by_this_report": True}
        )

        packet = packet_builder.build_packet(sweep, {"status": "PASS", "halt_count": 0})

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("low_turnover_rebuild_sweep_no_order_safe", packet["blockers"])
        self.assertFalse(packet["no_order_assertions"]["live_allowed_by_this_packet"])

    def test_blocks_when_best_child_does_not_cost_pass(self) -> None:
        sweep = self.sweep()
        candidate = sweep["candidate_results"][0]  # type: ignore[index]
        candidate["cost_pass_count"] = 1  # type: ignore[index]

        packet = packet_builder.build_packet(sweep, {"status": "PASS", "halt_count": 0})

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("candidate_cost_pass_count", packet["blockers"])


if __name__ == "__main__":
    unittest.main()
