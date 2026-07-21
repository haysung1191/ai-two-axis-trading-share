from __future__ import annotations

from src.manual.checklist import build_pretrade_checklist


def test_build_pretrade_checklist_for_buy_candidates() -> None:
    payload = build_pretrade_checklist(
        watchlist={
            "generated_at": "2026-03-22T12:00:00Z",
            "strategy_id": "mean_rev_approved",
            "bundle_id": "policy_1",
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
            "warnings": ["Policy bundle valid_until is in the past."],
        }
    )

    assert "buy candidate" in payload["headline"]
    assert payload["candidate_checklists"][0]["symbol"] == "BTC"
    assert len(payload["candidate_checklists"][0]["checks"]) >= 5
    assert any("warnings" in item.lower() for item in payload["general_checks"])


def test_build_pretrade_checklist_handles_no_buy_candidates() -> None:
    payload = build_pretrade_checklist(
        watchlist={
            "generated_at": "2026-03-22T12:00:00Z",
            "strategy_id": "mean_rev_approved",
            "bundle_id": "policy_1",
            "buy_candidates": [],
            "warnings": [],
        }
    )

    assert "No buy candidates" in payload["headline"]
    assert payload["candidate_checklists"] == []
