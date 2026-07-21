from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bridge_paper_safety_triage_review.py")
SPEC = importlib.util.spec_from_file_location("build_bridge_paper_safety_triage_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class BridgePaperSafetyTriageReviewTests(unittest.TestCase):
    def pull_through(self) -> dict:
        return {
            "repair_queue": [
                {
                    "candidate_id": "bridge_28_relief",
                    "current_gate": "G08_LOCAL_SIM_PAPER",
                    "status": "LOCAL_SIM_PAPER_FAILED",
                    "failure_reason": "SIM_SAFETY_VIOLATION",
                    "cagr": 0.35,
                    "mdd": -0.09,
                    "sharpe": 1.86,
                }
            ]
        }

    def paper_autotrade(self) -> dict:
        return {
            "mode": "paper_autotrade_active_simulated",
            "status": "pass",
            "profile": "small_account_growth_paper",
            "broker_submit_scope": "paper_only",
            "live_enabled_flag": False,
            "real_orders": 0,
            "private_submit_used": False,
            "targets": [
                {
                    "symbol": "KRW-BTC",
                    "variant": "bridge_28_relief",
                    "signal_side": "flat",
                    "target_account_weight": 0.0,
                }
            ],
            "simulated_orders": [
                {
                    "variant": "bridge_28_relief",
                    "action": "HOLD",
                    "delta_weight": 0.0,
                    "real_order_submitted": False,
                    "broker_submit_allowed": False,
                }
            ],
        }

    def firewall(self) -> dict:
        return {
            "bridge_firewall_row_count": 2,
            "allow_paper_only_count": 1,
            "reject_count": 1,
            "limited_live_reject_count": 1,
            "historical_replay_reject_count": 1,
            "rejection_reason_counts": {"LIMITED_LIVE_DISABLED": 1, "HISTORICAL_REPLAY_REJECTED": 1},
        }

    def test_builds_ready_bridge_safety_triage_without_order_paths(self) -> None:
        report = review.build_report(self.pull_through(), self.paper_autotrade(), self.firewall())

        self.assertEqual(report["status"], "BRIDGE_PAPER_SAFETY_TRIAGE_REVIEW_READY")
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertTrue(report["review_conclusion"]["candidate_remains_failed_for_promotion"])
        self.assertTrue(report["review_conclusion"]["paper_loop_hard_safety_clean"])
        self.assertTrue(report["review_conclusion"]["current_bridge_order_is_hold_zero_delta"])
        self.assertTrue(report["review_conclusion"]["firewall_observed_blocking_disallowed_paths"])
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_when_paper_autotrade_hard_safety_is_unsafe(self) -> None:
        paper = self.paper_autotrade()
        paper["live_enabled_flag"] = True

        report = review.build_report(self.pull_through(), paper, self.firewall())

        self.assertEqual(report["status"], "BRIDGE_PAPER_SAFETY_TRIAGE_REVIEW_BLOCKED")
        self.assertIn("PAPER_AUTOTRADE_HARD_SAFETY_NOT_CLEAN", report["blockers"])
        self.assertFalse(report["ready_for_gatekeeper_review"])

    def test_parses_bridge_firewall_markdown_rows(self) -> None:
        rows = review.parse_firewall_rows(
            "\n".join(
                [
                    "| `id1` | `bridge_28_relief` | `broker_paper` | `KRW-BTC` | `10000` | `REJECT` | `PAPER_APPROVAL_EXPIRED` | `h` | `small_account_growth_paper` | `r` |",
                    "| `id2` | `other` | `broker_paper` | `KRW-BTC` | `10000` | `REJECT` | `x` | `h` | `p` | `r` |",
                    "| `id3` | `bridge_28_relief` | `broker_paper` | `KRW-BTC` | `10000` | `ALLOW_PAPER_ONLY` | `` | `h` | `small_account_growth_paper` | `r` |",
                ]
            )
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["rejection_reason"], "PAPER_APPROVAL_EXPIRED")
        self.assertEqual(rows[1]["decision"], "ALLOW_PAPER_ONLY")


if __name__ == "__main__":
    unittest.main()
