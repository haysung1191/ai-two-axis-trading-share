from __future__ import annotations

from collections import Counter
from typing import Any


def _sort_key(row: dict[str, Any]) -> tuple[int, int, str]:
    action = str(row.get("action", "NO_BUY"))
    policy_materiality = str(row.get("policy_materiality", "none"))
    rank = int(row.get("rank", 10**6))
    symbol = str(row.get("symbol", ""))

    action_priority = {
        "BUY": 0,
        "HOLD": 1,
        "NO_BUY": 2,
    }.get(action, 3)
    materiality_priority = {
        "entry_reversal": 0,
        "near_miss": 1,
        "boosted_but_not_decisive": 2,
        "policy_reject": 3,
        "none": 4,
    }.get(policy_materiality, 5)
    return (action_priority, materiality_priority, rank, symbol)


def build_hourly_manual_brief(
    *,
    run_id: str,
    candle_close_utc: str,
    signals: list[dict[str, Any]],
    max_items: int = 5,
) -> dict[str, Any]:
    action_counts = Counter(str(row.get("action", "NO_BUY")) for row in signals)
    blocker_counts = Counter(
        str(row.get("blocked_reason", ""))
        for row in signals
        if str(row.get("blocked_reason", "")) not in {"", "None"}
    )
    scheduled_due_to_policy_count = sum(bool(row.get("scheduled_due_to_policy")) for row in signals)
    near_miss_count = sum(bool(row.get("near_miss_after_policy")) for row in signals)

    if scheduled_due_to_policy_count > 0:
        headline = "Policy created at least one actionable entry reversal in this run."
    elif action_counts.get("BUY", 0) > 0:
        headline = "Actionable BUY candidates exist, but policy was not decisive at the cutoff."
    elif near_miss_count > 0:
        headline = "No BUY signal cleared the gate, but policy-boosted near misses were present."
    else:
        headline = "No actionable BUY candidates in this run under current guardrails."

    notes: list[str] = []
    top_blockers = blocker_counts.most_common(2)
    if top_blockers:
        notes.append(
            "Primary blockers: "
            + ", ".join(f"{name} x{count}" for name, count in top_blockers)
        )
    if scheduled_due_to_policy_count > 0:
        notes.append("Policy changed admission for at least one scheduled candidate.")
    elif near_miss_count > 0:
        notes.append("Policy changed ranking but still left candidates just below admission.")
    else:
        notes.append("Baseline scanner and guardrails dominated this run.")

    ranked_items = sorted(signals, key=_sort_key)
    watchlist = [
        {
            "symbol": row.get("symbol"),
            "rank": row.get("rank"),
            "action": row.get("action"),
            "policy_materiality": row.get("policy_materiality"),
            "reference_price_krw": row.get("reference_price_krw"),
            "suggested_stop_price_krw": row.get("suggested_stop_price_krw"),
            "suggested_take_profit_price_krw": row.get("suggested_take_profit_price_krw"),
            "risk_reward_ratio": row.get("risk_reward_ratio"),
            "final_decision": row.get("final_decision"),
            "action_reason": row.get("action_reason"),
        }
        for row in ranked_items[: max(1, max_items)]
    ]

    return {
        "run_id": run_id,
        "candle_close_utc": candle_close_utc,
        "headline": headline,
        "summary": {
            "buy_count": int(action_counts.get("BUY", 0)),
            "hold_count": int(action_counts.get("HOLD", 0)),
            "no_buy_count": int(action_counts.get("NO_BUY", 0)),
            "scheduled_due_to_policy_count": int(scheduled_due_to_policy_count),
            "near_miss_after_policy_count": int(near_miss_count),
        },
        "notes": notes,
        "watchlist": watchlist,
    }
