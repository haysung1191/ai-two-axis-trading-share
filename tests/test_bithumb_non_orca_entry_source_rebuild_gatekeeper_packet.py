from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_non_orca_entry_source_rebuild_gatekeeper_packet.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_non_orca_entry_source_rebuild_gatekeeper_packet", MODULE_PATH)
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


class BithumbEntrySourceRebuildGatekeeperPacketTests(unittest.TestCase):
    def test_builds_review_ready_packet_without_order_permissions(self) -> None:
        sweep = {
            "status": "NON_ORCA_ENTRY_SOURCE_REBUILD_SWEEP_PASS",
            "rebuild_target_count": 2,
            "trial_count": 162,
            "evaluated_trial_count": 162,
            "oos_pass_trial_count": 33,
            "robustness_pass_trial_count": 15,
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": SAFE_SWEEP_ASSERTIONS,
            "trial_results": [
                {
                    "candidate_id": "pola_entrysource_029",
                    "parent_candidate_id": "pola",
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "status": "OOS_CANDIDATE_PASS",
                    "parameters": {
                        "entry_signal_family": "trend_pullback_continuation",
                        "price_source": "close",
                        "data_window_policy": "post_listing_warmup_90d",
                    },
                    "source_conversion": {
                        "recommended_exposure_cap": 1.0,
                        "estimated_cagr": 1.79,
                        "estimated_mdd": -0.199,
                        "source_trade_count": 12,
                        "source_profit_factor": 2.35,
                    },
                    "aggregate": {
                        "fold_count": 3,
                        "pass_fold_count": 3,
                        "positive_fold_count": 3,
                        "worst_fold_mdd": -0.199,
                        "average_fold_cagr": 6.69,
                        "total_trade_count": 11,
                    },
                    "robustness": {
                        "status": "ROBUSTNESS_STRESS_PASS",
                        "case_count": 7,
                        "pass_count": 5,
                        "cost_pass_count": 2,
                    },
                }
            ],
        }

        packet = packet_builder.build_packet(sweep, {"status": "PASS", "halt_count": 0})

        self.assertEqual(packet["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertEqual(packet["candidate_id"], "pola_entrysource_029")
        self.assertEqual(packet["parent_candidate_id"], "pola")
        self.assertEqual(packet["recommended_decision"], "REVIEW_NON_ORCA_ENTRY_SOURCE_REBUILD_EVIDENCE_ONLY")
        self.assertEqual(packet["exact_phrase_to_record"], "REVIEW_NON_ORCA_ENTRY_SOURCE_REBUILD_EVIDENCE_ONLY")
        self.assertIn("does not approve promotion", packet["review_only_effect"])
        self.assertEqual(packet["evidence_summary"]["oos_pass_fold_count"], 3)
        self.assertEqual(packet["evidence_summary"]["robustness_pass_count"], 5)
        self.assertEqual(packet["evidence_summary"]["trial_count"], 162)
        self.assertEqual(packet["parameters"]["entry_signal_family"], "trend_pullback_continuation")
        self.assertFalse(packet["no_order_assertions"]["shadow_registration_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["broker_submit_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["real_orders_allowed_by_this_packet"])

    def test_allows_warn_when_hard_safety_passes(self) -> None:
        sweep = {
            "status": "NON_ORCA_ENTRY_SOURCE_REBUILD_SWEEP_PASS",
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": SAFE_SWEEP_ASSERTIONS,
            "trial_results": [
                {
                    "candidate_id": "pola_entrysource_029",
                    "status": "OOS_CANDIDATE_PASS",
                    "robustness": {"status": "ROBUSTNESS_STRESS_PASS"},
                }
            ],
        }

        packet = packet_builder.build_packet(
            sweep,
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
        sweep = {
            "status": "NON_ORCA_ENTRY_SOURCE_REBUILD_SWEEP_PASS",
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": {
                **SAFE_SWEEP_ASSERTIONS,
                "broker_submit_allowed_by_this_report": True,
            },
            "trial_results": [
                {
                    "candidate_id": "pola_entrysource_029",
                    "status": "OOS_CANDIDATE_PASS",
                    "robustness": {"status": "ROBUSTNESS_STRESS_PASS"},
                }
            ],
        }

        packet = packet_builder.build_packet(sweep, {"status": "PASS", "halt_count": 0})

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("entry_source_rebuild_sweep_no_order_safe", packet["blockers"])
        self.assertFalse(packet["no_order_assertions"]["live_allowed_by_this_packet"])


if __name__ == "__main__":
    unittest.main()
