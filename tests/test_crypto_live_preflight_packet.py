from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_crypto_live_preflight_packet.py")
SPEC = importlib.util.spec_from_file_location("build_crypto_live_preflight_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


class CryptoLivePreflightPacketTests(unittest.TestCase):
    def base_inputs(self) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
        return (
            {"approval_text_supplied": True, "status": "ready_for_human_live_review"},
            {
                "simulated_orders": [
                    {
                        "asset": "crypto",
                        "symbol": "KRW-BTC",
                        "action": "BUY",
                        "target_weight": 0.1,
                        "delta_weight": 0.1,
                        "executable": True,
                    }
                ],
                "paper_enabled_flag": False,
                "live_enabled_flag": False,
                "real_orders": 0,
                "private_submit_used": False,
                "broker_submit_scope": "paper_only",
            },
            {"status": "PASS"},
            {"current_decision": {"live_or_real_order_allowed": False}},
            {"suggested_sleeves": [{"lane": "bithumb_crypto", "candidate_id": "bridge_28_relief"}]},
        )

    def test_packet_blocks_without_realtime_market_data_guard(self) -> None:
        packet = preflight.build_packet(*self.base_inputs(), {})

        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("CRYPTO_REALTIME_MARKET_DATA_NOT_FRESH", packet["blockers"])
        self.assertFalse(packet["safety"]["does_enable_trading"])

    def test_packet_can_reach_review_when_realtime_guard_and_signal_are_present(self) -> None:
        packet = preflight.build_packet(
            *self.base_inputs(),
            {
                "status": "PASS",
                "market": "KRW-BTC",
                "ticker": {"price_krw": 100000000.0, "age_seconds": 1.0},
                "orderbook": {"best_bid_krw": 99990000.0, "best_ask_krw": 100010000.0},
                "safety": {"does_call_private_api": False},
            },
        )

        self.assertEqual(packet["status"], "READY_FOR_EXPLICIT_LIVE_APPROVAL_REVIEW")
        self.assertNotIn("CRYPTO_REALTIME_MARKET_DATA_NOT_FRESH", packet["blockers"])


if __name__ == "__main__":
    unittest.main()
