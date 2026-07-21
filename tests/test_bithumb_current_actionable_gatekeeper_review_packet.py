from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_gatekeeper_review_packet.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_gatekeeper_review_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
packet_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_mod)


SAFE_REPORT_ASSERTIONS = {
    "promotion_allowed_by_this_report": False,
    "paper_enabled_by_this_report": False,
    "live_allowed_by_this_report": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders_allowed_by_this_report": False,
}


class BithumbCurrentActionableGatekeeperReviewPacketTests(unittest.TestCase):
    def test_packet_is_review_ready_without_enabling_shadow_or_orders(self) -> None:
        candidate_id = "bithumb_current_actionable_pola_1d_long_freeze001"
        packet = packet_mod.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "top_conversion": {
                    "candidate_id": candidate_id,
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "status": "RISK_CONVERSION_PASS",
                    "conversion": {
                        "recommended_exposure_cap": 0.53,
                        "estimated_cagr": 0.21,
                        "estimated_mdd": -0.20,
                    },
                    "gate_result": "pass_fixed_exposure_cap",
                    "next_gate": "G05_GATEKEEPER_REVIEW_RESEARCH_ONLY",
                },
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {},
            {
                "status": "OOS_WALKFORWARD_PASS",
                "candidate_id": candidate_id,
                "aggregate": {"pass_fold_count": 2, "positive_fold_count": 2, "total_trade_count": 8},
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "ROBUSTNESS_STRESS_PASS",
                "candidate_id": candidate_id,
                "pass_count": 4,
                "cost_pass_count": 2,
                "case_count": 7,
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {"status": "BACKTEST_SCREEN_COMPLETE", "no_order_assertions": SAFE_REPORT_ASSERTIONS},
            {
                "status": "READY_FOR_BACKTEST_SCREEN",
                "candidates": [{"candidate_id": candidate_id}],
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "gatekeeper_action_packet": {
                    "bithumb_current_actionable_risk_conversion": {"ready_for_gatekeeper_review": True}
                }
            },
            {"status": "PASS"},
        )

        self.assertEqual(packet["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertEqual(packet["selected_evidence_type"], "risk_conversion")
        self.assertEqual(packet["blockers"], [])
        self.assertFalse(packet["no_order_assertions"]["shadow_enabled_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["paper_enabled_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["live_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["broker_submit_allowed_by_this_packet"])
        self.assertFalse(packet["no_order_assertions"]["real_orders_allowed_by_this_packet"])

    def test_packet_blocks_when_source_order_assertions_are_not_safe(self) -> None:
        unsafe = dict(SAFE_REPORT_ASSERTIONS)
        unsafe["live_allowed_by_this_report"] = True
        packet = packet_mod.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "top_conversion": {"candidate_id": "c", "status": "RISK_CONVERSION_PASS"},
                "no_order_assertions": unsafe,
            },
            {},
            {
                "status": "OOS_WALKFORWARD_PASS",
                "candidate_id": "c",
                "aggregate": {"pass_fold_count": 2, "positive_fold_count": 2, "total_trade_count": 8},
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "ROBUSTNESS_STRESS_PASS",
                "candidate_id": "c",
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {"status": "BACKTEST_SCREEN_COMPLETE", "no_order_assertions": SAFE_REPORT_ASSERTIONS},
            {
                "status": "READY_FOR_BACKTEST_SCREEN",
                "candidates": [{"candidate_id": "c"}],
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "gatekeeper_action_packet": {
                    "bithumb_current_actionable_risk_conversion": {"ready_for_gatekeeper_review": True}
                }
            },
            {"status": "PASS"},
        )

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("risk_no_order_safe", packet["blockers"])

    def test_packet_prefers_safe_parameter_sweep_child_candidate(self) -> None:
        packet = packet_mod.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "top_conversion": {
                    "candidate_id": "parent",
                    "status": "RISK_CONVERSION_PASS",
                    "conversion": {"estimated_cagr": 0.2, "estimated_mdd": -0.2},
                },
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "top_sweep": {
                    "candidate_id": "parent_sweep0001",
                    "parent_candidate_id": "parent",
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "status": "PARAMETER_SWEEP_PASS",
                    "conversion": {
                        "recommended_exposure_cap": 1.0,
                        "estimated_cagr": 1.1,
                        "estimated_mdd": -0.19,
                        "source_trade_count": 8,
                        "source_profit_factor": 3.0,
                    },
                    "next_gate": "G05_GATEKEEPER_REVIEW_RESEARCH_ONLY",
                },
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "OOS_WALKFORWARD_PASS",
                "candidate_id": "parent_sweep0001",
                "aggregate": {"pass_fold_count": 2, "positive_fold_count": 2, "total_trade_count": 8},
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "ROBUSTNESS_STRESS_PASS",
                "candidate_id": "parent_sweep0001",
                "pass_count": 4,
                "cost_pass_count": 2,
                "case_count": 7,
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {"status": "BACKTEST_SCREEN_COMPLETE", "no_order_assertions": SAFE_REPORT_ASSERTIONS},
            {
                "status": "READY_FOR_BACKTEST_SCREEN",
                "candidates": [{"candidate_id": "parent"}],
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "gatekeeper_action_packet": {
                    "bithumb_current_actionable_risk_conversion": {"ready_for_gatekeeper_review": True}
                }
            },
            {"status": "PASS"},
        )

        self.assertEqual(packet["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertEqual(packet["selected_evidence_type"], "parameter_sweep")
        self.assertEqual(packet["candidate_id"], "parent_sweep0001")
        self.assertEqual(packet["parent_candidate_id"], "parent")
        self.assertEqual(packet["blockers"], [])

    def test_packet_blocks_when_parameter_sweep_fails_oos_walkforward(self) -> None:
        packet = packet_mod.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "top_conversion": {
                    "candidate_id": "parent",
                    "status": "RISK_CONVERSION_PASS",
                    "conversion": {"estimated_cagr": 0.2, "estimated_mdd": -0.2},
                },
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "top_sweep": {
                    "candidate_id": "parent_sweep0001",
                    "parent_candidate_id": "parent",
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "status": "PARAMETER_SWEEP_PASS",
                    "conversion": {"estimated_cagr": 1.1, "estimated_mdd": -0.19},
                },
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "OOS_WALKFORWARD_ITERATE",
                "candidate_id": "parent_sweep0001",
                "aggregate": {"pass_fold_count": 1, "positive_fold_count": 1, "total_trade_count": 8},
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "ROBUSTNESS_STRESS_PASS",
                "candidate_id": "parent_sweep0001",
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {"status": "BACKTEST_SCREEN_COMPLETE", "no_order_assertions": SAFE_REPORT_ASSERTIONS},
            {
                "status": "READY_FOR_BACKTEST_SCREEN",
                "candidates": [{"candidate_id": "parent"}],
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "gatekeeper_action_packet": {
                    "bithumb_current_actionable_risk_conversion": {"ready_for_gatekeeper_review": True}
                }
            },
            {"status": "PASS"},
        )

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("oos_walkforward_pass", packet["blockers"])
        self.assertEqual(packet["evidence_summary"]["oos_status"], "OOS_WALKFORWARD_ITERATE")

    def test_packet_blocks_when_robustness_stress_fails(self) -> None:
        packet = packet_mod.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "top_conversion": {"candidate_id": "parent", "status": "RISK_CONVERSION_PASS"},
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "top_sweep": {
                    "candidate_id": "parent_sweep0001",
                    "parent_candidate_id": "parent",
                    "status": "PARAMETER_SWEEP_PASS",
                    "conversion": {"estimated_cagr": 1.1, "estimated_mdd": -0.19},
                },
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "OOS_WALKFORWARD_PASS",
                "candidate_id": "parent_sweep0001",
                "top_oos": {
                    "candidate_id": "parent_sweep0001",
                    "parent_candidate_id": "parent",
                    "status": "OOS_CANDIDATE_PASS",
                },
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "ROBUSTNESS_STRESS_ITERATE",
                "candidate_id": "parent_sweep0001",
                "pass_count": 2,
                "cost_pass_count": 0,
                "case_count": 7,
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {"status": "BACKTEST_SCREEN_COMPLETE", "no_order_assertions": SAFE_REPORT_ASSERTIONS},
            {
                "status": "READY_FOR_BACKTEST_SCREEN",
                "candidates": [{"candidate_id": "parent"}],
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "gatekeeper_action_packet": {
                    "bithumb_current_actionable_risk_conversion": {"ready_for_gatekeeper_review": True}
                }
            },
            {"status": "PASS"},
        )

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("robustness_stress_pass", packet["blockers"])

    def test_packet_does_not_add_risk_blocker_for_freshness_warn_when_hard_safety_passes(self) -> None:
        packet = packet_mod.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "top_conversion": {"candidate_id": "parent", "status": "RISK_CONVERSION_PASS"},
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "top_sweep": {
                    "candidate_id": "parent_sweep0001",
                    "parent_candidate_id": "parent",
                    "status": "PARAMETER_SWEEP_PASS",
                    "conversion": {"estimated_cagr": 1.1, "estimated_mdd": -0.19},
                },
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "OOS_WALKFORWARD_PASS",
                "candidate_id": "parent_sweep0001",
                "top_oos": {
                    "candidate_id": "parent_sweep0001",
                    "parent_candidate_id": "parent",
                    "status": "OOS_CANDIDATE_PASS",
                },
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "ROBUSTNESS_STRESS_ITERATE",
                "candidate_id": "parent_sweep0001",
                "pass_count": 2,
                "cost_pass_count": 0,
                "case_count": 7,
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {"status": "BACKTEST_SCREEN_COMPLETE", "no_order_assertions": SAFE_REPORT_ASSERTIONS},
            {
                "status": "READY_FOR_BACKTEST_SCREEN",
                "candidates": [{"candidate_id": "parent"}],
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "gatekeeper_action_packet": {
                    "bithumb_current_actionable_risk_conversion": {"ready_for_gatekeeper_review": True}
                }
            },
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

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertEqual(packet["blockers"], ["robustness_stress_pass"])
        self.assertTrue(packet["readiness_checks"]["risk_guard_hard_safety_pass"])

    def test_packet_blocks_when_risk_guard_hard_safety_fails(self) -> None:
        packet = packet_mod.build_packet(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "top_conversion": {"candidate_id": "parent", "status": "RISK_CONVERSION_PASS"},
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {},
            {
                "status": "OOS_WALKFORWARD_PASS",
                "candidate_id": "parent",
                "aggregate": {"pass_fold_count": 2, "positive_fold_count": 2, "total_trade_count": 8},
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "status": "ROBUSTNESS_STRESS_PASS",
                "candidate_id": "parent",
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {"status": "BACKTEST_SCREEN_COMPLETE", "no_order_assertions": SAFE_REPORT_ASSERTIONS},
            {
                "status": "READY_FOR_BACKTEST_SCREEN",
                "candidates": [{"candidate_id": "parent"}],
                "no_order_assertions": SAFE_REPORT_ASSERTIONS,
            },
            {
                "gatekeeper_action_packet": {
                    "bithumb_current_actionable_risk_conversion": {"ready_for_gatekeeper_review": True}
                }
            },
            {"status": "HALT_RECOMMENDED", "halt_count": 1, "checks": [{"name": "real_orders_zero", "status": "HALT"}]},
        )

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("risk_guard_hard_safety_pass", packet["blockers"])


if __name__ == "__main__":
    unittest.main()
