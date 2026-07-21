import unittest
from unittest.mock import patch

import build_tiny_live_order_intent as tiny


class TinyLiveOrderIntentTests(unittest.TestCase):
    def test_approval_text_uses_legacy_firewall_format(self):
        caps = {"max_krw": 200000.0, "max_daily_loss_krw": 10000.0, "max_total_loss_krw": 30000.0}

        self.assertEqual(tiny.approval_text(caps), "LIVE APPROVE 200000 10000 30000")

    def test_policy_is_limited_live(self):
        caps = {
            "max_krw": 200000.0,
            "crypto_cap_krw": 100000.0,
            "stock_cap_krw": 100000.0,
            "max_order_krw": 100000.0,
            "max_daily_loss_krw": 10000.0,
            "max_total_loss_krw": 30000.0,
        }

        policy = tiny.build_policy(caps)

        self.assertEqual(policy["policy_mode"], "limited_live")
        self.assertEqual(policy["broker_submit_scope"], "limited_live")
        self.assertTrue(policy["real_orders_allowed"])

    def test_builds_orca_limited_live_intent_and_firewall_passes_without_submit(self):
        signal = {
            "top_triggered_candidate": {
                "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep2154",
                "market": "KRW-ORCA",
                "signal": {"triggered": True, "latest_close": 2314.0},
            }
        }
        with patch.object(tiny, "read_json", return_value=signal), patch.object(tiny.Path, "exists", return_value=True):
            report = tiny.build_report("LIVE APPROVE 100000 20000 100000", write=False)

        self.assertEqual(report["market"], "KRW-ORCA")
        self.assertEqual(report["notional_krw"], 10000.0)
        self.assertEqual(report["firewall"]["decision"], "ALLOW_LIMITED_LIVE")
        self.assertEqual(report["broker_submit_attempt_status"], "BLOCKED_BY_GLOBAL_DISABLE")
        self.assertEqual(report["submitted_order_count"], 0)

    def test_rejects_wrong_live_approval_phrase(self):
        with self.assertRaises(ValueError):
            tiny.parse_live_approval("해줘")


if __name__ == "__main__":
    unittest.main()
