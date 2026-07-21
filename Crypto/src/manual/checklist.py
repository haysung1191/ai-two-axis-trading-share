from __future__ import annotations

from typing import Any


def _fmt(value: Any) -> str:
    return "not available" if value in (None, "") else str(value)


def build_pretrade_checklist(
    *,
    watchlist: dict[str, Any],
    max_items: int = 3,
) -> dict[str, Any]:
    buy_candidates = list(watchlist.get("buy_candidates", []))
    warnings = list(watchlist.get("warnings", []))
    checklist_items: list[dict[str, Any]] = []

    for candidate in buy_candidates[: max(1, max_items)]:
        items = [
            {
                "type": "price_confirm",
                "label": "Reference price check",
                "detail": f"Confirm current Bithumb price is still close to {_fmt(candidate.get('reference_price_krw'))}.",
            },
            {
                "type": "stop_confirm",
                "label": "Stop price check",
                "detail": f"Confirm planned stop is around {_fmt(candidate.get('suggested_stop_price_krw'))}.",
            },
            {
                "type": "target_confirm",
                "label": "Take profit check",
                "detail": f"Confirm planned take-profit is around {_fmt(candidate.get('suggested_take_profit_price_krw'))}.",
            },
            {
                "type": "risk_reward",
                "label": "Risk/reward check",
                "detail": f"Expected risk/reward is about {_fmt(candidate.get('risk_reward_ratio'))}.",
            },
            {
                "type": "thesis_check",
                "label": "Entry thesis check",
                "detail": str(candidate.get("action_reason", "")),
            },
        ]
        checklist_items.append(
            {
                "symbol": candidate.get("symbol"),
                "rank": candidate.get("rank"),
                "policy_materiality": candidate.get("policy_materiality"),
                "checks": items,
            }
        )

    general_checks = [
        "Confirm the setup still matches the latest candle and has not materially moved since the artifact was generated.",
        "Do not override bundle expiry or governance warnings without a conscious manual decision.",
        "If no BUY candidates exist, do not force an entry from monitor-only names.",
    ]
    if warnings:
        general_checks.append("Review warnings before placing any manual order.")

    headline: str
    if checklist_items:
        headline = f"{len(checklist_items)} buy candidate(s) require final manual checks before entry."
    else:
        headline = "No buy candidates are available for a pre-trade checklist."

    return {
        "generated_at": watchlist.get("generated_at"),
        "headline": headline,
        "strategy_id": watchlist.get("strategy_id"),
        "bundle_id": watchlist.get("bundle_id"),
        "candidate_checklists": checklist_items,
        "general_checks": general_checks,
        "warnings": warnings,
    }
