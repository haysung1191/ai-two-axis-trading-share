from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_orca_repair_followup_seed_packet.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_orca_repair_followup_seed_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


SAFE_ASSERTIONS = {
    "promotion_allowed_by_this_report": False,
    "paper_enabled_by_this_report": False,
    "live_allowed_by_this_report": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders_allowed_by_this_report": False,
}


class BithumbCurrentActionableOrcaRepairFollowupSeedPacketTests(unittest.TestCase):
    def source_packet(self) -> dict:
        return {
            "status": "ORCA_REPAIR_SEED_SWEEP_ITERATE",
            "base_candidate_id": "orca_sweep1507",
            "parent_candidate_id": "orca_parent",
            "market": "KRW-ORCA",
            "timeframe": "1d",
            "seed_count": 1,
            "oos_pass_seed_count": 1,
            "robustness_pass_seed_count": 0,
            "no_order_assertions": dict(SAFE_ASSERTIONS),
            "seed_results": [
                {
                    "seed_id": "seed_a",
                    "candidate_id": "orca_seed_a",
                    "status": "OOS_CANDIDATE_PASS",
                    "parameters": {
                        "lookback_bars": 3,
                        "hold_bars": 3,
                        "volume_window": 10,
                        "volume_ratio_floor": 1.25,
                        "momentum_threshold": 0.04,
                        "stop_loss": 0.05,
                        "take_profit": 0.18,
                        "round_trip_cost_rate": 0.002,
                    },
                    "screen_metrics": {"total_return": -0.1, "mdd": -0.44},
                    "source_conversion": {"estimated_cagr": -0.07, "estimated_mdd": -0.2},
                    "robustness": {
                        "status": "ROBUSTNESS_STRESS_ITERATE",
                        "case_count": 1,
                        "pass_count": 0,
                        "cost_pass_count": 0,
                        "cases": [
                            {
                                "case_id": "base_recheck",
                                "status": "STRESS_ITERATE",
                                "full_window_metrics": {"total_return": -0.1, "mdd": -0.44, "trade_count": 13},
                                "fold_aggregate": {"pass_fold_count": 2, "positive_fold_count": 2},
                            }
                        ],
                    },
                }
            ],
        }

    def test_followup_seed_packet_is_ready_and_safe(self) -> None:
        report = builder.build_report(self.source_packet())

        self.assertEqual(report["status"], "ORCA_REPAIR_FOLLOWUP_SEED_PACKET_READY")
        self.assertEqual(len(report["proposed_seed_specs"]), 3)
        self.assertEqual(report["ranked_seed_failures"][0]["candidate_id"], "orca_seed_a")
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertEqual(report["no_order_assertions"], SAFE_ASSERTIONS)

    def test_followup_seed_packet_blocks_unsafe_source(self) -> None:
        source = self.source_packet()
        source["no_order_assertions"]["live_allowed_by_this_report"] = True

        report = builder.build_report(source)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("SOURCE_PACKET_ORDER_PATH_NOT_SAFE", report["blockers"])


if __name__ == "__main__":
    unittest.main()
