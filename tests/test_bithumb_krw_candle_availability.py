from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\Crypto\scripts\build_bithumb_krw_candle_availability.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_krw_candle_availability", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
availability = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(availability)


class BithumbKrwCandleAvailabilityTests(unittest.TestCase):
    def test_selected_batch_can_include_watchlist_after_research_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            liquidity = root / "liquidity.json"
            liquidity.write_text(
                """
{
  "markets": [
    {"market": "KRW-WATCH-HIGH", "lane": "watchlist", "acc_trade_price_24h": 9000},
    {"market": "KRW-RESEARCH", "lane": "research_batch", "acc_trade_price_24h": 1000},
    {"market": "KRW-LOW", "lane": "low_liquidity", "acc_trade_price_24h": 999999}
  ]
}
""".strip(),
                encoding="utf-8",
            )
            availability.LIQUIDITY_PATH = liquidity

            rows = availability._selected_batch(limit=None, lanes={"research_batch", "watchlist"})

        self.assertEqual([row["market"] for row in rows], ["KRW-RESEARCH", "KRW-WATCH-HIGH"])

    def test_parse_lanes_defaults_to_research_batch(self) -> None:
        self.assertEqual(availability._parse_lanes(""), {"research_batch"})
        self.assertEqual(availability._parse_lanes("research_batch, watchlist"), {"research_batch", "watchlist"})
        self.assertEqual(
            availability._parse_lanes("all"),
            {"research_batch", "watchlist", "low_liquidity"},
        )

    def test_summary_surfaces_full_bithumb_universe_coverage(self) -> None:
        summary = availability._summary(
            [{"status": "model_ready_1d"}, {"status": "insufficient_history"}],
            selected_count=2,
            total_liquidity_markets=2,
            selected_lanes={"research_batch", "watchlist", "low_liquidity"},
        )

        self.assertEqual(summary["checked_market_count"], 2)
        self.assertEqual(summary["model_ready_1d_count"], 1)
        self.assertTrue(summary["covers_full_bithumb_krw_universe"])
        self.assertEqual(summary["coverage_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
