from __future__ import annotations

import json
import math
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

import run_stock_etf_combined_account_factory as factory
import verified_gatekeeper_v2 as gatekeeper


class VerifiedPipelineBacktestSanityTests(unittest.TestCase):
    def test_rank_strategy_uses_shifted_positions_and_costs(self) -> None:
        dates = pd.date_range("2024-01-01", periods=8, freq="D")
        close = pd.DataFrame(
            {
                "A": [100.0, 110.0, 121.0, 133.1, 146.41, 161.051, 177.1561, 194.87171],
                "B": [100.0, 90.0, 81.0, 72.9, 65.61, 59.049, 53.1441, 47.82969],
            },
            index=dates,
        )
        value = close * 1000.0
        score = pd.DataFrame({"A": [1.0] * len(dates), "B": [0.0] * len(dates)}, index=dates)

        result = factory._backtest_combined_rank_strategy(
            close,
            value,
            {"A": "us_stock", "B": "us_stock"},
            family="unit_shift_check",
            score=score,
            top_k=1,
            rebalance_days=1,
            cost_bps=0.0,
            min_history=1,
            min_price=1.0,
            min_avg_value=0.0,
            long_when_positive=True,
            max_axis_weight=1.0,
        )

        returns = result["returns"]
        self.assertEqual(len(returns), 4)
        self.assertAlmostEqual(float(returns.iloc[0]), 0.0)
        self.assertAlmostEqual(float(returns.iloc[1]), 0.10)
        self.assertAlmostEqual(float(returns.iloc[2]), 0.10)
        self.assertAlmostEqual(float(returns.iloc[3]), 0.10)

    def test_usdkrw_fx_applies_only_to_us_axes(self) -> None:
        with TemporaryDirectory() as tmp:
            fx_path = Path(tmp) / "usdkrw.csv"
            fx_path.write_text("date,usd_krw\n2024-01-01,1000\n2024-01-02,1100\n", encoding="utf-8")
            args = type("Args", (), {"fx_mode": "usdkrw_daily", "fx_path": str(fx_path)})()
            dates = pd.date_range("2024-01-01", periods=2, freq="D")
            close = pd.DataFrame({"A": [2.0, 3.0]}, index=dates)
            value = pd.DataFrame({"A": [20.0, 30.0]}, index=dates)

            us_close, us_value, us_meta = factory._apply_fx_if_needed("us_stock", close, value, args)
            kr_close, kr_value, kr_meta = factory._apply_fx_if_needed("kr_stock", close, value, args)

            self.assertEqual(list(us_close["A"]), [2000.0, 3300.0])
            self.assertEqual(list(us_value["A"]), [20000.0, 33000.0])
            self.assertEqual(list(kr_close["A"]), [2.0, 3.0])
            self.assertEqual(list(kr_value["A"]), [20.0, 30.0])
            self.assertTrue(us_meta["fx_applied"])
            self.assertFalse(kr_meta["fx_applied"])

    def test_metrics_cagr_mdd_sharpe_sanity(self) -> None:
        returns = pd.Series([0.10, -0.05, 0.02])
        turnover = pd.Series([1.0, 0.0, 0.0])
        metrics = factory._metrics(returns, turnover)
        equity = (1.0 + returns).cumprod()
        expected_mdd = float((equity / equity.cummax() - 1.0).min())
        expected_cagr = float(equity.iloc[-1] ** (1.0 / (3 / 252.0)) - 1.0)
        self.assertAlmostEqual(metrics["mdd"], expected_mdd)
        self.assertAlmostEqual(metrics["cagr"], expected_cagr)
        self.assertTrue(math.isfinite(metrics["sharpe"]))


class VerifiedGatekeeperIsolationTests(unittest.TestCase):
    def test_gatekeeper_reads_verified_registry_and_quarantines_legacy_tokens(self) -> None:
        with TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "registry.json"
            registry_path.write_text(
                json.dumps(
                    {
                        "data_epoch": "unit-test",
                        "summary": {"stock_etf_fx_mode": "usdkrw_daily"},
                        "candidates": [
                            {
                                "candidate_id": "verified.stock.good",
                                "axis": "stock_etf_combined",
                                "family": "clean_candidate",
                                "source": "unit",
                                "blockers": [],
                                "total": {"days": 300, "cagr": 0.25, "mdd": -0.20, "sharpe": 1.4},
                                "test": {"cagr": 0.10, "sharpe": 1.0},
                            },
                            {
                                "candidate_id": "verified.crypto.bridge_28_relief",
                                "axis": "btc_active_stack_recompute",
                                "family": "bridge_28_relief",
                                "source": "unit",
                                "blockers": [],
                                "total": {"days": 400, "cagr": 0.30, "mdd": -0.10, "sharpe": 2.0},
                                "test": {"cagr": 0.20, "sharpe": 1.0},
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with patch.object(gatekeeper, "REGISTRY", registry_path):
                report = gatekeeper.build_report()

        self.assertEqual(report["summary"]["candidate_count"], 2)
        self.assertEqual(report["summary"]["conversion_candidate_count"], 1)
        self.assertEqual(report["summary"]["promotion_ready_count"], 0)
        self.assertFalse(report["safety"]["paper_enabled"])
        self.assertFalse(report["safety"]["live_enabled"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        blocked = report["top_research_blocked"][0]
        self.assertIn("legacy_candidate_token_quarantined", blocked["gatekeeper_blockers"])
        self.assertIn("btc_active_stack_legacy_reference_only", blocked["gatekeeper_blockers"])


if __name__ == "__main__":
    unittest.main()
