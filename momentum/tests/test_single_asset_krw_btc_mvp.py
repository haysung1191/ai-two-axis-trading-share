import unittest

import pandas as pd

from app.single_asset.candidate_seeds import get_single_asset_candidates
from app.single_asset.evaluator import evaluate_single_asset_candidate
from app.single_asset.strategies.krw_btc_bb_rsi_mean_reversion import build_signal_frame


class KRWBTCMVPSmokeTests(unittest.TestCase):
    def test_candidate_registry_includes_mvp(self) -> None:
        candidates = get_single_asset_candidates()
        ids = {c["candidate_id"] for c in candidates}
        self.assertIn("krw_btc_1h_bb20_rsi14_mr_v1", ids)

    def test_signal_frame_emits_strategy_columns(self) -> None:
        close = [100.0] * 20 + [90.0] * 5 + [105.0] * 5
        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2026-01-01", periods=len(close), freq="h"),
                "open": close,
                "high": close,
                "low": close,
                "close": close,
                "volume": [1.0] * len(close),
            }
        )
        out = build_signal_frame(df)
        for col in ["sma20", "lower_bb20_2", "rsi14", "entry_condition", "exit_condition", "position", "event"]:
            self.assertIn(col, out.columns)

    def test_evaluator_runs_single_asset_candidate(self) -> None:
        candles = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-01", periods=200, freq="h"),
                "open": [100.0] * 200,
                "high": [100.0] * 200,
                "low": [100.0] * 200,
                "close": [100.0] * 180 + [80.0] * 10 + [100.0] * 10,
                "volume": [1.0] * 200,
            }
        )
        candidate = get_single_asset_candidates()[0]
        result, signal_frame, trade_log = evaluate_single_asset_candidate(candidate, candles, "test_run")
        self.assertEqual(result.symbol, "KRW-BTC")
        self.assertEqual(result.interval, "1h")
        self.assertTrue("strategy_return" in signal_frame.columns)
        self.assertIsInstance(trade_log, pd.DataFrame)


if __name__ == "__main__":
    unittest.main()
