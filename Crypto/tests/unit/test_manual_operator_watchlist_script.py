from __future__ import annotations

from scripts.manual_operator_watchlist import render_text_operator_watchlist


def test_render_text_operator_watchlist_contains_sections() -> None:
    rendered = render_text_operator_watchlist(
        {
            "generated_at": "2026-03-22T16:00:00Z",
            "headline": "Market filter is active; recheck these names first when the filter releases.",
            "market_filter_active": True,
            "baseline_priority": [
                {
                    "symbol": "H",
                    "final_rank": 1,
                    "final_ranking_score": 6.0,
                    "policy_materiality": "none",
                    "note": "Baseline scanner strength alone keeps this candidate inside the counterfactual cutoff.",
                }
            ],
            "policy_assisted": [
                {
                    "symbol": "SIGN",
                    "final_rank": 5,
                    "final_ranking_score": 3.4,
                    "policy_score_delta": 0.05,
                    "policy_materiality": "boosted_but_not_decisive",
                    "note": "Policy contributes to this setup, but it was not decisive at the cutoff.",
                }
            ],
            "recheck_on_filter_release": [
                {"symbol": "H", "final_rank": 1, "final_ranking_score": 6.0, "policy_materiality": "none"},
                {"symbol": "SIGN", "final_rank": 5, "final_ranking_score": 3.4, "policy_materiality": "boosted_but_not_decisive"},
            ],
            "warnings": [],
        }
    )

    assert "baseline_priority:" in rendered
    assert "policy_assisted:" in rendered
    assert "recheck_on_filter_release:" in rendered
    assert "H | rank=1 | score=6.0 | policy=none" in rendered
    assert "SIGN | rank=5 | score=3.4 | delta=0.05 | policy=boosted_but_not_decisive" in rendered
