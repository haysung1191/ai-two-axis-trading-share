from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_model_factory_pull_through_board.py")
SPEC = importlib.util.spec_from_file_location("build_model_factory_pull_through_board", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
board = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(board)


class ModelFactoryPullThroughBoardTests(unittest.TestCase):
    def test_gatekeeper_action_packet_keeps_promotion_and_live_disabled(self) -> None:
        paper_evidence = {
            "evidence_gaps": [
                "INSUFFICIENT_PAPER_CYCLES",
                "INSUFFICIENT_NON_FLAT_SIGNAL_EVIDENCE",
                "INSUFFICIENT_EXECUTABLE_ORDER_EVIDENCE",
            ],
            "thresholds": {
                "min_cycles_for_promotion_review": 288,
                "min_non_flat_signals_for_promotion": 5,
                "min_executable_orders_for_promotion": 5,
            },
            "evidence": {
                "paper_cycles_completed": 90,
                "combined_evidence": {
                    "combined_non_flat_signal_count": 2,
                    "combined_executable_order_evidence_count": 2,
                },
                "acceleration_evidence": {
                    "historical_replay_non_flat_count_excluded": 190,
                    "historical_replay_counts_as_promotion_evidence": False,
                },
            },
        }
        packet = board.gatekeeper_action_packet(
            evidence_rows=[
                {
                    "candidate_id": "bridge_28_relief",
                    "lane": "bithumb_1d",
                    "status": "LOCAL_SIM_PAPER_ACTIVE",
                    "next_action": "collect live-like non-flat executable evidence",
                }
            ],
            repairs=[],
            paper_evidence=paper_evidence,
            capital_allocator={
                "safety": {
                    "broker_submit_allowed": True,
                    "broker_submit_scope": "paper_only",
                    "live_enabled": False,
                    "private_submit_used": False,
                    "real_orders": 0,
                }
            },
            paper_acceleration={
                "evidence_velocity_queue": [
                    {
                        "market": "KRW-BIO",
                        "timeframe": "1d",
                        "side": "long",
                        "velocity_rank_reason": "already_non_flat",
                        "non_flat_trigger_gap": 0.0,
                        "lookback_return": 2.36,
                        "short_return": 0.83,
                        "volume_ratio": 1.3,
                        "counts_as_live_paper_evidence": True,
                        "broker_submit_allowed": False,
                    }
                ]
            },
            paper_progress_delta={
                "pace_summary": {
                    "eta_status": "STALLED_ON_EVENT_EVIDENCE",
                    "slowest_gate_dimension": "non_flat_signals",
                    "estimated_hours_to_cycle_target": 9.5,
                    "promotion_review_eta_hours": None,
                },
                "event_stall_summary": {
                    "event_stall_status": "EVENT_EVIDENCE_STALLED",
                    "stall_severity": "WARN_STALL",
                    "safe_next_action": "Continue safe paper loop, but monitor nearest flat target and stall age closely.",
                    "non_flat_signals": {
                        "hours_since_last_increase": 2.0,
                        "paper_cycles_since_last_increase": 25,
                    },
                    "executable_orders": {
                        "hours_since_last_increase": 2.0,
                        "paper_cycles_since_last_increase": 25,
                    },
                },
            },
        )

        self.assertTrue(packet["paper_scope_ok"])
        self.assertFalse(packet["promotion_allowed_by_this_report"])
        self.assertFalse(packet["live_allowed_by_this_report"])
        self.assertFalse(packet["real_orders_allowed_by_this_report"])

    def test_bithumb_orca_oos_family_review_is_visible_and_no_order(self) -> None:
        report = {
            "status": "ORCA_OOS_FAMILY_REVIEW_READY",
            "market": "KRW-ORCA",
            "family": "bithumb_current_actionable_orca_1d_long_freeze001",
            "oos_pass_candidate_count": 6,
            "distinct_parameter_count": 5,
            "top_candidate": {
                "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                "estimated_cagr": 1.39,
                "estimated_mdd": -0.2,
            },
            "review_value": {"reduces_single_registered_candidate_dependency": True},
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "shadow_registration_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            [],
            [],
            {
                "evidence_gaps": [
                    "INSUFFICIENT_PAPER_CYCLES",
                    "INSUFFICIENT_NON_FLAT_SIGNAL_EVIDENCE",
                    "INSUFFICIENT_EXECUTABLE_ORDER_EVIDENCE",
                ],
                "thresholds": {
                    "min_cycles_for_promotion_review": 288,
                    "min_non_flat_signals_for_promotion": 5,
                    "min_executable_orders_for_promotion": 5,
                },
                "evidence": {
                    "paper_cycles_completed": 90,
                    "combined_evidence": {
                        "combined_non_flat_signal_count": 2,
                        "combined_executable_order_evidence_count": 2,
                    },
                    "acceleration_evidence": {
                        "historical_replay_counts_as_promotion_evidence": False,
                    },
                },
            },
            {"safety": {"broker_submit_allowed": True, "broker_submit_scope": "paper_only", "live_enabled": False, "private_submit_used": False, "real_orders": 0}},
            paper_acceleration={
                "evidence_velocity_queue": [
                    {
                        "market": "KRW-BIO",
                        "timeframe": "1d",
                        "side": "long",
                        "velocity_rank_reason": "already_non_flat",
                        "non_flat_trigger_gap": 0.0,
                        "lookback_return": 2.36,
                        "short_return": 0.83,
                        "volume_ratio": 1.3,
                        "counts_as_live_paper_evidence": True,
                        "broker_submit_allowed": False,
                    }
                ]
            },
            paper_progress_delta={
                "pace_summary": {
                    "eta_status": "STALLED_ON_EVENT_EVIDENCE",
                    "slowest_gate_dimension": "non_flat_signals",
                    "promotion_review_eta_hours": None,
                },
                "event_stall_summary": {
                    "event_stall_status": "EVENT_EVIDENCE_STALLED",
                    "stall_severity": "WARN_STALL",
                    "safe_next_action": "Continue safe paper loop, but monitor nearest flat target and stall age closely.",
                    "non_flat_signals": {
                        "hours_since_last_increase": 2.0,
                        "paper_cycles_since_last_increase": 25,
                    },
                    "executable_orders": {
                        "hours_since_last_increase": 2.0,
                        "paper_cycles_since_last_increase": 25,
                    },
                },
            },
            bithumb_current_actionable_orca_oos_family_review=report,
        )

        summary = packet["bithumb_current_actionable_orca_oos_family_review"]
        self.assertEqual(summary["status"], "ORCA_OOS_FAMILY_REVIEW_READY")
        self.assertTrue(summary["ready_for_review"])
        self.assertEqual(summary["oos_pass_candidate_count"], 6)
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertEqual(packet["paper_evidence_gap_summary"]["non_flat_signals_missing"], 3)
        self.assertEqual(packet["paper_evidence_gap_summary"]["executable_orders_missing"], 3)
        self.assertFalse(packet["paper_evidence_gap_summary"]["historical_replay_counts_as_promotion_evidence"])
        self.assertEqual(packet["paper_evidence_pace_summary"]["eta_status"], "STALLED_ON_EVENT_EVIDENCE")
        self.assertEqual(packet["paper_evidence_pace_summary"]["slowest_gate_dimension"], "non_flat_signals")
        self.assertIsNone(packet["paper_evidence_pace_summary"]["promotion_review_eta_hours"])
        self.assertEqual(
            packet["paper_evidence_event_stall_summary"]["event_stall_status"],
            "EVENT_EVIDENCE_STALLED",
        )
        self.assertEqual(packet["paper_evidence_event_stall_summary"]["stall_severity"], "WARN_STALL")
        self.assertEqual(
            packet["paper_evidence_event_stall_summary"]["non_flat_signals"]["paper_cycles_since_last_increase"],
            25,
        )
        self.assertEqual(packet["paper_evidence_velocity_targets"][0]["market"], "KRW-BIO")
        self.assertFalse(packet["paper_evidence_velocity_targets"][0]["broker_submit_allowed"])

        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )
        self.assertIn("pace_eta_status: `STALLED_ON_EVENT_EVIDENCE`", rendered)
        self.assertIn("slowest_gate_dimension: `non_flat_signals`", rendered)
        self.assertIn("event_stall_status: `EVENT_EVIDENCE_STALLED`", rendered)
        self.assertIn("stall_severity: `WARN_STALL`", rendered)
        self.assertIn("monitor nearest flat target", rendered)
        self.assertIn("non_flat_hours_since_last_increase: `2.0`", rendered)

    def test_paper_evidence_velocity_targets_are_report_only(self) -> None:
        targets = board.paper_evidence_velocity_targets(
            {
                "evidence_velocity_queue": [
                    {
                        "market": "KRW-ETH",
                        "timeframe": "1h",
                        "side": "flat",
                        "velocity_rank_reason": "nearest_to_non_flat_trigger",
                        "non_flat_trigger_gap": 0.003,
                        "lookback_return": -0.001,
                        "short_return": -0.001,
                        "volume_ratio": 0.52,
                        "counts_as_live_paper_evidence": True,
                        "broker_submit_allowed": True,
                    }
                ]
            }
        )

        self.assertEqual(targets[0]["operator_use"], "observe_for_next_live_like_non_flat_executable_paper_evidence")
        self.assertTrue(targets[0]["counts_as_live_paper_evidence"])
        self.assertFalse(targets[0]["broker_submit_allowed"])

    def test_intraday_backtest_lifts_lane_to_oos_without_order_paths(self) -> None:
        funnel = board.build_funnel(
            registry_rows=[],
            scoreboard={},
            paper_evidence={},
            intraday_intake={"candidate_count": 4},
            intraday_backtest={"screened_count": 4, "pass_count": 1},
        )
        btc_eth = next(row for row in funnel if row["lane"] == "btc_eth_1h4h")

        self.assertEqual(btc_eth["generated"], 4)
        self.assertEqual(btc_eth["validation_pass"], 1)
        self.assertEqual(btc_eth["main_bottleneck"], "G04 OOS/walk-forward")

        summary = board.intraday_backtest_summary(
            {
                "status": "BACKTEST_SCREEN_COMPLETE",
                "screened_count": 4,
                "pass_count": 1,
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            }
        )

        self.assertTrue(summary["ready_for_oos_review"])
        self.assertFalse(summary["promotion_allowed_by_this_report"])
        self.assertFalse(summary["live_allowed_by_this_report"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])

    def test_intraday_sweep_lifts_lane_to_freeze_candidate_without_order_paths(self) -> None:
        funnel = board.build_funnel(
            registry_rows=[],
            scoreboard={},
            paper_evidence={},
            intraday_intake={"candidate_count": 4},
            intraday_backtest={"screened_count": 4, "pass_count": 0},
            intraday_sweep={"sweep_count": 4, "pass_like_count": 1},
        )
        btc_eth = next(row for row in funnel if row["lane"] == "btc_eth_1h4h")

        self.assertEqual(btc_eth["generated"], 5)
        self.assertEqual(btc_eth["main_bottleneck"], "G03 freeze sweep candidate")

        summary = board.intraday_sweep_summary(
            {
                "status": "SWEEP_COMPLETE",
                "sweep_count": 4,
                "pass_like_count": 1,
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            }
        )

        self.assertTrue(summary["ready_to_freeze_candidate"])
        self.assertFalse(summary["promotion_allowed_by_this_report"])
        self.assertFalse(summary["live_allowed_by_this_report"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])

    def test_intraday_frozen_candidate_lifts_lane_to_oos_without_order_paths(self) -> None:
        funnel = board.build_funnel(
            registry_rows=[],
            scoreboard={},
            paper_evidence={},
            intraday_intake={"candidate_count": 4},
            intraday_backtest={"screened_count": 4, "pass_count": 0},
            intraday_sweep={"sweep_count": 4, "pass_like_count": 1},
            intraday_frozen={"frozen_candidate_count": 1},
        )
        btc_eth = next(row for row in funnel if row["lane"] == "btc_eth_1h4h")

        self.assertEqual(btc_eth["generated"], 5)
        self.assertEqual(btc_eth["validation_pass"], 0)
        self.assertEqual(btc_eth["main_bottleneck"], "G04 OOS/walk-forward")

        summary = board.intraday_frozen_summary(
            {
                "status": "READY_FOR_OOS_RESEARCH_REVIEW",
                "frozen_candidate_count": 1,
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            }
        )

        self.assertTrue(summary["ready_for_oos_review"])
        self.assertFalse(summary["promotion_allowed_by_this_report"])
        self.assertFalse(summary["live_allowed_by_this_report"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])

    def test_intraday_oos_pass_lifts_lane_to_risk_conversion_without_order_paths(self) -> None:
        funnel = board.build_funnel(
            registry_rows=[],
            scoreboard={},
            paper_evidence={},
            intraday_intake={"candidate_count": 4},
            intraday_backtest={"screened_count": 4, "pass_count": 0},
            intraday_sweep={"sweep_count": 4, "pass_like_count": 1},
            intraday_frozen={"frozen_candidate_count": 1},
            intraday_oos={"status": "OOS_WALKFORWARD_PASS"},
        )
        btc_eth = next(row for row in funnel if row["lane"] == "btc_eth_1h4h")

        self.assertEqual(btc_eth["generated"], 5)
        self.assertEqual(btc_eth["validation_pass"], 1)
        self.assertEqual(btc_eth["main_bottleneck"], "G06 risk conversion")

        summary = board.intraday_oos_summary(
            {
                "status": "OOS_WALKFORWARD_PASS",
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "aggregate": {
                    "pass_fold_count": 2,
                    "positive_fold_count": 2,
                    "worst_fold_mdd": -0.12,
                    "average_fold_cagr": 0.1,
                    "total_trade_count": 42,
                },
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            }
        )

        self.assertTrue(summary["ready_for_risk_conversion"])
        self.assertFalse(summary["promotion_allowed_by_this_report"])
        self.assertFalse(summary["live_allowed_by_this_report"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])

    def test_intraday_oos_stability_review_is_report_only(self) -> None:
        stability = {
            "status": "OOS_STABILITY_ITERATE",
            "evaluated_trial_count": 20,
            "stability_pass_count": 2,
            "current_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "best_candidate_id": "btc_eth_intraday_momentum_btc_4h__stability_001",
            "best_improves_current": False,
            "best_worst_fold_mdd": -0.167,
            "best_average_fold_cagr": 0.03,
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            btc_eth_intraday_oos_stability=stability,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["btc_eth_intraday_oos_stability_review"]
        self.assertFalse(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["evaluated_trial_count"], 20)
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertIn("btc_eth_intraday_oos_stability_status: `OOS_STABILITY_ITERATE`", rendered)
        self.assertIn("btc_eth_intraday_oos_stability_evaluated_count: `20`", rendered)

    def test_intraday_robustness_stress_surfaces_as_review_only_evidence(self) -> None:
        robustness = {
            "status": "ROBUSTNESS_STRESS_PASS",
            "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "market": "KRW-BTC",
            "timeframe": "4h",
            "case_count": 7,
            "pass_count": 5,
            "cost_pass_count": 1,
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            btc_eth_intraday_robustness=robustness,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["btc_eth_intraday_robustness_stress"]
        self.assertTrue(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["pass_count"], 5)
        self.assertFalse(summary["counts_as_paper_or_live_evidence"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertIn("btc_eth_intraday_robustness_status: `ROBUSTNESS_STRESS_PASS`", rendered)
        self.assertIn("btc_eth_intraday_robustness_counts_as_paper_or_live_evidence: `False`", rendered)

    def test_intraday_cost_friction_review_surfaces_as_review_only_evidence(self) -> None:
        friction = {
            "status": "BTC_ETH_INTRADAY_COST_FRICTION_REVIEW_READY",
            "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "robustness_status": "ROBUSTNESS_STRESS_ITERATE",
            "case_count": 7,
            "pass_count": 4,
            "cost_pass_count": 0,
            "cost_case_count": 2,
            "recommended_action": "KEEP_RESEARCH_ONLY_REQUIRE_COST_FRICTION_REPAIR_BEFORE_SHADOW_OR_PAPER_USE",
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": {
                "mutation_allowed_by_this_report": False,
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            btc_eth_intraday_cost_friction=friction,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["btc_eth_intraday_cost_friction_review"]
        self.assertTrue(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["cost_pass_count"], 0)
        self.assertFalse(summary["counts_as_paper_or_live_evidence"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertIn("btc_eth_intraday_cost_friction_status: `BTC_ETH_INTRADAY_COST_FRICTION_REVIEW_READY`", rendered)
        self.assertIn("btc_eth_intraday_cost_friction_cost_pass_count: `0`", rendered)

    def test_intraday_robustness_repair_review_surfaces_negative_evidence(self) -> None:
        repair = {
            "status": "ROBUSTNESS_REPAIR_ITERATE",
            "base_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "trial_count": 432,
            "evaluated_oos_pass_trial_count": 2,
            "repair_pass_count": 0,
            "best_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001_robustrepair_049",
            "best_pass_count": 4,
            "best_cost_pass_count": 0,
            "best_cost_case_id": "cost_30bps",
            "best_cost_total_return": -0.0328,
            "best_cost_return_gap_to_pass": 0.0328,
            "best_cost_mdd": -0.1895,
            "best_cost_mdd_gap_to_pass": 0.0,
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            btc_eth_intraday_robustness_repair=repair,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["btc_eth_intraday_robustness_repair_review"]
        self.assertFalse(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["trial_count"], 432)
        self.assertEqual(summary["repair_pass_count"], 0)
        self.assertEqual(summary["best_cost_case_id"], "cost_30bps")
        self.assertEqual(summary["best_cost_return_gap_to_pass"], 0.0328)
        self.assertFalse(summary["counts_as_paper_or_live_evidence"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertIn("btc_eth_intraday_robustness_repair_status: `ROBUSTNESS_REPAIR_ITERATE`", rendered)
        self.assertIn("btc_eth_intraday_robustness_repair_best_cost_pass_count: `0`", rendered)
        self.assertIn("btc_eth_intraday_robustness_repair_best_cost_case_id: `cost_30bps`", rendered)
        self.assertIn("btc_eth_intraday_robustness_repair_best_cost_return_gap_to_pass: `3.28%`", rendered)

    def test_intraday_robustness_repair_delta_review_is_visible_and_no_order(self) -> None:
        delta = {
            "status": "ROBUSTNESS_REPAIR_DELTA_REVIEW_READY",
            "base_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
            "child_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001_robustrepair_445",
            "lineage_match": True,
            "base_conversion": {
                "estimated_average_fold_cagr": 0.19,
                "estimated_worst_fold_mdd": -0.12,
            },
            "child_conversion": {
                "recommended_exposure_cap": 0.65,
                "estimated_average_fold_cagr": 0.29,
                "estimated_worst_fold_mdd": -0.12,
            },
            "delta": {
                "estimated_average_fold_cagr_delta": 0.10,
                "estimated_worst_fold_mdd_delta": 0.0,
                "trade_count_delta": -30,
            },
            "repair_stress": {
                "best_cost_pass_count": 2,
                "best_cost_case_id": "cost_30bps",
            },
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            btc_eth_intraday_robustness_repair_delta=delta,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["btc_eth_intraday_robustness_repair_delta_review"]
        self.assertTrue(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["child_candidate_id"], "btc_eth_intraday_momentum_btc_4h_sweep001_robustrepair_445")
        self.assertTrue(summary["lineage_match"])
        self.assertEqual(summary["trade_count_delta"], -30)
        self.assertEqual(summary["best_cost_pass_count"], 2)
        self.assertFalse(summary["counts_as_paper_or_live_evidence"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertIn(
            "btc_eth_intraday_robustness_repair_delta_status: `ROBUSTNESS_REPAIR_DELTA_REVIEW_READY`",
            rendered,
        )
        self.assertIn("btc_eth_intraday_robustness_repair_delta_capped_cagr_delta: `10.00%`", rendered)

    def test_intraday_risk_conversion_lifts_lane_to_shadow_review_without_order_paths(self) -> None:
        funnel = board.build_funnel(
            registry_rows=[],
            scoreboard={},
            paper_evidence={},
            intraday_intake={"candidate_count": 4},
            intraday_backtest={"screened_count": 4, "pass_count": 0},
            intraday_sweep={"sweep_count": 4, "pass_like_count": 1},
            intraday_frozen={"frozen_candidate_count": 1},
            intraday_oos={"status": "OOS_WALKFORWARD_PASS"},
            intraday_risk={"status": "READY_FOR_GATEKEEPER_REVIEW"},
        )
        btc_eth = next(row for row in funnel if row["lane"] == "btc_eth_1h4h")

        self.assertEqual(btc_eth["conversion_pass"], 1)
        self.assertEqual(btc_eth["main_bottleneck"], "G07 shadow review")

        summary = board.intraday_risk_summary(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "conversion": {
                    "recommended_exposure_cap": 0.75,
                    "estimated_average_fold_cagr": 0.06,
                    "estimated_worst_fold_mdd": -0.12,
                },
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            }
        )

        self.assertTrue(summary["ready_for_shadow_review"])
        self.assertFalse(summary["promotion_allowed_by_this_report"])
        self.assertFalse(summary["live_allowed_by_this_report"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])

    def test_intraday_shadow_packet_lifts_lane_to_human_review_without_order_paths(self) -> None:
        funnel = board.build_funnel(
            registry_rows=[],
            scoreboard={},
            paper_evidence={},
            intraday_intake={"candidate_count": 4},
            intraday_backtest={"screened_count": 4, "pass_count": 0},
            intraday_sweep={"sweep_count": 4, "pass_like_count": 1},
            intraday_frozen={"frozen_candidate_count": 1},
            intraday_oos={"status": "OOS_WALKFORWARD_PASS"},
            intraday_risk={"status": "READY_FOR_GATEKEEPER_REVIEW"},
            intraday_shadow_packet={"status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW"},
        )
        btc_eth = next(row for row in funnel if row["lane"] == "btc_eth_1h4h")

        self.assertEqual(btc_eth["conversion_pass"], 1)
        self.assertEqual(btc_eth["main_bottleneck"], "G07 human Gatekeeper review")

        summary = board.intraday_shadow_packet_summary(
            {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "blockers": [],
                "no_order_assertions": {
                    "promotion_allowed_by_this_packet": False,
                    "shadow_enabled_by_this_packet": False,
                    "paper_enabled_by_this_packet": False,
                    "live_allowed_by_this_packet": False,
                    "broker_submit_allowed_by_this_packet": False,
                    "private_submit_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                },
            }
        )

        self.assertTrue(summary["ready_for_human_gatekeeper_review"])
        self.assertFalse(summary["shadow_enabled_by_this_report"])
        self.assertFalse(summary["promotion_allowed_by_this_report"])
        self.assertFalse(summary["live_allowed_by_this_report"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])

    def test_intraday_shadow_preflight_keeps_lane_pending_without_starting_shadow(self) -> None:
        funnel = board.build_funnel(
            registry_rows=[],
            scoreboard={},
            paper_evidence={},
            intraday_intake={"candidate_count": 4},
            intraday_backtest={"screened_count": 4, "pass_count": 0},
            intraday_sweep={"sweep_count": 4, "pass_like_count": 1},
            intraday_frozen={"frozen_candidate_count": 1},
            intraday_oos={"status": "OOS_WALKFORWARD_PASS"},
            intraday_risk={"status": "READY_FOR_GATEKEEPER_REVIEW"},
            intraday_shadow_packet={"status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW"},
            intraday_shadow_preflight={"status": "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION"},
        )
        btc_eth = next(row for row in funnel if row["lane"] == "btc_eth_1h4h")

        self.assertEqual(btc_eth["main_bottleneck"], "G07 shadow decision pending")

        summary = board.intraday_shadow_preflight_summary(
            {
                "status": "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION",
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "blockers": ["HUMAN_GATEKEEPER_SHADOW_DECISION_MISSING"],
                "safety": {
                    "does_register_shadow_candidate": False,
                    "does_start_shadow_loop": False,
                    "does_enable_paper": False,
                    "does_enable_live": False,
                    "broker_submit_allowed": False,
                    "private_submit_allowed": False,
                    "real_orders_allowed": False,
                },
            }
        )

        self.assertFalse(summary["ready_for_shadow_registration"])
        self.assertFalse(summary["does_register_shadow_candidate"])
        self.assertFalse(summary["does_start_shadow_loop"])
        self.assertFalse(summary["paper_enabled_by_this_report"])
        self.assertFalse(summary["live_allowed_by_this_report"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])

    def test_intraday_shadow_decision_template_surfaces_pending_and_approval_states_without_side_effects(self) -> None:
        pending_funnel = board.build_funnel(
            registry_rows=[],
            scoreboard={},
            paper_evidence={},
            intraday_intake={"candidate_count": 4},
            intraday_backtest={"screened_count": 4, "pass_count": 0},
            intraday_sweep={"sweep_count": 4, "pass_like_count": 1},
            intraday_frozen={"frozen_candidate_count": 1},
            intraday_oos={"status": "OOS_WALKFORWARD_PASS"},
            intraday_risk={"status": "READY_FOR_GATEKEEPER_REVIEW"},
            intraday_shadow_packet={"status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW"},
            intraday_shadow_preflight={"status": "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION"},
            intraday_shadow_decision_template={"status": "PENDING_HUMAN_GATEKEEPER_DECISION"},
        )
        btc_eth = next(row for row in pending_funnel if row["lane"] == "btc_eth_1h4h")

        self.assertEqual(btc_eth["main_bottleneck"], "G07 shadow decision pending")

        approved_funnel = board.build_funnel(
            registry_rows=[],
            scoreboard={},
            paper_evidence={},
            intraday_intake={"candidate_count": 4},
            intraday_backtest={"screened_count": 4, "pass_count": 0},
            intraday_sweep={"sweep_count": 4, "pass_like_count": 1},
            intraday_frozen={"frozen_candidate_count": 1},
            intraday_oos={"status": "OOS_WALKFORWARD_PASS"},
            intraday_risk={"status": "READY_FOR_GATEKEEPER_REVIEW"},
            intraday_shadow_packet={"status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW"},
            intraday_shadow_preflight={"status": "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION"},
            intraday_shadow_decision_template={"status": "HUMAN_GATEKEEPER_SHADOW_DECISION_RECORDED"},
        )
        btc_eth_approved = next(row for row in approved_funnel if row["lane"] == "btc_eth_1h4h")

        self.assertEqual(btc_eth_approved["main_bottleneck"], "G07 shadow registration pending")

        summary = board.intraday_shadow_decision_template_summary(
            {
                "status": "PENDING_HUMAN_GATEKEEPER_DECISION",
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "blockers": ["HUMAN_GATEKEEPER_SHADOW_DECISION_MISSING"],
                "human_decision": {
                    "present": False,
                    "valid": False,
                    "decision_recorded": False,
                },
                "approved_for_separate_shadow_registration_review": False,
                "safety": {
                    "does_register_shadow_candidate": False,
                    "does_start_shadow_loop": False,
                    "does_enable_paper": False,
                    "does_enable_live": False,
                    "broker_submit_allowed": False,
                    "private_submit_allowed": False,
                    "real_orders_allowed": False,
                },
            }
        )

        self.assertFalse(summary["decision_recorded"])
        self.assertFalse(summary["approved_for_separate_shadow_registration_review"])
        self.assertFalse(summary["does_register_shadow_candidate"])
        self.assertFalse(summary["does_start_shadow_loop"])
        self.assertFalse(summary["paper_enabled_by_this_report"])
        self.assertFalse(summary["live_allowed_by_this_report"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])

    def test_candidate_specific_conversion_evidence_is_report_only(self) -> None:
        evidence = board.candidate_specific_conversion_evidence(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "candidate_id": "stock_aggressive_trim22",
                "source_evidence_type": "existing_candidate_backtest_row_plus_fixed_exposure_overlay",
                "after_fixed_exposure": {
                    "overlay": "fixed_exposure_065",
                    "estimated_cagr": 0.459,
                    "estimated_mdd": -0.199,
                    "estimated_sharpe": 1.74,
                    "gate_result": "pass_mdd_margin",
                },
                "safety": {
                    "live_enabled": False,
                    "broker_submit_allowed": False,
                    "private_submit_used": False,
                    "real_orders": 0,
                },
                "next_action": "Gatekeeper may review this candidate-specific conversion evidence.",
            }
        )

        self.assertTrue(evidence["ready_for_gatekeeper_review"])
        self.assertEqual(evidence["overlay"], "fixed_exposure_065")
        self.assertFalse(evidence["promotion_allowed_by_this_report"])
        self.assertFalse(evidence["live_allowed_by_this_report"])
        self.assertFalse(evidence["real_orders_allowed_by_this_report"])

    def test_ranked_risk_conversion_targets_prefers_high_sharpe_stock_candidates(self) -> None:
        repairs = [
            {
                "candidate_id": "weak_crypto",
                "lane": "bithumb_1d",
                "failure_reason": "MDD_TOO_HIGH",
                "cagr": 0.9,
                "mdd": -0.4,
                "sharpe": 3.0,
            },
            {
                "candidate_id": "stock_high_sharpe",
                "lane": "kis_stocks",
                "status": "SHADOW_READY",
                "failure_reason": "MDD_TOO_HIGH",
                "cagr": 0.7,
                "mdd": -0.31,
                "sharpe": 1.8,
                "required_mdd_reduction_to_20pct": 0.11,
            },
            {
                "candidate_id": "stock_low_sharpe",
                "lane": "kis_etfs",
                "status": "SHADOW_READY",
                "failure_reason": "MDD_TOO_HIGH",
                "cagr": 0.8,
                "mdd": -0.35,
                "sharpe": 1.4,
                "required_mdd_reduction_to_20pct": 0.15,
            },
        ]

        targets = board.ranked_risk_conversion_targets(repairs)

        self.assertEqual([row["candidate_id"] for row in targets], ["stock_high_sharpe", "stock_low_sharpe"])
        self.assertEqual(targets[0]["safe_experiment_scope"], "risk_conversion_only_no_order_paths")
        self.assertEqual(targets[0]["fixed_exposure_recipe"]["recommended_fixed_exposure_cap"], 0.64)
        self.assertFalse(targets[0]["fixed_exposure_recipe"]["order_paths_allowed"])

    def test_fixed_exposure_recipe_is_sizing_only_and_hits_mdd_target(self) -> None:
        recipe = board.fixed_exposure_risk_conversion_recipe(
            {
                "candidate_id": "stock_aggressive",
                "cagr": 0.706,
                "mdd": -0.3065,
            }
        )

        self.assertEqual(recipe["experiment_scope"], "sizing_overlay_only_no_signal_logic_change")
        self.assertFalse(recipe["child_candidate_required"])
        self.assertFalse(recipe["order_paths_allowed"])
        self.assertLessEqual(abs(recipe["estimated_capped_mdd"]), 0.20)
        self.assertGreater(recipe["estimated_capped_cagr"], 0.45)

    def test_paper_smoke_packet_summary_is_report_only_gatekeeper_input(self) -> None:
        summary = board.paper_smoke_review_packet_summary(
            {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "review_ready": True,
                "recommended_gatekeeper_lane": "PAPER_SMOKE_REVIEW_READY",
                "blockers": [],
                "evidence_summary": {
                    "paper_cycles_completed": 175,
                    "combined_non_flat_signal_count": 2,
                    "combined_executable_order_evidence_count": 2,
                    "extended_paper_ready": False,
                    "historical_replay_non_flat_excluded": 197,
                },
                "permissions": {
                    "promotion_allowed_by_this_packet": False,
                    "extended_paper_promotion_allowed_by_this_packet": False,
                    "live_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                    "private_submit_allowed_by_this_packet": False,
                    "broker_submit_scope_required": "paper_only",
                },
            }
        )

        self.assertTrue(summary["review_ready"])
        self.assertEqual(summary["status"], "READY_FOR_GATEKEEPER_REVIEW")
        self.assertEqual(summary["blocker_count"], 0)
        self.assertFalse(summary["extended_paper_ready"])
        self.assertEqual(summary["historical_replay_non_flat_excluded"], 197)

    def test_event_stall_triage_summary_is_report_only_gatekeeper_input(self) -> None:
        summary = board.event_stall_triage_summary(
            {
                "status": "READY_FOR_STALL_REVIEW",
                "review_ready": True,
                "blockers": [],
                "stall_summary": {
                    "event_stall_status": "EVENT_EVIDENCE_STALLED",
                    "stall_severity": "WARN_STALL",
                    "slowest_gate_dimension": "non_flat_signals",
                },
                "evidence_gap_summary": {
                    "non_flat_signals_missing": 3,
                    "executable_orders_missing": 3,
                },
                "replay_policy": {
                    "historical_replay_non_flat_count": 197,
                    "counts_as_extended_paper_promotion": False,
                    "counts_as_live_readiness": False,
                },
                "permissions": {
                    "promotion_allowed_by_this_report": False,
                    "extended_paper_promotion_allowed_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            }
        )

        self.assertTrue(summary["review_ready"])
        self.assertEqual(summary["status"], "READY_FOR_STALL_REVIEW")
        self.assertEqual(summary["blocker_count"], 0)
        self.assertEqual(summary["event_stall_status"], "EVENT_EVIDENCE_STALLED")
        self.assertFalse(summary["counts_as_extended_paper_promotion"])
        self.assertFalse(summary["counts_as_live_readiness"])
        self.assertFalse(summary["promotion_allowed_by_this_report"])
        self.assertFalse(summary["live_allowed_by_this_report"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])

    def test_intraday_intake_lifts_empty_lane_without_order_paths(self) -> None:
        intake = {
            "status": "READY_FOR_BACKTEST_INTAKE",
            "candidate_count": 4,
            "non_flat_candidate_count": 0,
            "nearest_trigger_candidate": {"candidate_id": "btc_eth_intraday_momentum_eth_1h"},
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
            "next_action": "Run a frozen backtest screen.",
        }

        funnel = board.build_funnel([], {}, {}, intake)
        intraday = next(row for row in funnel if row["lane"] == "btc_eth_1h4h")
        summary = board.intraday_intake_summary(intake)

        self.assertEqual(intraday["generated"], 4)
        self.assertEqual(intraday["gatekeeper_intake"], 0)
        self.assertEqual(intraday["main_bottleneck"], "G03 backtest intake")
        self.assertTrue(summary["ready_for_backtest_intake"])
        self.assertFalse(summary["promotion_allowed_by_this_report"])
        self.assertFalse(summary["live_allowed_by_this_report"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])

    def test_bithumb_current_actionable_intake_is_report_only(self) -> None:
        intake = {
            "status": "CURRENT_ACTIONABLE_CANDIDATES_FOUND",
            "candidate_count": 13,
            "current_actionable_count": 2,
            "near_trigger_count": 11,
            "top_current_actionable": [
                {"market": "KRW-BIO", "candidate_id": "bithumb_current_actionable_bio_1d_long"},
                {"market": "KRW-POLA", "candidate_id": "bithumb_current_actionable_pola_1d_long"},
            ],
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
            "next_action": "Freeze and backtest the top current-actionable Bithumb candidates.",
        }

        summary = board.bithumb_actionable_intake_summary(intake)
        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_current_actionable_intake=intake,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        self.assertEqual(summary["current_actionable_count"], 2)
        self.assertEqual(summary["top_current_actionable_markets"], ["KRW-BIO", "KRW-POLA"])
        self.assertTrue(summary["ready_for_backtest_intake"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertEqual(
            packet["bithumb_current_actionable_candidate_intake"]["top_current_actionable_markets"],
            ["KRW-BIO", "KRW-POLA"],
        )
        self.assertIn("bithumb_current_actionable_count: `2`", rendered)
        self.assertIn("bithumb_current_actionable_top_markets: `KRW-BIO, KRW-POLA`", rendered)

    def test_bithumb_current_actionable_frozen_and_backtest_are_report_only(self) -> None:
        frozen = {
            "status": "READY_FOR_BACKTEST_SCREEN",
            "frozen_candidate_count": 2,
            "candidates": [
                {"candidate_id": "bithumb_current_actionable_bio_1d_long_freeze001"},
                {"candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001"},
            ],
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }
        backtest = {
            "status": "BACKTEST_SCREEN_COMPLETE",
            "screened_count": 2,
            "pass_count": 1,
            "top_screen": {"candidate_id": "bithumb_current_actionable_bio_1d_long_freeze001"},
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_current_actionable_frozen=frozen,
            bithumb_current_actionable_backtest=backtest,
        )

        self.assertTrue(packet["bithumb_current_actionable_frozen_candidate"]["ready_for_backtest_screen"])
        self.assertTrue(packet["bithumb_current_actionable_backtest_screen"]["ready_for_oos_review"])
        self.assertFalse(packet["bithumb_current_actionable_backtest_screen"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(packet["bithumb_current_actionable_backtest_screen"]["real_orders_allowed_by_this_report"])

    def test_bithumb_current_actionable_risk_conversion_is_report_only(self) -> None:
        risk = {
            "status": "READY_FOR_GATEKEEPER_REVIEW",
            "converted_count": 2,
            "pass_count": 1,
            "top_conversion": {
                "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
                "market": "KRW-POLA",
                "conversion": {
                    "recommended_exposure_cap": 0.53,
                    "estimated_cagr": 0.22,
                    "estimated_mdd": -0.20,
                },
            },
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_current_actionable_risk=risk,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["bithumb_current_actionable_risk_conversion"]
        self.assertTrue(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["top_candidate_id"], "bithumb_current_actionable_pola_1d_long_freeze001")
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertIn("bithumb_current_actionable_risk_status: `READY_FOR_GATEKEEPER_REVIEW`", rendered)
        self.assertIn("bithumb_current_actionable_ready_for_gatekeeper_review: `True`", rendered)

    def test_bithumb_current_actionable_parameter_sweep_is_report_only(self) -> None:
        sweep = {
            "status": "READY_FOR_GATEKEEPER_REVIEW",
            "sweep_count": 12,
            "pass_like_count": 3,
            "top_sweep": {
                "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep0001",
                "parent_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
                "market": "KRW-POLA",
                "conversion": {
                    "recommended_exposure_cap": 1.0,
                    "estimated_cagr": 1.1,
                    "estimated_mdd": -0.19,
                },
            },
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_current_actionable_sweep=sweep,
        )

        summary = packet["bithumb_current_actionable_parameter_sweep"]
        self.assertTrue(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["pass_like_count"], 3)
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])

    def test_bithumb_current_actionable_oos_walkforward_is_report_only(self) -> None:
        oos = {
            "status": "OOS_WALKFORWARD_ITERATE",
            "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep0001",
            "parent_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
            "market": "KRW-POLA",
            "aggregate": {
                "pass_fold_count": 1,
                "positive_fold_count": 1,
                "worst_fold_mdd": -0.14,
                "average_fold_cagr": 5.7,
                "total_trade_count": 8,
            },
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_current_actionable_oos=oos,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["bithumb_current_actionable_oos_walkforward"]
        self.assertFalse(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["pass_fold_count"], 1)
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertIn("bithumb_current_actionable_oos_status: `OOS_WALKFORWARD_ITERATE`", rendered)

    def test_bithumb_current_actionable_robustness_stress_is_report_only(self) -> None:
        stress = {
            "status": "ROBUSTNESS_STRESS_PASS",
            "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354",
            "market": "KRW-POLA",
            "case_count": 7,
            "pass_count": 4,
            "cost_pass_count": 2,
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_current_actionable_robustness=stress,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["bithumb_current_actionable_robustness_stress"]
        self.assertTrue(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["cost_pass_count"], 2)
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertIn("bithumb_current_actionable_robustness_status: `ROBUSTNESS_STRESS_PASS`", rendered)

    def test_bithumb_current_actionable_alternate_robustness_is_visible_and_no_order(self) -> None:
        alternate = {
            "status": "ALTERNATE_ROBUSTNESS_ITERATE",
            "evaluated_oos_pass_candidate_count": 6,
            "robustness_pass_candidate_count": 0,
            "top_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
            "best_alternate_candidate_id": None,
            "candidate_results": [
                {
                    "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                    "market": "KRW-ORCA",
                    "status": "ROBUSTNESS_STRESS_ITERATE",
                    "pass_count": 0,
                    "cost_pass_count": 0,
                    "oos_total_trade_count": 11,
                }
            ],
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_current_actionable_alternate_robustness=alternate,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["bithumb_current_actionable_alternate_robustness"]
        self.assertFalse(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["evaluated_oos_pass_candidate_count"], 6)
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertIn("bithumb_current_actionable_alternate_robustness_status: `ALTERNATE_ROBUSTNESS_ITERATE`", rendered)
        self.assertIn("bithumb_current_actionable_alternate_robustness_evaluated_count: `6`", rendered)

    def test_bithumb_current_actionable_alternate_robustness_failure_is_visible_and_no_order(self) -> None:
        failure = {
            "status": "BITHUMB_ALTERNATE_ROBUSTNESS_FAILURE_REVIEW_READY",
            "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
            "alternate_robustness_status": "ALTERNATE_ROBUSTNESS_ITERATE",
            "evaluated_oos_pass_candidate_count": 6,
            "robustness_pass_candidate_count": 0,
            "best_alternate_candidate_id": None,
            "candidate_result_count": 6,
            "top_candidate_results": [{"candidate_id": "orca_1507", "pass_count": 0}],
            "oos_alternates_count_as_gatekeeper_relief": False,
            "recommended_action": "STOP_TREATING_OOS_ALTERNATES_AS_GATEKEEPER_RELIEF_REQUIRE_ROBUSTNESS_OR_NEW_FAMILY",
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": {
                "mutation_allowed_by_this_report": False,
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_current_actionable_alternate_robustness_failure=failure,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["bithumb_current_actionable_alternate_robustness_failure_review"]
        self.assertTrue(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["evaluated_oos_pass_candidate_count"], 6)
        self.assertEqual(summary["robustness_pass_candidate_count"], 0)
        self.assertFalse(summary["oos_alternates_count_as_gatekeeper_relief"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertIn(
            "bithumb_current_actionable_alternate_robustness_failure_status: "
            "`BITHUMB_ALTERNATE_ROBUSTNESS_FAILURE_REVIEW_READY`",
            rendered,
        )
        self.assertIn("bithumb_current_actionable_alternate_robustness_failure_robustness_pass: `0`", rendered)

    def test_bithumb_current_actionable_orca_robustness_repair_is_visible_and_no_order(self) -> None:
        repair = {
            "status": "ORCA_ROBUSTNESS_REPAIR_ITERATE",
            "base_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
            "parent_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001",
            "market": "KRW-ORCA",
            "trial_count": 3888,
            "evaluated_robustness_count": 24,
            "oos_pass_candidate_count": 24,
            "robustness_pass_candidate_count": 0,
            "best_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_orcarepair_2392",
            "best_candidate_status": "OOS_CANDIDATE_PASS",
            "best_robustness_status": "ROBUSTNESS_STRESS_ITERATE",
            "blockers": ["NO_ORCA_ROBUSTNESS_REPAIR_PASS"],
            "candidate_results": [
                {
                    "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_orcarepair_2392",
                    "market": "KRW-ORCA",
                    "status": "OOS_CANDIDATE_PASS",
                    "aggregate": {"pass_fold_count": 2, "fold_count": 3, "total_trade_count": 12},
                    "robustness": {"status": "ROBUSTNESS_STRESS_ITERATE", "pass_count": 0, "cost_pass_count": 0},
                }
            ],
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_current_actionable_orca_robustness_repair=repair,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["bithumb_current_actionable_orca_robustness_repair"]
        self.assertFalse(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["trial_count"], 3888)
        self.assertEqual(summary["evaluated_robustness_count"], 24)
        self.assertEqual(summary["oos_pass_candidate_count"], 24)
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertIn(
            "bithumb_current_actionable_orca_robustness_repair_status: `ORCA_ROBUSTNESS_REPAIR_ITERATE`",
            rendered,
        )
        self.assertIn("bithumb_current_actionable_orca_robustness_repair_trial_count: `3888`", rendered)
        self.assertIn("bithumb_current_actionable_orca_robustness_repair_evaluated_count: `24`", rendered)

    def test_bithumb_current_actionable_family_diversity_is_visible_and_no_order(self) -> None:
        diversity = {
            "status": "FAMILY_DIVERSITY_OOS_PASS",
            "evaluated_candidate_count": 3,
            "oos_pass_candidate_count": 1,
            "robustness_pass_candidate_count": 0,
            "best_candidate_id": "bithumb_current_actionable_virtual_1d_long_freeze001",
            "best_candidate_market": "KRW-VIRTUAL",
            "candidate_results": [
                {
                    "candidate_id": "bithumb_current_actionable_virtual_1d_long_freeze001",
                    "market": "KRW-VIRTUAL",
                    "status": "OOS_CANDIDATE_PASS",
                    "aggregate": {"pass_fold_count": 2, "fold_count": 3, "total_trade_count": 7},
                    "robustness": {"status": "ROBUSTNESS_STRESS_ITERATE", "pass_count": 1, "cost_pass_count": 0},
                }
            ],
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_current_actionable_family_diversity=diversity,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["bithumb_current_actionable_family_diversity_review"]
        self.assertFalse(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["evaluated_candidate_count"], 3)
        self.assertEqual(summary["oos_pass_candidate_count"], 1)
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertIn("bithumb_current_actionable_family_diversity_status: `FAMILY_DIVERSITY_OOS_PASS`", rendered)
        self.assertIn("bithumb_current_actionable_family_diversity_oos_pass_count: `1`", rendered)

    def test_bithumb_current_actionable_family_diversity_failure_is_visible_and_no_order(self) -> None:
        failure = {
            "status": "FAMILY_DIVERSITY_FAILURE_REVIEW_READY",
            "family_diversity_status": "FAMILY_DIVERSITY_ITERATE",
            "current_oos_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
            "current_oos_market": "KRW-ORCA",
            "evaluated_candidate_count": 2,
            "failure_candidate_count": 2,
            "dominant_failure_dimension": "enough_pass_folds",
            "failure_dimension_counts": {"enough_pass_folds": 2, "enough_positive_folds": 2},
            "recommended_research_action": "REPAIR_NON_ORCA_PASS_FOLD_COVERAGE",
            "candidate_gaps": [{"candidate_id": "pola", "market": "KRW-POLA"}],
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_current_actionable_family_diversity_failure=failure,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["bithumb_current_actionable_family_diversity_failure_review"]
        self.assertTrue(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["failure_candidate_count"], 2)
        self.assertEqual(summary["dominant_failure_dimension"], "enough_pass_folds")
        self.assertEqual(summary["recommended_research_action"], "REPAIR_NON_ORCA_PASS_FOLD_COVERAGE")
        self.assertFalse(summary["counts_as_paper_or_live_evidence"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertIn(
            "bithumb_current_actionable_family_diversity_failure_status: `FAMILY_DIVERSITY_FAILURE_REVIEW_READY`",
            rendered,
        )
        self.assertIn(
            "bithumb_current_actionable_family_diversity_failure_action: `REPAIR_NON_ORCA_PASS_FOLD_COVERAGE`",
            rendered,
        )

    def test_bithumb_non_orca_family_pass_fold_repair_spec_is_visible_and_no_order(self) -> None:
        repair_spec = {
            "status": "READY_FOR_RESEARCH_SPEC_REVIEW",
            "experiment_id": "bithumb_non_orca_family_pass_fold_repair__orca",
            "source_decision_id": "bithumb_current_actionable_family_diversity_failure_review",
            "queue_rank": 13,
            "dominant_failure_dimension": "enough_pass_folds",
            "recommended_research_action": "REPAIR_NON_ORCA_PASS_FOLD_COVERAGE",
            "repair_target_count": 2,
            "repair_targets": [{"candidate_id": "pola"}, {"candidate_id": "bio"}],
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_non_orca_family_pass_fold_repair_spec=repair_spec,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["bithumb_non_orca_family_pass_fold_repair_spec"]
        self.assertTrue(summary["ready_for_research_spec_review"])
        self.assertEqual(summary["repair_target_count"], 2)
        self.assertEqual(summary["recommended_research_action"], "REPAIR_NON_ORCA_PASS_FOLD_COVERAGE")
        self.assertFalse(summary["counts_as_paper_or_live_evidence"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertIn(
            "bithumb_non_orca_family_pass_fold_repair_spec_status: `READY_FOR_RESEARCH_SPEC_REVIEW`",
            rendered,
        )
        self.assertIn("bithumb_non_orca_family_pass_fold_repair_spec_targets: `2`", rendered)

    def test_bithumb_current_actionable_family_parameter_repair_is_visible_and_no_order(self) -> None:
        repair = {
            "status": "FAMILY_PARAMETER_REPAIR_OOS_PASS",
            "seed_candidate_count": 3,
            "evaluated_trial_count": 15,
            "oos_pass_candidate_count": 2,
            "robustness_pass_candidate_count": 0,
            "best_candidate_id": "bithumb_current_actionable_virtual_1d_long_freeze001_sweep0001",
            "best_candidate_market": "KRW-VIRTUAL",
            "candidate_results": [
                {
                    "candidate_id": "bithumb_current_actionable_virtual_1d_long_freeze001_sweep0001",
                    "market": "KRW-VIRTUAL",
                    "status": "OOS_CANDIDATE_PASS",
                    "aggregate": {"pass_fold_count": 2, "fold_count": 3, "total_trade_count": 9},
                    "robustness": {"status": "ROBUSTNESS_STRESS_ITERATE", "pass_count": 1, "cost_pass_count": 0},
                }
            ],
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_current_actionable_family_parameter_repair=repair,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["bithumb_current_actionable_family_parameter_repair_review"]
        self.assertFalse(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["seed_candidate_count"], 3)
        self.assertEqual(summary["evaluated_trial_count"], 15)
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertIn(
            "bithumb_current_actionable_family_parameter_repair_status: `FAMILY_PARAMETER_REPAIR_OOS_PASS`",
            rendered,
        )
        self.assertIn("bithumb_current_actionable_family_parameter_repair_evaluated_count: `15`", rendered)

    def test_bithumb_current_actionable_family_parameter_repair_packet_is_visible_and_no_order(self) -> None:
        packet_source = {
            "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
            "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
            "evidence_summary": {
                "market": "KRW-POLA",
                "oos_fold_count": 3,
                "oos_pass_fold_count": 2,
                "oos_total_trade_count": 17,
                "robustness_case_count": 7,
                "robustness_pass_count": 4,
                "robustness_cost_pass_count": 2,
            },
            "blockers": [],
            "no_order_assertions": {
                "promotion_allowed_by_this_packet": False,
                "shadow_registration_allowed_by_this_packet": False,
                "paper_enabled_by_this_packet": False,
                "live_allowed_by_this_packet": False,
                "broker_submit_allowed_by_this_packet": False,
                "private_submit_allowed_by_this_packet": False,
                "real_orders_allowed_by_this_packet": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_current_actionable_family_parameter_repair_packet=packet_source,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["bithumb_current_actionable_family_parameter_repair_gatekeeper_packet"]
        self.assertTrue(summary["ready_for_human_gatekeeper_review"])
        self.assertFalse(summary["shadow_registration_allowed_by_this_report"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertIn(
            "bithumb_current_actionable_family_parameter_repair_packet_status: `READY_FOR_HUMAN_GATEKEEPER_REVIEW`",
            rendered,
        )
        self.assertIn("bithumb_current_actionable_family_parameter_repair_packet_robustness: `4/7`", rendered)

    def test_stock_conversion_robustness_top5_coverage_is_visible(self) -> None:
        stress = {
            "status": "ROBUSTNESS_STRESS_PASS",
            "candidate_id": "stock_aggressive_trim22",
            "case_count": 7,
            "pass_count": 5,
            "mdd_stress_pass_count": 1,
            "queue_coverage": {
                "covered_candidate_count": 5,
                "stress_pass_candidate_count": 5,
                "all_covered_candidates_safe": True,
                "top5_full_coverage": True,
            },
            "candidate_results": [
                {
                    "candidate_id": "stock_aggressive_trim22",
                    "lane": "kis_etfs",
                    "status": "ROBUSTNESS_STRESS_PASS",
                    "case_count": 7,
                    "pass_count": 5,
                    "mdd_stress_pass_count": 1,
                    "queue_order_paths_safe": True,
                }
            ],
            "no_order_assertions": {
                "promotion_allowed_by_this_report": False,
                "paper_enabled_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            stock_conversion_robustness=stress,
            stock_conversion_sizing_repair={
                "status": "SIZING_REPAIR_READY",
                "evaluated_iterate_candidate_count": 2,
                "repair_ready_count": 2,
                "repairs": [
                    {
                        "candidate_id": "stock_aggressive_trim_repair",
                        "lane": "kis_stocks",
                        "repair_status": "SIZING_REPAIR_READY",
                        "current_fixed_exposure_cap": 0.59,
                        "recommended_conversion": {
                            "overlay": "fixed_exposure_055",
                            "fixed_exposure_cap": 0.55,
                            "stress": {"pass_count": 4},
                        },
                    }
                ],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            stock_conversion_repaired_robustness={
                "status": "REPAIRED_ROBUSTNESS_STRESS_PASS",
                "queue_coverage": {
                    "covered_candidate_count": 5,
                    "stress_pass_candidate_count": 5,
                    "repaired_candidate_count": 2,
                    "all_covered_candidates_safe": True,
                    "top5_full_coverage": True,
                },
                "candidate_results": [
                    {
                        "candidate_id": "stock_aggressive_trim_repair",
                        "lane": "kis_stocks",
                        "status": "ROBUSTNESS_STRESS_PASS",
                        "overlay": "fixed_exposure_055",
                        "fixed_exposure_cap": 0.55,
                        "pass_count": 4,
                        "mdd_stress_pass_count": 2,
                        "repair_applied": True,
                        "queue_order_paths_safe": True,
                    }
                ],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["stock_conversion_robustness_stress"]
        self.assertTrue(summary["ready_for_gatekeeper_review"])
        self.assertEqual(summary["queue_coverage"]["covered_candidate_count"], 5)
        self.assertEqual(summary["candidate_results"][0]["candidate_id"], "stock_aggressive_trim22")
        self.assertEqual(packet["stock_conversion_sizing_repair"]["repair_ready_count"], 2)
        self.assertTrue(packet["stock_conversion_repaired_robustness_stress"]["ready_for_gatekeeper_review"])
        self.assertEqual(
            packet["stock_conversion_repaired_robustness_stress"]["queue_coverage"]["stress_pass_candidate_count"],
            5,
        )
        self.assertIn("queue_covered_candidate_count: `5`", rendered)
        self.assertIn("Stock Conversion Robustness Top 5 Queue Coverage", rendered)
        self.assertIn("Stock Conversion Sizing Repair", rendered)
        self.assertIn("Stock Conversion Repaired Robustness Stress", rendered)
        self.assertIn("repair_ready_count: `2`", rendered)

    def test_bithumb_current_actionable_gatekeeper_and_preflight_are_report_only(self) -> None:
        packet_source = {
            "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
            "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
            "blockers": [],
            "no_order_assertions": {
                "promotion_allowed_by_this_packet": False,
                "shadow_enabled_by_this_packet": False,
                "paper_enabled_by_this_packet": False,
                "live_allowed_by_this_packet": False,
                "broker_submit_allowed_by_this_packet": False,
                "private_submit_allowed_by_this_packet": False,
                "real_orders_allowed_by_this_packet": False,
            },
        }
        preflight = {
            "status": "BLOCKED_PENDING_HUMAN_GATEKEEPER_DECISION",
            "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
            "blockers": ["HUMAN_GATEKEEPER_SHADOW_DECISION_MISSING"],
            "safety": {
                "does_register_shadow_candidate": False,
                "does_start_shadow_loop": False,
                "does_enable_paper": False,
                "does_enable_live": False,
                "broker_submit_allowed": False,
                "private_submit_allowed": False,
                "real_orders_allowed": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_current_actionable_gatekeeper_packet=packet_source,
            bithumb_current_actionable_shadow_preflight=preflight,
            bithumb_current_actionable_shadow_decision_template={
                "status": "PENDING_HUMAN_GATEKEEPER_DECISION",
                "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001",
                "blockers": ["HUMAN_GATEKEEPER_SHADOW_DECISION_MISSING"],
                "human_decision": {
                    "present": False,
                    "valid": False,
                    "decision_recorded": False,
                },
                "approved_for_separate_shadow_registration_review": False,
                "safety": {
                    "does_register_shadow_candidate": False,
                    "does_start_shadow_loop": False,
                    "does_enable_paper": False,
                    "does_enable_live": False,
                    "broker_submit_allowed": False,
                    "private_submit_allowed": False,
                    "real_orders_allowed": False,
                },
            },
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        review = packet["bithumb_current_actionable_gatekeeper_review_packet"]
        shadow = packet["bithumb_current_actionable_shadow_preflight"]
        decision = packet["bithumb_current_actionable_shadow_decision_template"]
        self.assertTrue(review["ready_for_human_gatekeeper_review"])
        self.assertFalse(review["shadow_enabled_by_this_report"])
        self.assertFalse(review["real_orders_allowed_by_this_report"])
        self.assertFalse(shadow["ready_for_shadow_registration"])
        self.assertFalse(shadow["does_register_shadow_candidate"])
        self.assertFalse(shadow["does_start_shadow_loop"])
        self.assertFalse(decision["decision_recorded"])
        self.assertFalse(decision["approved_for_separate_shadow_registration_review"])
        self.assertFalse(decision["does_register_shadow_candidate"])
        self.assertFalse(decision["does_start_shadow_loop"])
        self.assertFalse(decision["broker_submit_allowed_by_this_report"])
        self.assertFalse(decision["real_orders_allowed_by_this_report"])
        self.assertIn("bithumb_current_actionable_gatekeeper_packet_review_ready: `True`", rendered)
        self.assertIn("bithumb_current_actionable_shadow_preflight_registers_candidate: `False`", rendered)
        self.assertIn("bithumb_current_actionable_shadow_decision_template_status: `PENDING_HUMAN_GATEKEEPER_DECISION`", rendered)

    def test_gatekeeper_review_decision_phrase_packet_surfaces_exact_phrase(self) -> None:
        phrase_packet = {
            "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
            "ready_phrase_count": 6,
            "blocked_decision_count": 1,
            "next_phrase": {
                "decision_id": "paper_smoke_review",
                "candidate_id": "small_account_growth_paper",
                "exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
            },
            "ready_phrases": [
                {
                    "decision_id": "bithumb_current_actionable_shadow_review",
                    "status": "INVALID_HUMAN_GATEKEEPER_DECISION",
                    "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                    "human_decision_state": {
                        "expected_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                        "recorded_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354",
                        "decision_candidate_match": False,
                    },
                }
            ],
            "board_permissions": {
                "promotion_allowed_by_this_packet": False,
                "shadow_registration_allowed_by_this_packet": False,
                "paper_enabled_by_this_packet": False,
                "live_allowed_by_this_packet": False,
                "broker_submit_allowed_by_this_packet": False,
                "private_submit_allowed_by_this_packet": False,
                "real_orders_allowed_by_this_packet": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            gatekeeper_review_decision_phrase_packet=phrase_packet,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["gatekeeper_review_decision_phrase_packet"]
        self.assertTrue(summary["ready_for_human_gatekeeper_review"])
        self.assertEqual(summary["next_exact_phrase_to_record"], "REVIEW_PAPER_SMOKE_ONLY")
        self.assertEqual(summary["bithumb_shadow_decision_status"], "INVALID_HUMAN_GATEKEEPER_DECISION")
        self.assertEqual(
            summary["bithumb_shadow_expected_candidate_id"],
            "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
        )
        self.assertEqual(
            summary["bithumb_shadow_recorded_candidate_id"],
            "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354",
        )
        self.assertFalse(summary["bithumb_shadow_decision_candidate_match"])
        self.assertFalse(summary["broker_submit_allowed_by_this_packet"])
        self.assertFalse(summary["real_orders_allowed_by_this_packet"])
        self.assertIn("gatekeeper_review_next_exact_phrase: `REVIEW_PAPER_SMOKE_ONLY`", rendered)
        self.assertIn("gatekeeper_review_bithumb_shadow_candidate_match: `False`", rendered)

    def test_bithumb_dependency_relief_packet_surfaces_review_only(self) -> None:
        relief_packet = {
            "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
            "exact_phrase_to_record": "REVIEW_DEPENDENCY_RELIEF_EVIDENCE_ONLY",
            "dependency_relief_candidate": {
                "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                "estimated_cagr": 0.88,
                "estimated_mdd": -0.2,
                "robustness_status": "ROBUSTNESS_STRESS_PASS",
            },
            "dependency_relief_summary": {
                "registered_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354",
                "latest_oos_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                "relief_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                "sweep1354_dependency_reduced_by_review_evidence": True,
                "relief_candidate_is_registered_candidate": False,
                "relief_candidate_is_latest_oos_candidate": False,
            },
            "no_order_assertions": {
                "promotion_allowed_by_this_packet": False,
                "shadow_registration_allowed_by_this_packet": False,
                "paper_enabled_by_this_packet": False,
                "live_allowed_by_this_packet": False,
                "broker_submit_allowed_by_this_packet": False,
                "private_submit_allowed_by_this_packet": False,
                "real_orders_allowed_by_this_packet": False,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            bithumb_current_actionable_dependency_relief_packet=relief_packet,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["bithumb_current_actionable_dependency_relief_packet"]
        self.assertTrue(summary["ready_for_human_gatekeeper_review"])
        self.assertEqual(summary["registered_candidate_id"], "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354")
        self.assertEqual(summary["relief_candidate_id"], "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355")
        self.assertTrue(summary["sweep1354_dependency_reduced_by_review_evidence"])
        self.assertFalse(summary["shadow_registration_allowed_by_this_report"])
        self.assertFalse(summary["broker_submit_allowed_by_this_report"])
        self.assertFalse(summary["real_orders_allowed_by_this_report"])
        self.assertIn("bithumb_current_actionable_dependency_relief_status: `READY_FOR_HUMAN_GATEKEEPER_REVIEW`", rendered)
        self.assertIn("bithumb_current_actionable_dependency_relief_reduces_sweep1354_dependency: `True`", rendered)

    def test_goal_unblock_verification_packet_surfaces_blockers_and_safe_replay_policy(self) -> None:
        unblock_packet = {
            "status": "WAITING_FOR_BLOCKER_CLEARANCE",
            "blocker_count": 2,
            "blocker_deliverables": [
                "current_paper_activation_gate",
                "two_axis_model_factory_scope",
            ],
            "unblock_summary": {
                "kis_operator_input_required": True,
                "kis_missing_requirements": [
                    "app_key",
                    "app_secret",
                    "account_no",
                    "account_product_code",
                ],
                "kis_api_environment_ready": False,
                "kis_local_coverage_ready": True,
                "paper_cycles_completed": 252,
                "paper_cycles_target": 288,
                "paper_cycles_missing": 36,
                "non_flat_signal_count": 53,
                "non_flat_signal_target": 5,
                "non_flat_signals_ready": True,
                "executable_order_count": 53,
                "executable_order_target": 5,
                "executable_orders_ready": True,
                "promotion_review_ready": False,
                "historical_replay_counts_as_promotion_evidence": False,
                "historical_replay_excluded": True,
            },
            "verification_steps": [
                {"blocker": "two_axis_model_factory_scope"},
                {"blocker": "current_paper_activation_gate"},
            ],
            "completion_recheck_commands": ["python .\\build_goal_model_factory_requirement_checklist.py"],
            "safety": {
                "does_enable_paper": False,
                "does_enable_live": False,
                "broker_submit_allowed_by_this_packet": False,
                "private_submit_allowed_by_this_packet": False,
                "real_orders_allowed_by_this_packet": False,
                "real_orders": 0,
            },
        }

        packet = board.gatekeeper_action_packet(
            evidence_rows=[],
            repairs=[],
            paper_evidence={},
            capital_allocator={},
            goal_unblock_verification_packet=unblock_packet,
        )
        rendered = board.render_markdown(
            {
                "generated_at_utc": "2026-05-03T00:00:00+00:00",
                "status": "PASS",
                "scope": "decision_support_no_candidate_state_side_effects",
                "next_action": "test",
                "model_factory_metrics": {},
                "candidate_funnel_by_lane": [],
                "candidate_priority": [],
                "paper_evidence_velocity_targets": [],
                "failure_reason_distribution": [],
                "repair_queue": [],
                "paper_shadow_evidence_queue": [],
                "gatekeeper_action_packet": packet,
                "anchor_challenger_matrix": [],
                "gate_counts_by_lane": {},
                "paper_evidence_decision": {"decision": "KEEP_PAPER_COLLECT_EVIDENCE", "evidence_gaps": []},
                "capital_allocator_decision": {"decision": "KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE"},
            }
        )

        summary = packet["goal_model_factory_unblock_verification_packet"]
        self.assertEqual(summary["status"], "WAITING_FOR_BLOCKER_CLEARANCE")
        self.assertEqual(summary["paper_cycles_completed"], 252)
        self.assertEqual(summary["paper_cycles_target"], 288)
        self.assertEqual(summary["non_flat_signal_count"], 53)
        self.assertEqual(summary["executable_order_count"], 53)
        self.assertFalse(summary["historical_replay_counts_as_promotion_evidence"])
        self.assertFalse(summary["broker_submit_allowed_by_this_packet"])
        self.assertFalse(summary["real_orders_allowed_by_this_packet"])
        self.assertTrue(summary["surface_safe"])
        self.assertIn("goal_unblock_packet_status: `WAITING_FOR_BLOCKER_CLEARANCE`", rendered)
        self.assertIn("goal_unblock_paper_cycles: `252/288`", rendered)
        self.assertIn("goal_unblock_replay_counts_as_promotion: `False`", rendered)


if __name__ == "__main__":
    unittest.main()
