from __future__ import annotations

from scripts.manual_pretrade_checklist import render_text_checklist


def test_render_text_checklist_contains_sections() -> None:
    rendered = render_text_checklist(
        {
            "generated_at": "2026-03-22T12:00:00Z",
            "strategy_id": "mean_rev_approved",
            "bundle_id": "policy_1",
            "headline": "1 buy candidate(s) require final manual checks before entry.",
            "general_checks": ["Confirm the setup still matches the latest candle."],
            "candidate_checklists": [
                {
                    "symbol": "BTC",
                    "rank": 1,
                    "policy_materiality": "entry_reversal",
                    "checks": [
                        {"label": "Reference price check", "detail": "Confirm current Bithumb price is still close to 100.0."}
                    ],
                }
            ],
            "warnings": ["Policy bundle valid_until is in the past."],
        }
    )

    assert "headline: 1 buy candidate(s) require final manual checks before entry." in rendered
    assert "general_checks:" in rendered
    assert "BTC | rank=1 | policy=entry_reversal" in rendered
    assert "Reference price check" in rendered
    assert "warnings:" in rendered
