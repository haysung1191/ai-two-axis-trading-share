from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_gatekeeper_evidence_taxonomy.py")
SPEC = importlib.util.spec_from_file_location("build_gatekeeper_evidence_taxonomy", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
taxonomy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(taxonomy)


class GatekeeperEvidenceTaxonomyTests(unittest.TestCase):
    def ready_inputs(self) -> tuple[dict, dict, dict]:
        paper = {
            "decision": "KEEP_PAPER_COLLECT_EVIDENCE",
            "evidence_gaps": ["INSUFFICIENT_PAPER_CYCLES"],
            "evidence": {
                "paper_cycles_completed": 252,
                "combined_evidence": {
                    "combined_non_flat_signal_count": 53,
                    "combined_executable_order_evidence_count": 53,
                },
            },
        }
        acceleration = {
            "summary": {"eligible_live_paper_signal_count": 410},
            "historical_replay": {"non_flat_count": 7621, "counts_as_live_paper_evidence": False},
        }
        progress = {"current": {"paper_cycles_completed": 252}, "event_stall_summary": {}}
        return paper, acceleration, progress

    def test_warn_from_loop_freshness_does_not_block_hard_safe_taxonomy(self) -> None:
        paper, acceleration, progress = self.ready_inputs()
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

        report = taxonomy.build_taxonomy(paper, acceleration, progress, risk_guard)

        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["safety"]["risk_guard_hard_safety_ok"])
        self.assertTrue(report["taxonomy"]["paper_smoke_evidence"]["ready"])
        self.assertEqual(report["current_decision"]["recommended_gatekeeper_lane"], "PAPER_SMOKE_REVIEW_READY")

    def test_hard_safety_failure_blocks_taxonomy(self) -> None:
        paper, acceleration, progress = self.ready_inputs()
        risk_guard = {
            "status": "WARN",
            "halt_count": 0,
            "checks": [
                {"name": "live_disabled", "status": "FAIL", "observed": True},
                {"name": "private_submit_unused", "status": "PASS", "observed": False},
                {"name": "real_orders_zero", "status": "PASS", "observed": 0},
            ],
        }

        report = taxonomy.build_taxonomy(paper, acceleration, progress, risk_guard)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["safety"]["risk_guard_hard_safety_ok"])
        self.assertFalse(report["taxonomy"]["paper_smoke_evidence"]["ready"])


if __name__ == "__main__":
    unittest.main()
