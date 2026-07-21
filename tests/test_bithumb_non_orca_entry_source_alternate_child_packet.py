from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_non_orca_entry_source_alternate_child_packet.py")
SPEC = importlib.util.spec_from_file_location(
    "build_bithumb_non_orca_entry_source_alternate_child_packet",
    MODULE_PATH,
)
assert SPEC is not None
assert SPEC.loader is not None
packet_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_builder)


class BithumbNonOrcaEntrySourceAlternateChildPacketTests(unittest.TestCase):
    def safe_report_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def source_sweep(self) -> dict[str, object]:
        return {
            "status": "NON_ORCA_ENTRY_SOURCE_REBUILD_SWEEP_PASS",
            "best_candidate_id": "pola_entrysource_029",
            "best_repair_target_id": "pola",
            "rebuild_target_count": 2,
            "trial_count": 162,
            "evaluated_trial_count": 162,
            "oos_pass_trial_count": 33,
            "robustness_pass_trial_count": 3,
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": self.safe_report_assertions(),
            "trial_results": [
                {
                    "candidate_id": "pola_entrysource_029",
                    "parent_candidate_id": "pola",
                    "repair_target_id": "pola",
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "status": "OOS_CANDIDATE_PASS",
                    "source_conversion": {"estimated_cagr": 1.1, "estimated_mdd": -0.2, "source_trade_count": 12},
                    "aggregate": {"pass_fold_count": 3, "average_fold_cagr": 5.0, "worst_fold_mdd": -0.2},
                    "robustness": {"status": "ROBUSTNESS_STRESS_PASS", "pass_count": 7, "cost_pass_count": 2},
                    "parameters": {"entry_signal_family": "trend_pullback_continuation"},
                },
                {
                    "candidate_id": "pola_entrysource_032",
                    "parent_candidate_id": "pola",
                    "repair_target_id": "pola",
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "status": "OOS_CANDIDATE_PASS",
                    "source_conversion": {"estimated_cagr": 0.9, "estimated_mdd": -0.19, "source_trade_count": 11},
                    "aggregate": {"pass_fold_count": 3, "average_fold_cagr": 4.0, "worst_fold_mdd": -0.19},
                    "robustness": {"status": "ROBUSTNESS_STRESS_PASS", "pass_count": 7, "cost_pass_count": 2},
                    "parameters": {"entry_signal_family": "trend_pullback_continuation"},
                },
                {
                    "candidate_id": "bio_entrysource_012",
                    "parent_candidate_id": "bio",
                    "repair_target_id": "bio",
                    "market": "KRW-BIO",
                    "timeframe": "1d",
                    "status": "OOS_CANDIDATE_PASS",
                    "source_conversion": {"estimated_cagr": 0.6, "estimated_mdd": -0.2, "source_trade_count": 9},
                    "aggregate": {"pass_fold_count": 2, "average_fold_cagr": 3.0, "worst_fold_mdd": -0.2},
                    "robustness": {"status": "ROBUSTNESS_STRESS_PASS", "pass_count": 6, "cost_pass_count": 2},
                    "parameters": {"entry_signal_family": "volume_momentum_reversal"},
                },
            ],
        }

    def test_builds_ready_alternate_child_packet_without_order_paths(self) -> None:
        packet = packet_builder.build_packet(self.source_sweep())

        self.assertEqual(packet["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertTrue(packet["ready_for_human_review"])
        self.assertEqual(packet["alternate_pass_child_count"], 2)
        self.assertEqual(packet["top_alternate_candidate_id"], "pola_entrysource_032")
        self.assertEqual(
            packet["exact_phrase_to_record"],
            "REVIEW_NON_ORCA_ENTRY_SOURCE_ALTERNATE_CHILDREN_ONLY",
        )
        self.assertFalse(packet["counts_as_paper_or_live_evidence"])
        self.assertFalse(packet["no_order_assertions"]["live_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["broker_submit_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["real_orders_allowed_by_this_packet"])

    def test_blocks_unsafe_source_sweep(self) -> None:
        source = self.source_sweep()
        source["no_order_assertions"] = {"broker_submit_allowed_by_this_report": True}

        packet = packet_builder.build_packet(source)

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("SOURCE_SWEEP_NOT_NO_ORDER_SAFE", packet["blockers"])


if __name__ == "__main__":
    unittest.main()
