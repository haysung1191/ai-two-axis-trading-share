from __future__ import annotations

from typing import Any


def _policy_bucket(row: dict[str, Any]) -> str:
    materiality = str(row.get("policy_materiality", "none"))
    if materiality in {"entry_reversal", "boosted_but_not_decisive", "near_miss"}:
        return "policy_assisted"
    return "baseline_priority"


def _priority(row: dict[str, Any]) -> tuple[int, str]:
    return (int(row.get("final_rank") or 10**6), str(row.get("symbol", "")))


def _normalize_operator_row(row: dict[str, Any], recommendation: dict[str, Any]) -> dict[str, Any]:
    symbol = str(row.get("symbol") or recommendation.get("symbol") or "")
    final_rank = row.get("final_rank", recommendation.get("final_rank", recommendation.get("rank")))
    final_score = row.get("final_ranking_score", recommendation.get("final_ranking_score", recommendation.get("score")))
    policy_materiality = row.get("policy_materiality", recommendation.get("policy_materiality", "none"))
    policy_decision = row.get("policy_decision", recommendation.get("policy_decision", "NEUTRAL"))
    policy_score_delta = recommendation.get("policy_score_delta", row.get("policy_score_delta", 0.0))
    reference_price = row.get("reference_price_krw", recommendation.get("reference_price_krw"))
    note = (
        "Policy contributes to this setup, but it was not decisive at the cutoff."
        if _policy_bucket({"policy_materiality": policy_materiality}) == "policy_assisted"
        else "Baseline scanner strength alone keeps this candidate inside the active cutoff."
    )
    return {
        "symbol": symbol,
        "final_rank": final_rank,
        "final_ranking_score": final_score,
        "policy_materiality": policy_materiality,
        "policy_decision": policy_decision,
        "policy_score_delta": policy_score_delta,
        "reference_price_krw": reference_price,
        "bucket": _policy_bucket({"policy_materiality": policy_materiality}),
        "note": note,
    }


def build_operator_watchlist(
    *,
    daily_summary: dict[str, Any],
    recommendations: list[dict[str, Any]],
    max_baseline: int = 5,
    max_policy_assisted: int = 5,
    max_recheck: int = 5,
) -> dict[str, Any]:
    snapshot_metadata = daily_summary.get("snapshot_metadata", {})
    counterfactual = list(snapshot_metadata.get("counterfactual_buys_without_market_filter", []))
    market_filter = snapshot_metadata.get("market_filter", {})
    recommendation_by_symbol = {
        str(row.get("symbol")): row for row in recommendations if row.get("symbol") is not None
    }

    normalized: list[dict[str, Any]] = []
    if market_filter.get("below_ema"):
        source_rows = counterfactual
    else:
        source_rows = [
            row
            for row in recommendations
            if str(row.get("action")) in {"BUY", "HOLD"}
            or str(row.get("policy_materiality")) in {"entry_reversal", "boosted_but_not_decisive", "near_miss"}
        ]

    for row in source_rows:
        symbol = str(row.get("symbol", ""))
        recommendation = recommendation_by_symbol.get(symbol, row if isinstance(row, dict) else {})
        normalized.append(_normalize_operator_row(row, recommendation))

    normalized.sort(key=_priority)
    baseline = [row for row in normalized if row["bucket"] == "baseline_priority"]
    assisted = [row for row in normalized if row["bucket"] == "policy_assisted"]
    recheck = normalized[: max(1, max_recheck)]

    if market_filter.get("below_ema"):
        headline = "Market filter is active; recheck these names first when the filter releases."
    elif normalized:
        headline = "Market filter is inactive; these are the strongest current operator watchlist names."
    else:
        headline = "No operator watchlist candidates are available from the latest snapshot."

    warnings = list(daily_summary.get("warnings", []))
    if market_filter.get("below_ema") and not normalized:
        warnings.append("Market filter is active, but no counterfactual top-cutoff candidates were produced.")

    return {
        "generated_at": daily_summary.get("generated_at"),
        "bundle_id": daily_summary.get("policy_snapshot", {}).get("bundle_id"),
        "strategy_id": daily_summary.get("strategy_snapshot", {}).get("strategy_id"),
        "headline": headline,
        "market_filter_active": bool(market_filter.get("below_ema")),
        "baseline_priority": baseline[: max(1, max_baseline)],
        "policy_assisted": assisted[: max(1, max_policy_assisted)],
        "recheck_on_filter_release": recheck,
        "warnings": list(dict.fromkeys(warnings)),
    }
