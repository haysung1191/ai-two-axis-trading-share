from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_orca_repair_seed_packet.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_orca_repair_seed_packet", MODULE_PATH)
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


class BithumbCurrentActionableOrcaRepairSeedPacketTests(unittest.TestCase):
    def source_packet(self) -> dict:
        return {
            "status": "ORCA_ROBUSTNESS_REPAIR_ITERATE",
            "base_candidate_id": "orca_sweep1507",
            "parent_candidate_id": "orca_parent",
            "market": "KRW-ORCA",
            "timeframe": "1d",
            "trial_count": 3888,
            "oos_pass_candidate_count": 2,
            "robustness_pass_candidate_count": 0,
            "no_order_assertions": dict(SAFE_ASSERTIONS),
            "candidate_results": [
                {
                    "candidate_id": "orca_child_a",
                    "status": "OOS_CANDIDATE_PASS",
                    "parameters": {
                        "lookback_bars": 3,
                        "hold_bars": 3,
                        "volume_window": 10,
                        "volume_ratio_floor": 1.0,
                        "momentum_threshold": 0.03,
                        "stop_loss": 0.12,
                        "take_profit": 0.2,
                        "round_trip_cost_rate": 0.002,
                    },
                    "source_conversion": {"estimated_cagr": 1.0, "estimated_mdd": -0.2},
                    "aggregate": {"fold_count": 3, "pass_fold_count": 2, "total_trade_count": 11},
                    "robustness": {
                        "status": "ROBUSTNESS_STRESS_ITERATE",
                        "case_count": 2,
                        "pass_count": 0,
                        "cost_pass_count": 0,
                        "cases": [
                            {
                                "case_id": "base_recheck",
                                "status": "STRESS_ITERATE",
                                "full_window_metrics": {"total_return": 0.5, "mdd": -0.28, "trade_count": 12},
                                "fold_aggregate": {"pass_fold_count": 2, "positive_fold_count": 2},
                            },
                            {
                                "case_id": "cost_30bps",
                                "status": "STRESS_ITERATE",
                                "full_window_metrics": {"total_return": 0.4, "mdd": -0.27, "trade_count": 12},
                                "fold_aggregate": {"pass_fold_count": 2, "positive_fold_count": 2},
                            },
                        ],
                    },
                }
            ],
        }

    def test_seed_packet_extracts_near_misses_without_order_permissions(self) -> None:
        report = builder.build_report(self.source_packet())

        self.assertEqual(report["status"], "ORCA_REPAIR_SEED_PACKET_READY")
        self.assertEqual(report["near_miss_candidate_count"], 1)
        self.assertEqual(len(report["proposed_seed_specs"]), 3)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertEqual(report["no_order_assertions"], SAFE_ASSERTIONS)
        top = report["top_near_miss_candidates"][0]
        self.assertEqual(top["candidate_id"], "orca_child_a")
        self.assertEqual(top["component_pass_total"], 8)
        self.assertEqual(top["max_component_pass_total"], 10)
        self.assertEqual(top["dominant_failure_dimensions"][0]["dimension"], "mdd_within_limit")

    def test_seed_packet_blocks_unsafe_source(self) -> None:
        source = self.source_packet()
        source["no_order_assertions"]["live_allowed_by_this_report"] = True

        report = builder.build_report(source)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("SOURCE_PACKET_ORDER_PATH_NOT_SAFE", report["blockers"])

    def test_seed_packet_blocks_when_repair_already_passed(self) -> None:
        source = self.source_packet()
        source["robustness_pass_candidate_count"] = 1

        report = builder.build_report(source)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("ORCA_ROBUSTNESS_REPAIR_ALREADY_HAS_PASSING_CHILD", report["blockers"])


if __name__ == "__main__":
    unittest.main()
