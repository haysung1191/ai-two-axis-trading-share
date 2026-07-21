from __future__ import annotations

import unittest

import run_research_lane_stage1_loop as loop


class ResearchLaneStage1LoopTests(unittest.TestCase):
    def test_candidate_status_separates_conversion_high_risk_and_rejects(self) -> None:
        conversion = {
            "total": {"cagr": 0.80, "mdd": -0.30, "average_daily_turnover": 0.05},
            "test": {"cagr": 0.40, "mdd": -0.25, "sharpe": 1.2},
        }
        high_risk = {
            "total": {"cagr": 2.00, "mdd": -0.70, "average_daily_turnover": 0.05},
            "test": {"cagr": 0.80, "mdd": -0.55, "sharpe": 1.1},
        }
        reject = {
            "total": {"cagr": 0.50, "mdd": -0.50, "average_daily_turnover": 0.30},
            "test": {"cagr": -0.10, "mdd": -0.40, "sharpe": -0.2},
        }

        self.assertEqual(loop.candidate_status(conversion)[0], "conversion_candidate")
        self.assertEqual(loop.candidate_status(high_risk)[0], "high_return_high_risk_research")
        self.assertEqual(loop.candidate_status(reject)[0], "research_reject_or_redesign")

    def test_normalized_btc_reference_is_not_account_model(self) -> None:
        row = {
            "strategy_name": "btc_1d_post_spike_consolidation_breakout_v4",
            "cagr": 0.50,
            "mdd": -0.12,
            "sharpe": 2.0,
            "days": 1000,
        }
        normalized = loop.normalize_account_candidate("btc_single_asset_reference", row, "unit")

        self.assertEqual(normalized["account"], "btc_single_asset_reference")
        self.assertEqual(normalized["family"], "btc_1d_post_spike_consolidation_breakout_v4")
        self.assertEqual(normalized["total"]["cagr"], 0.50)

    def test_render_markdown_reports_research_only_safety(self) -> None:
        payload = {
            "generated_at": "2026-05-10T00:00:00+00:00",
            "status": "RESEARCH_LANE_STAGE1_READY",
            "safety": {
                "paper_enabled": False,
                "live_enabled": False,
                "broker_submit_allowed": False,
                "real_orders": 0,
            },
            "coverage": {
                "kis_loaded_symbols": 11996,
                "kis_strategy_rows": 72,
                "bithumb_ready_markets": 457,
                "bithumb_selected_markets": 34,
                "bithumb_strategy_rows": 34,
                "legacy_momentum_completed": 32,
                "legacy_crypto_completed": 478,
            },
            "summary": {
                "conversion_candidate_count": 1,
                "high_risk_research_count": 0,
                "reject_or_redesign_count": 0,
            },
            "conversion_queue": [
                {
                    "account": "kis_account",
                    "family": "combined_short_reversal_l5_top50_axiscap0.5_reb21",
                    "status": "conversion_candidate",
                    "tags": ["conversion_candidate"],
                    "total": {"cagr": 0.88, "mdd": -0.34},
                    "test": {"cagr": 0.72, "mdd": -0.34},
                }
            ],
            "next_action": "unit next action",
        }

        markdown = loop.render_markdown(payload)

        self.assertIn("paper/live/broker: `False` / `False` / `False`", markdown)
        self.assertIn("combined_short_reversal_l5_top50_axiscap0.5_reb21", markdown)
        self.assertIn("unit next action", markdown)


if __name__ == "__main__":
    unittest.main()
