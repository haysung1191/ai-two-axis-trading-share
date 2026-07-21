from __future__ import annotations

from scripts.manual_policy_materiality import render_text_materiality


def test_render_text_materiality_contains_gap_section() -> None:
    rendered = render_text_materiality(
        {
            "generated_at": "2026-03-22T07:00:00Z",
            "policy_snapshot": {"bundle_id": "policy_1"},
            "snapshot_metadata": {
                "market_filter": {
                    "below_ema": True,
                    "symbol": "BTC",
                    "close": 100.0,
                    "ema_period": 26,
                    "ema": 105.0,
                }
            },
            "policy_materiality": {
                "boosted_candidate_count": 1,
                "direct_reversals": 0,
                "direct_reversal_count": 0,
                "near_miss_count": 0,
                "cutoff_rank": 10,
                "cutoff_score": 3.0,
                "closest_to_reversal": [
                    {
                        "symbol": "SIGN",
                        "raw_rank": 5,
                        "final_rank": 5,
                        "final_decision": "CANCELED:MARKET_DOWNTREND",
                        "applied_delta": 0.05,
                        "gap_to_cutoff_after_boost": -0.4,
                        "required_extra_delta_for_cutoff": 0.0,
                        "policy_materiality": "boosted_but_not_decisive",
                    }
                ],
            },
        }
    )

    assert "market_filter:" in rendered
    assert "closest_boosted_candidates_to_reversal:" in rendered
    assert "SIGN" in rendered
