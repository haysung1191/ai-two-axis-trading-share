from __future__ import annotations

from typing import Any


def _priority(row: dict[str, Any]) -> tuple[int, int, str]:
    materiality = str(row.get("policy_materiality", "none"))
    rank = int(row.get("rank", 10**6))
    symbol = str(row.get("symbol", ""))
    materiality_rank = {
        "entry_reversal": 0,
        "boosted_but_not_decisive": 1,
        "near_miss": 2,
        "policy_reject": 3,
        "none": 4,
    }.get(materiality, 5)
    return (materiality_rank, rank, symbol)


def build_manual_watchlist(
    *,
    daily_summary: dict[str, Any],
    recommendations: list[dict[str, Any]],
    max_buy: int = 3,
    max_monitor: int = 5,
) -> dict[str, Any]:
    buys = sorted(
        [row for row in recommendations if str(row.get("action")) == "BUY"],
        key=_priority,
    )
    monitors = sorted(
        [
            row
            for row in recommendations
            if str(row.get("action")) != "BUY"
            and (
                str(row.get("action")) == "HOLD"
                or str(row.get("policy_materiality")) in {"near_miss", "boosted_but_not_decisive"}
            )
        ],
        key=_priority,
    )

    warnings = list(daily_summary.get("warnings", []))
    for row in buys:
        missing = [
            label
            for key, label in (
                ("reference_price_krw", "reference price"),
                ("suggested_stop_price_krw", "stop"),
                ("suggested_take_profit_price_krw", "target"),
                ("risk_reward_ratio", "risk/reward"),
            )
            if row.get(key) in (None, "")
        ]
        if missing:
            warnings.append(
                f"{row.get('symbol', '-')}: manual BUY candidate is missing {', '.join(missing)} data."
            )
    headline: str
    if buys:
        headline = f"{len(buys)} actionable BUY candidate(s) available for manual review."
    elif monitors:
        headline = "No immediate BUY, but there are monitor-worthy candidates."
    else:
        headline = "No actionable watchlist candidates under the current local artifacts."

    buy_list = [
        {
            "symbol": row.get("symbol"),
            "rank": row.get("rank"),
            "policy_materiality": row.get("policy_materiality"),
            "reference_price_krw": row.get("reference_price_krw"),
            "suggested_stop_price_krw": row.get("suggested_stop_price_krw"),
            "suggested_take_profit_price_krw": row.get("suggested_take_profit_price_krw"),
            "risk_reward_ratio": row.get("risk_reward_ratio"),
            "action_reason": row.get("action_reason"),
        }
        for row in buys[: max(1, max_buy)]
    ]
    monitor_list = [
        {
            "symbol": row.get("symbol"),
            "rank": row.get("rank"),
            "policy_materiality": row.get("policy_materiality"),
            "final_decision": row.get("final_decision"),
            "action_reason": row.get("action_reason"),
        }
        for row in monitors[: max(1, max_monitor)]
    ]

    return {
        "generated_at": daily_summary.get("generated_at"),
        "headline": headline,
        "strategy_id": daily_summary.get("strategy_snapshot", {}).get("strategy_id"),
        "bundle_id": daily_summary.get("policy_snapshot", {}).get("bundle_id"),
        "buy_candidates": buy_list,
        "monitor_candidates": monitor_list,
        "warnings": list(dict.fromkeys(warnings)),
    }
