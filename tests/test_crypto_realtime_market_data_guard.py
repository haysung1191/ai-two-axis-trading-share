from __future__ import annotations

import importlib.util
import unittest
from datetime import UTC, datetime
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_crypto_realtime_market_data_guard.py")
SPEC = importlib.util.spec_from_file_location("build_crypto_realtime_market_data_guard", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class CryptoRealtimeMarketDataGuardTests(unittest.TestCase):
    def test_guard_passes_with_public_ticker_and_orderbook_without_order_permissions(self) -> None:
        def fake_fetch(url: str) -> dict[str, object]:
            if "/ticker/" in url:
                return {
                    "status": "0000",
                    "data": {
                        "closing_price": "100000000",
                        "date": str(int(datetime.now(tz=UTC).timestamp() * 1000)),
                    },
                }
            return {
                "status": "0000",
                "data": {
                    "bids": [{"price": "99990000", "quantity": "0.1"}],
                    "asks": [{"price": "100010000", "quantity": "0.1"}],
                },
            }

        report = guard.build_guard(fetch_json=fake_fetch)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["ticker"]["price_krw"], 100000000.0)
        self.assertEqual(report["blockers"], [])
        self.assertFalse(report["safety"]["does_call_private_api"])
        self.assertFalse(report["safety"]["real_orders_allowed_by_this_report"])
        self.assertFalse(report["safety"]["private_submit_allowed_by_this_report"])

    def test_guard_blocks_when_ticker_is_unavailable(self) -> None:
        def fake_fetch(url: str) -> dict[str, object]:
            return {"status": "5100", "message": "bad request"}

        report = guard.build_guard(fetch_json=fake_fetch)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("BITHUMB_REALTIME_TICKER_UNAVAILABLE", report["blockers"])
        self.assertFalse(report["safety"]["does_enable_trading"])


if __name__ == "__main__":
    unittest.main()
