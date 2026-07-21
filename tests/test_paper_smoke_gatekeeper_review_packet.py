from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_paper_smoke_gatekeeper_review_packet.py")
SPEC = importlib.util.spec_from_file_location("build_paper_smoke_gatekeeper_review_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
packet = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet)


def ready_inputs() -> tuple[dict, dict, dict, dict, dict, dict]:
    taxonomy = {
        "status": "PASS",
        "taxonomy": {
            "paper_smoke_evidence": {
                "ready": True,
                "paper_cycles_completed": 175,
                "minimum_cycles": 24,
            },
            "extended_paper_evidence": {
                "ready": False,
                "decision": "KEEP_PAPER_COLLECT_EVIDENCE",
                "evidence_gaps": ["INSUFFICIENT_NON_FLAT_SIGNAL_EVIDENCE"],
            },
        },
        "safety": {
            "historical_replay_counts_as_paper_smoke": False,
            "historical_replay_counts_as_accelerated_shadow": True,
        },
    }
    paper = {
        "candidate_profile": "small_account_growth_paper",
        "replay_policy": {
            "historical_replay_counts_as_promotion_evidence": False,
            "historical_replay_non_flat_count_excluded": 197,
        },
        "evidence": {
            "paper_safety": {
                "broker_submit_allowed": True,
                "broker_submit_scope": "paper_only",
                "live_enabled_flag": False,
                "private_submit_used": False,
                "real_orders": 0,
            },
            "combined_evidence": {
                "combined_non_flat_signal_count": 2,
                "combined_executable_order_evidence_count": 2,
            },
        },
    }
    acceleration = {
        "safety": {
            "broker_submit_allowed": False,
            "live_enabled": False,
        },
        "multi_asset_1d_signals": [
            {
                "market": "KRW-BIO",
                "timeframe": "1d",
                "side": "long",
                "target_weight": 0.02,
                "latest_timestamp": "2026-05-02T15:00:00",
                "signal_id": "sig-bio",
                "counts_as_live_paper_evidence": True,
                "broker_submit_allowed": False,
            }
        ],
        "intraday_1h_4h_signals": [],
        "virtual_orders": [
            {
                "market": "KRW-BIO",
                "timeframe": "1d",
                "action": "BUY",
                "target_weight": 0.02,
                "signal_id": "sig-bio",
                "counts_as_live_paper_evidence": True,
                "broker_submit_allowed": False,
            }
        ],
        "historical_replay": {
            "counts_as_live_paper_evidence": False,
        },
    }
    risk_guard = {"status": "PASS", "halt_count": 0}
    safety_self_test = {
        "duplicate_idempotency_passed": True,
        "first_order_intent_ids": ["intent-1"],
        "second_order_intent_ids": ["intent-1"],
    }
    paper_autotrade = {
        "profile": "small_account_growth_paper",
        "simulated_orders": [
            {
                "action": "HOLD",
                "real_order_submitted": False,
                "broker_submit_allowed": False,
                "broker_submit_scope": "paper_only",
            }
        ],
    }
    return taxonomy, paper, acceleration, risk_guard, safety_self_test, paper_autotrade


class PaperSmokeGatekeeperReviewPacketTests(unittest.TestCase):
    def test_packet_is_ready_for_paper_smoke_without_extended_paper_5_of_5(self) -> None:
        report = packet.build_packet(*ready_inputs())

        self.assertEqual(report["status"], "READY_FOR_GATEKEEPER_REVIEW")
        self.assertTrue(report["review_ready"])
        self.assertFalse(report["permissions"]["promotion_allowed_by_this_packet"])
        self.assertFalse(report["permissions"]["extended_paper_promotion_allowed_by_this_packet"])
        self.assertFalse(report["permissions"]["live_allowed_by_this_packet"])
        self.assertFalse(report["permissions"]["real_orders_allowed_by_this_packet"])
        self.assertEqual(report["permissions"]["broker_submit_scope_required"], "paper_only")
        self.assertFalse(report["evidence_summary"]["extended_paper_ready"])
        self.assertEqual(report["blockers"], [])
        self.assertTrue(report["review_checks"]["risk_guard_hard_safety_ok"])
        self.assertTrue(report["review_checks"]["dedup_idempotency_ok"])
        self.assertTrue(report["review_checks"]["historical_replay_only_accelerated_shadow"])

    def test_packet_allows_review_when_risk_guard_warn_is_loop_freshness_only(self) -> None:
        taxonomy, paper, acceleration, risk_guard, safety_self_test, paper_autotrade = ready_inputs()
        risk_guard = {
            "status": "WARN",
            "halt_count": 0,
            "warn_count": 1,
            "checks": [
                {"name": "live_disabled", "status": "PASS", "observed": False},
                {"name": "private_submit_unused", "status": "PASS", "observed": False},
                {"name": "real_orders_zero", "status": "PASS", "observed": 0},
                {
                    "name": "broker_submit_scope",
                    "status": "PASS",
                    "observed": {"broker_submit_allowed": True, "broker_submit_scope": "paper_only"},
                },
                {"name": "paper_loop", "status": "WARN", "reason": "stale"},
            ],
        }

        report = packet.build_packet(taxonomy, paper, acceleration, risk_guard, safety_self_test, paper_autotrade)

        self.assertEqual(report["status"], "READY_FOR_GATEKEEPER_REVIEW")
        self.assertTrue(report["review_ready"])
        self.assertTrue(report["review_checks"]["risk_guard_hard_safety_ok"])
        self.assertNotIn("risk_guard_hard_safety_ok", report["blockers"])

    def test_packet_blocks_when_risk_guard_warn_contains_hard_safety_failure(self) -> None:
        taxonomy, paper, acceleration, risk_guard, safety_self_test, paper_autotrade = ready_inputs()
        risk_guard = {
            "status": "WARN",
            "halt_count": 0,
            "checks": [
                {"name": "live_disabled", "status": "FAIL", "observed": True},
                {"name": "private_submit_unused", "status": "PASS", "observed": False},
                {"name": "real_orders_zero", "status": "PASS", "observed": 0},
            ],
        }

        report = packet.build_packet(taxonomy, paper, acceleration, risk_guard, safety_self_test, paper_autotrade)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["review_ready"])
        self.assertIn("risk_guard_hard_safety_ok", report["blockers"])

    def test_packet_blocks_if_historical_replay_is_marked_as_promotion_evidence(self) -> None:
        taxonomy, paper, acceleration, risk_guard, safety_self_test, paper_autotrade = ready_inputs()
        paper["replay_policy"]["historical_replay_counts_as_promotion_evidence"] = True

        report = packet.build_packet(taxonomy, paper, acceleration, risk_guard, safety_self_test, paper_autotrade)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["review_ready"])
        self.assertIn("historical_replay_not_promotion", report["blockers"])

    def test_packet_blocks_if_dedup_idempotency_fails(self) -> None:
        taxonomy, paper, acceleration, risk_guard, safety_self_test, paper_autotrade = ready_inputs()
        safety_self_test["second_order_intent_ids"] = ["different-intent"]

        report = packet.build_packet(taxonomy, paper, acceleration, risk_guard, safety_self_test, paper_autotrade)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["review_ready"])
        self.assertIn("dedup_idempotency_ok", report["blockers"])


if __name__ == "__main__":
    unittest.main()
