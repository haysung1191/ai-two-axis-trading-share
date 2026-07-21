from __future__ import annotations

from scripts.manual_today_briefing import render_text_today_briefing


def test_render_text_today_briefing_contains_all_sections() -> None:
    rendered = render_text_today_briefing(
        {
            "daily_summary": {
                "generated_at": "2026-03-22T12:00:00Z",
                "strategy_snapshot": {
                    "strategy_id": "mean_rev_approved",
                    "source_run_id": "run-1",
                    "symbol": "BTCUSDT",
                    "timeframe": "1h",
                    "metrics": {"sharpe": 1.2, "max_drawdown": 0.1, "win_rate": 0.55, "trades": 120, "cagr": 0.08},
                },
                "policy_snapshot": {
                    "bundle_id": "policy_1",
                    "bundle_mode": "shadow",
                    "policy_type": "filter_and_boost",
                    "symbol_scope_count": 2,
                    "boost_score": 0.1,
                    "valid_until": "2099-01-01T00:00:00Z",
                },
                "manual_brief": {
                    "headline": "Actionable BUY candidates exist, but policy was not decisive at the cutoff.",
                    "summary": {
                        "buy_count": 1,
                        "hold_count": 0,
                        "no_buy_count": 0,
                        "scheduled_due_to_policy_count": 0,
                        "near_miss_after_policy_count": 0,
                    },
                    "watchlist": [],
                },
                "warnings": [],
            },
            "operator_watchlist": {
                "generated_at": "2026-03-22T12:00:00Z",
                "strategy_id": "mean_rev_approved",
                "bundle_id": "policy_1",
                "headline": "Market filter is active; recheck these names first when the filter releases.",
                "market_filter_active": True,
                "baseline_priority": [],
                "policy_assisted": [],
                "recheck_on_filter_release": [],
                "warnings": [],
            },
            "watchlist": {
                "generated_at": "2026-03-22T12:00:00Z",
                "strategy_id": "mean_rev_approved",
                "bundle_id": "policy_1",
                "headline": "1 actionable BUY candidate(s) available for manual review.",
                "buy_candidates": [],
                "monitor_candidates": [],
                "warnings": [],
            },
            "pretrade_checklist": {
                "generated_at": "2026-03-22T12:00:00Z",
                "strategy_id": "mean_rev_approved",
                "bundle_id": "policy_1",
                "headline": "1 buy candidate(s) require final manual checks before entry.",
                "general_checks": ["Confirm the setup still matches the latest candle."],
                "candidate_checklists": [],
                "warnings": [],
            },
        }
    )

    assert "=== Daily Summary ===" in rendered
    assert "=== Operator Watchlist ===" in rendered
    assert "=== Watchlist ===" in rendered
    assert "=== Pre-trade Checklist ===" in rendered
