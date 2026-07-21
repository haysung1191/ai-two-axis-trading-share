from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\ops\limited_live_entry\limited_live_entry_closure_loop.py")
SPEC = importlib.util.spec_from_file_location("limited_live_entry_closure_loop", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
closure = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = closure
SPEC.loader.exec_module(closure)


class LimitedLiveEntryClosureLoopTests(unittest.TestCase):
    def test_oos_audit_blocks_registered_candidate_without_exact_params(self) -> None:
        audit = closure.build_oos_audit(
            {"records": [{"candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354", "market": "KRW-POLA", "timeframe": "1d"}]},
            {"top_oos": {"candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep2118", "market": "KRW-ORCA", "timeframe": "1d", "parameters": {"lookback_bars": 3}}},
        )

        self.assertEqual(audit["status"], "BLOCKED")
        self.assertEqual(audit["blocked_count"], 1)
        self.assertIn("OOS_PARAMETERS_NOT_FOUND_FOR_REGISTERED_CANDIDATE", audit["blockers"])

    def test_oos_audit_passes_exact_registered_params(self) -> None:
        audit = closure.build_oos_audit(
            {"records": [{"candidate_id": "c1", "market": "KRW-BTC", "timeframe": "1d"}]},
            {"evaluations": [{"candidate_id": "c1", "market": "KRW-BTC", "timeframe": "1d", "parameters": {"lookback_bars": 3}}]},
        )

        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["eligible_count"], 1)

    def test_oos_audit_excludes_disqualified_candidate_without_blocking_closure(self) -> None:
        audit = closure.build_oos_audit(
            {"records": [{"candidate_id": "stale_pola", "market": "KRW-POLA", "timeframe": "1d"}]},
            {"top_oos": {"candidate_id": "latest_orca", "market": "KRW-ORCA", "timeframe": "1d", "parameters": {"lookback_bars": 3}}},
            {"disqualified_candidates": [{"candidate_id": "stale_pola", "reason": "rolled_to_latest_oos_candidate"}]},
        )

        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["eligible_count"], 0)
        self.assertEqual(audit["excluded_count"], 1)
        self.assertEqual(audit["blockers"], [])

    def test_decision_prioritizes_risk_guard_before_signal(self) -> None:
        state, blockers = closure.decide(
            {"status": "WARN"},
            {"status": "PASS"},
            {"status": "WAITING_FOR_CURRENT_NONZERO_SIGNAL", "blockers": ["CURRENT_CRYPTO_SIGNAL_HAS_NO_NONZERO_ORDER"]},
            {"status": "READY", "blockers": []},
            {"status": "PASS"},
        )

        self.assertEqual(state, "BLOCKED_RISK_GUARD_NOT_PASS")
        self.assertEqual(blockers, ["RISK_GUARD_NOT_PASS"])

    def test_decision_ready_only_when_all_core_checks_pass(self) -> None:
        state, blockers = closure.decide(
            {"status": "PASS"},
            {"status": "PASS"},
            {"status": "READY", "blockers": []},
            {"status": "BLOCKED_NO_CAP_COMPLIANT_ROUTE", "blockers": ["NO_CAP_COMPLIANT_ROUTE"]},
            {"status": "PASS"},
        )

        self.assertEqual(state, "READY_FOR_LIMITED_LIVE_ARM_REVIEW")
        self.assertEqual(blockers, [])

    def test_safety_snapshot_blocks_unsafe_submit_scope(self) -> None:
        safety = closure.safety_snapshot(
            {"live_enabled": False, "paper_enabled": False},
            {"broker_submit_allowed": True, "broker_submit_scope": "live", "private_submit_used": False, "real_orders": 0},
        )

        self.assertEqual(safety["status"], "BLOCKED")
        self.assertIn("BROKER_SUBMIT_SCOPE_NOT_SAFE", safety["blockers"])


if __name__ == "__main__":
    unittest.main()
