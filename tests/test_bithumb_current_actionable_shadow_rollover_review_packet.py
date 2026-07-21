from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_shadow_rollover_review_packet.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_shadow_rollover_review_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
rollover = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rollover)


class BithumbCurrentActionableShadowRolloverReviewPacketTests(unittest.TestCase):
    def test_detects_rollover_and_keeps_order_paths_closed(self) -> None:
        packet = rollover.build_packet(
            {
                "records": [
                    {
                        "lane": "bithumb_1d",
                        "status": "SHADOW_REVIEW_REGISTERED",
                        "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354",
                        "market": "KRW-POLA",
                        "timeframe": "1d",
                        "estimated_cagr": 0.94,
                        "estimated_mdd": -0.2,
                    }
                ]
            },
            {
                "top_oos": {
                    "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "status": "OOS_CANDIDATE_PASS",
                    "source_conversion": {
                        "estimated_cagr": 1.06,
                        "estimated_mdd": -0.2,
                        "source_profit_factor": 2.59,
                        "source_trade_count": 17,
                    },
                }
            },
            {
                "human_decision_summary": {
                    "expected_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                    "recorded_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354",
                    "decision_recorded": False,
                    "decision": "APPROVE_SHADOW_REVIEW_ONLY",
                }
            },
            {
                "status": "SHADOW_SIGNAL_READY",
                "parameter_source": "top_oos_same_family_market_timeframe_fallback",
                "parameter_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                "warnings": ["OOS_PARAMETERS_FALLBACK_TO_SAME_FAMILY_CURRENT_TOP"],
                "signal": {
                    "shadow_action": "SHADOW_TARGET_OBSERVATION",
                    "triggered": True,
                    "target_shadow_weight": 0.86,
                },
            },
        )

        self.assertEqual(packet["status"], "ROLLOVER_REVIEW_READY")
        self.assertTrue(packet["comparison"]["candidate_rollover_detected"])
        self.assertIn("FRESH_HUMAN_DECISION_REQUIRED_FOR_LATEST_OOS_CANDIDATE", packet["blockers"])
        self.assertIn("RECORDED_HUMAN_DECISION_DOES_NOT_MATCH_LATEST_OOS_CANDIDATE", packet["blockers"])
        self.assertFalse(packet["safety"]["does_register_shadow_candidate"])
        self.assertFalse(packet["safety"]["does_emit_order_signal"])
        self.assertFalse(packet["safety"]["does_write_order_intent"])
        self.assertFalse(packet["safety"]["does_enable_live"])
        self.assertFalse(packet["safety"]["broker_submit_allowed_by_this_report"])
        self.assertEqual(packet["safety"]["real_orders"], 0)

    def test_blocks_without_registered_candidate(self) -> None:
        packet = rollover.build_packet({"records": []}, {}, {}, {})

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("REGISTERED_SHADOW_REVIEW_CANDIDATE_MISSING", packet["blockers"])


if __name__ == "__main__":
    unittest.main()
