from __future__ import annotations

from typing import Any


def build_policy_materiality_summary(
    *,
    recommendations: list[dict[str, Any]],
    snapshot_metadata: dict[str, Any],
) -> dict[str, Any]:
    counterfactual = list(snapshot_metadata.get("counterfactual_buys_without_market_filter", []))
    top_n = int(snapshot_metadata.get("top_n", 0) or 0)
    active_cutoff_rows = sorted(
        [
            row
            for row in recommendations
            if int(row.get("final_rank") or row.get("rank") or 10**6) <= max(0, top_n)
        ],
        key=lambda row: (
            int(row.get("final_rank") or row.get("rank") or 10**6),
            str(row.get("symbol", "")),
        ),
    )
    cutoff_rank = len(counterfactual) if counterfactual else max(0, top_n)
    cutoff_score = None
    if counterfactual:
        cutoff_score = float(counterfactual[min(len(counterfactual), cutoff_rank) - 1]["final_ranking_score"])
    elif active_cutoff_rows and cutoff_rank > 0:
        cutoff_score = float(
            active_cutoff_rows[min(len(active_cutoff_rows), cutoff_rank) - 1].get("final_ranking_score")
            or active_cutoff_rows[min(len(active_cutoff_rows), cutoff_rank) - 1].get("score")
            or 0.0
        )

    boosted_rows: list[dict[str, Any]] = []
    for row in recommendations:
        delta = float(row.get("policy_score_delta") or 0.0)
        if delta <= 0.0:
            continue
        final_score = float(row.get("final_ranking_score") or row.get("score") or 0.0)
        raw_score = float(row.get("scanner_score_before_policy") or (final_score - delta))
        final_rank = int(row.get("final_rank") or row.get("rank") or 10**6)
        raw_rank = int(row.get("raw_rank") or final_rank)
        gap_after_boost = None
        required_extra_delta = None
        if cutoff_score is not None:
            gap_after_boost = float(cutoff_score - final_score)
            required_extra_delta = max(0.0, gap_after_boost)
        boosted_rows.append(
            {
                "symbol": row.get("symbol"),
                "raw_rank": raw_rank,
                "final_rank": final_rank,
                "raw_score": raw_score,
                "final_score": final_score,
                "applied_delta": delta,
                "scheduled_due_to_policy": bool(row.get("scheduled_due_to_policy")),
                "near_miss_after_policy": bool(row.get("near_miss_after_policy")),
                "policy_materiality": (
                    row.get("policy_materiality")
                    if row.get("policy_materiality") not in (None, "", "none")
                    else "boosted_but_not_decisive"
                ),
                "final_decision": row.get("final_decision"),
                "gap_to_cutoff_after_boost": gap_after_boost,
                "required_extra_delta_for_cutoff": required_extra_delta,
            }
        )

    boosted_rows.sort(
        key=lambda item: (
            0 if item["scheduled_due_to_policy"] else 1,
            0 if item["near_miss_after_policy"] else 1,
            item["final_rank"],
            str(item["symbol"]),
        )
    )

    closest_candidates = [
        row
        for row in boosted_rows
        if row["required_extra_delta_for_cutoff"] is not None
        and (
            row["scheduled_due_to_policy"]
            or str(row.get("final_decision", "")) == "CANCELED:BELOW_ENTRY_CUTOFF"
            or bool(row["near_miss_after_policy"])
        )
    ]
    closest_candidates.sort(
        key=lambda item: (
            item["required_extra_delta_for_cutoff"],
            item["final_rank"],
            str(item["symbol"]),
        )
    )

    return {
        "boosted_candidate_count": len(boosted_rows),
        "cutoff_rank": cutoff_rank,
        "cutoff_score": cutoff_score,
        "direct_reversal_count": sum(bool(row["scheduled_due_to_policy"]) for row in boosted_rows),
        "near_miss_count": sum(bool(row["near_miss_after_policy"]) for row in boosted_rows),
        "boosted_candidates": boosted_rows,
        "closest_to_reversal": closest_candidates[:5],
    }
