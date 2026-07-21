from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_btc_eth_intraday_shadow_human_decision_draft.py")
SPEC = importlib.util.spec_from_file_location("build_btc_eth_intraday_shadow_human_decision_draft", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
draft = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(draft)


class BtcEthIntradayShadowHumanDecisionDraftTests(unittest.TestCase):
    def test_builds_placeholder_draft_without_human_decision_or_order_paths(self) -> None:
        report = draft.build_draft(
            {
                "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "evidence_summary": {
                    "market": "KRW-BTC",
                    "timeframe": "4h",
                    "recommended_exposure_cap": 0.71,
                    "estimated_average_fold_cagr": 0.02,
                    "estimated_worst_fold_mdd": -0.12,
                },
            },
            {},
            False,
        )

        self.assertEqual(report["status"], "DRAFT_READY")
        self.assertEqual(report["candidate_id"], "btc_eth_intraday_momentum_btc_4h_sweep001")
        self.assertEqual(report["draft_decision"]["decision"], "HUMAN_MUST_CHOOSE_APPROVE_REJECT_OR_DEFER")
        self.assertIn("APPROVE_SHADOW_REVIEW_ONLY", report["draft_decision"]["allowed_decisions"])
        self.assertFalse(report["existing_human_decision_present"])
        self.assertFalse(report["safety"]["does_write_human_decision_file"])
        self.assertFalse(report["safety"]["does_register_shadow_candidate"])
        self.assertFalse(report["safety"]["does_emit_order_signal"])
        self.assertFalse(report["safety"]["does_enable_live"])
        self.assertFalse(report["safety"]["broker_submit_allowed_by_this_report"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_blocks_without_candidate_id(self) -> None:
        report = draft.build_draft({}, {}, False)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("BTC_ETH_INTRADAY_CANDIDATE_MISSING", report["blockers"])


if __name__ == "__main__":
    unittest.main()
