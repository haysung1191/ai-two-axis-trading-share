from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stage4_risk_compression_queue_status.py")
SPEC = importlib.util.spec_from_file_location("build_stage4_risk_compression_queue_status", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
status = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(status)


class Stage4RiskCompressionQueueStatusTests(unittest.TestCase):
    def test_cand019_routes_to_existing_cand022_child_when_g2_exists(self) -> None:
        report = status.build_report(
            queue_rows=[
                {
                    "candidate_id": "CAND-019",
                    "candidate_name": "aggressive",
                    "transition_id": "RESEARCH_TO_COMPRESSION::CAND-019",
                    "source_artifact": "candidate_registry.jsonl",
                }
            ],
            candidate_rows=[
                {
                    "candidate_id": "CAND-019",
                    "universe": "KIS_COMBINED_KRW",
                    "metrics": {"cagr": 0.673, "mdd": -0.261, "sharpe": 1.739},
                }
            ],
            compression_packet={
                "g2_candidates_count": 1,
                "g2_candidates": [{"variant": "compressed_broe60_sroe80", "cagr": 0.661, "mdd": -0.246, "sharpe": 1.753}],
            },
        )

        self.assertEqual(report["status"], "READY_STAGE4_QUEUE_STATUS")
        self.assertEqual(report["queue_record_count"], 1)
        self.assertEqual(report["ready_existing_child_count"], 1)
        route = report["entries"][0]["route"]
        self.assertEqual(route["status"], "HAS_COMPRESSED_G2_CHILD_READY_FOR_STAGE5_REVIEW")
        self.assertEqual(route["next_candidate_hint"], "CAND-022")
        self.assertFalse(report["safety"]["paper_enabled"])
        self.assertFalse(report["safety"]["live_enabled"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertEqual(report["safety"]["pretrade_firewall_default_decision"], "BLOCK")

    def test_bithumb_queue_record_remains_research_only(self) -> None:
        report = status.build_report(
            queue_rows=[{"candidate_id": "CAND-021", "candidate_name": "btc compressed"}],
            candidate_rows=[
                {
                    "candidate_id": "CAND-021",
                    "universe_id": "BITHUMB_KRW_BTC_ONLY",
                    "blockers": ["no_oos_parameters_defined"],
                }
            ],
            compression_packet={},
        )

        route = report["entries"][0]["route"]
        self.assertEqual(route["route"], "crypto_compression_or_oos_repair")
        self.assertEqual(route["status"], "BLOCKED_OR_RESEARCH_ONLY_UNTIL_OOS_AND_ACCOUNT_SCOPE_VERIFIED")
        self.assertEqual(report["ready_existing_child_count"], 0)


if __name__ == "__main__":
    unittest.main()
