from __future__ import annotations

from scripts.manual_watchlist import render_text_watchlist


def test_render_text_watchlist_contains_sections() -> None:
    rendered = render_text_watchlist(
        {
            "generated_at": "2026-03-22T12:00:00Z",
            "strategy_id": "mean_rev_approved",
            "bundle_id": "policy_1",
            "headline": "1 actionable BUY candidate(s) available for manual review.",
            "buy_candidates": [
                {
                    "symbol": "BTC",
                    "rank": 1,
                    "policy_materiality": "entry_reversal",
                    "reference_price_krw": 100.0,
                    "suggested_stop_price_krw": 95.0,
                    "suggested_take_profit_price_krw": 110.0,
                    "risk_reward_ratio": 2.0,
                    "action_reason": "Policy uplift moved this candidate inside the active entry cutoff.",
                }
            ],
            "monitor_candidates": [
                {
                    "symbol": "ETH",
                    "rank": 2,
                    "policy_materiality": "near_miss",
                    "final_decision": "CANCELED:MAX_CONCURRENT",
                    "action_reason": "Boosted candidate remained a near miss after policy but capacity timing blocked entry.",
                }
            ],
            "warnings": ["Policy bundle valid_until is in the past."],
        }
    )

    assert "headline: 1 actionable BUY candidate(s) available for manual review." in rendered
    assert "BTC | rank=1 | policy=entry_reversal" in rendered
    assert "ETH | rank=2 | policy=near_miss | decision=CANCELED:MAX_CONCURRENT" in rendered
    assert "warnings:" in rendered
