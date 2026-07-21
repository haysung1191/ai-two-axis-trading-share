from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))




ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_search_summary"


BRANCH_ROWS = [
    {
        "Branch": "equal_weight_no_mad_min4",
        "Track": "operational",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_more_robust_branch",
        "StructuralType": "reference_equal_weight",
    },
    {
        "Branch": "rule_breadth_risk_off",
        "Track": "operational",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_more_robust_branch",
        "StructuralType": "breadth_risk_off",
    },
    {
        "Branch": "rule_breadth_it_risk_off",
        "Track": "operational",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_more_robust_branch",
        "StructuralType": "it_risk_off",
    },
    {
        "Branch": "rule_breadth_it_us5_cap",
        "Track": "operational",
        "Stage": "mainline",
        "Outcome": "survivor",
        "OutcomeReason": "current_operational_baseline",
        "StructuralType": "us_position_cap",
    },
    {
        "Branch": "rule_sector_cap2",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_stronger_aggressive_branch",
        "StructuralType": "sector_cap2",
    },
    {
        "Branch": "rule_sector_cap2_breadth_risk_off",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_stronger_aggressive_branch",
        "StructuralType": "breadth_risk_off",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_risk_off",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_stronger_aggressive_branch",
        "StructuralType": "it_risk_off",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_cap",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_stronger_aggressive_branch",
        "StructuralType": "us_position_cap",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_risk_on",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_stronger_aggressive_branch",
        "StructuralType": "risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top2_risk_on",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_stronger_aggressive_branch",
        "StructuralType": "top2_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top2_convex_risk_on",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_ranked_tail_source_improvement",
        "StructuralType": "top2_convex_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_deeper_ranked_tail_branch",
        "StructuralType": "top2_convex_ranked_tail_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count4_floor35_risk_on",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_broader_ranked_tail_branch",
        "StructuralType": "top2_convex_ranked_tail_count4_floor35_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_floor40_risk_on",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_softer_ranked_tail_branch",
        "StructuralType": "top2_convex_ranked_tail_count5_floor40_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen55_floor35_risk_on",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_broader_softer_ranked_tail_branch",
        "StructuralType": "top2_convex_ranked_tail_count5_pen55_floor35_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen50_floor30_risk_on",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_deeper_softer_ranked_tail_branch",
        "StructuralType": "top2_convex_ranked_tail_count5_pen50_floor30_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_risk_on",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_higher_top_slice_bonus_branch",
        "StructuralType": "top2_convex_ranked_tail_count7_pen40_floor20_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_risk_on",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_curved_tail_penalty_branch",
        "StructuralType": "top2_convex_ranked_tail_count7_pen40_floor20_bonus18_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "retired",
        "OutcomeReason": "superseded_by_plateau_local_best_branch",
        "StructuralType": "top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on",
        "Track": "aggressive",
        "Stage": "mainline",
        "Outcome": "survivor",
        "OutcomeReason": "current_aggressive_strong_branch",
        "StructuralType": "top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on",
    },
    {
        "Branch": "hybrid_top2_plus_third01",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "broader_but_weaker_than_strongest",
        "StructuralType": "top2_plus_small_third_bonus",
    },
    {
        "Branch": "top2_split_49_51",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "micro_split_weaker_than_strongest",
        "StructuralType": "top2_internal_bonus_split",
    },
    {
        "Branch": "alt_family_top3_flat_bonus18",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "broader_family_too_weak_for_mainline",
        "StructuralType": "top3_flat_bonus_family",
    },
    {
        "Branch": "rule_sector_cap2_us5_cap",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "weaker_quality_metrics",
        "StructuralType": "remove_breadth_it_overlays",
    },
    {
        "Branch": "rule_sector_cap2_it_us5_cap",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "weaker_quality_metrics",
        "StructuralType": "remove_breadth_risk_off",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_mad",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "weaker_cagr_and_sharpe",
        "StructuralType": "mad_weighting",
    },
    {
        "Branch": "rule_sector_cap2_no_sector_filter_it_us5_cap",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "weaker_cagr_and_sharpe",
        "StructuralType": "remove_sector_filter",
    },
    {
        "Branch": "rule_sector_cap2_no_flow_it_us5_cap",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "weaker_cagr_and_sharpe",
        "StructuralType": "remove_flow_filter",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top1_country",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "over_concentrated_and_weaker",
        "StructuralType": "top1_country",
    },
    {
        "Branch": "rule_sector_cap1_breadth_it_us5_cap",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "too_restrictive_cagr_collapse",
        "StructuralType": "sector_cap1",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_turnover_risk_on",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "weaker_cagr_and_sharpe",
        "StructuralType": "turnover_conditioned_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_sector_leaders_risk_on",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "cagr_cost_too_high",
        "StructuralType": "sector_leaders_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_newhigh_risk_on",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "dominated_by_existing_risk_on",
        "StructuralType": "new_high_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_us_top2_risk_on",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "close_but_inferior",
        "StructuralType": "us_only_top2_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top1_risk_on",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "weak_period_and_concentration_penalty",
        "StructuralType": "top1_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top2_persist_risk_on",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "dominated_by_top2_risk_on",
        "StructuralType": "persistent_top2_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top3_risk_on",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "dominated_by_top2_risk_on",
        "StructuralType": "top3_risk_on",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_cross_sector_top2_risk_on",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "dominated_by_top2_risk_on",
        "StructuralType": "cross_sector_top2_risk_on",
    },
    {
        "Branch": "rule_sector_cap3_breadth_it_us5_top2_convex_risk_on",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "weaker_cagr_and_sharpe",
        "StructuralType": "sector_cap3",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_top2_convex_gross_risk_on",
        "Track": "aggressive",
        "Stage": "exploratory",
        "Outcome": "killed",
        "OutcomeReason": "micro_tuning_and_weaker_weak_period",
        "StructuralType": "gross_leverage_overlay",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_buffer4",
        "Track": "aggressive",
        "Stage": "cosmetic",
        "Outcome": "killed",
        "OutcomeReason": "effectively_identical",
        "StructuralType": "hold_buffer",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_selective_risk_on",
        "Track": "aggressive",
        "Stage": "cosmetic",
        "Outcome": "killed",
        "OutcomeReason": "effectively_identical",
        "StructuralType": "selective_risk_on_gate",
    },
    {
        "Branch": "rule_sector_cap2_breadth_it_us5_risk_on_momentum_weighted",
        "Track": "aggressive",
        "Stage": "cosmetic",
        "Outcome": "killed",
        "OutcomeReason": "effectively_identical",
        "StructuralType": "momentum_weighting",
    },
]


def _pct(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return float(numerator / denominator)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(BRANCH_ROWS)
    df = df.sort_values(["Track", "Stage", "Branch"]).reset_index(drop=True)
    df.to_csv(OUTPUT_DIR / "branch_inventory.csv", index=False, encoding="utf-8-sig")

    by_track = (
        df.groupby("Track")
        .agg(
            TotalBranches=("Branch", "count"),
            Survivors=("Outcome", lambda s: int((s == "survivor").sum())),
            RetiredMainline=("Outcome", lambda s: int((s == "retired").sum())),
            Killed=("Outcome", lambda s: int((s == "killed").sum())),
            Exploratory=("Stage", lambda s: int((s == "exploratory").sum())),
            Cosmetic=("Stage", lambda s: int((s == "cosmetic").sum())),
        )
        .reset_index()
    )
    by_track["SurvivorRate"] = [
        _pct(int(row.Survivors), int(row.TotalBranches)) for row in by_track.itertuples(index=False)
    ]
    by_track["KilledRate"] = [_pct(int(row.Killed), int(row.TotalBranches)) for row in by_track.itertuples(index=False)]
    by_track.to_csv(OUTPUT_DIR / "branch_search_summary_by_track.csv", index=False, encoding="utf-8-sig")

    by_reason = (
        df[df["Outcome"] == "killed"]
        .groupby("OutcomeReason")
        .agg(Branches=("Branch", "count"))
        .sort_values("Branches", ascending=False)
        .reset_index()
    )
    by_reason.to_csv(OUTPUT_DIR / "branch_search_kill_reasons.csv", index=False, encoding="utf-8-sig")

    overall = {
        "total_branches_documented": int(len(df)),
        "survivors": int((df["Outcome"] == "survivor").sum()),
        "retired_mainline": int((df["Outcome"] == "retired").sum()),
        "killed": int((df["Outcome"] == "killed").sum()),
        "exploratory_branches": int((df["Stage"] == "exploratory").sum()),
        "cosmetic_branches": int((df["Stage"] == "cosmetic").sum()),
        "aggressive_total": int((df["Track"] == "aggressive").sum()),
        "operational_total": int((df["Track"] == "operational").sum()),
        "aggressive_survivor_rate": _pct(
            int(((df["Track"] == "aggressive") & (df["Outcome"] == "survivor")).sum()),
            int((df["Track"] == "aggressive").sum()),
        ),
        "operational_survivor_rate": _pct(
            int(((df["Track"] == "operational") & (df["Outcome"] == "survivor")).sum()),
            int((df["Track"] == "operational").sum()),
        ),
    }
    (OUTPUT_DIR / "branch_search_summary.json").write_text(json.dumps(overall, indent=2), encoding="utf-8")
    print(json.dumps(overall, indent=2))


if __name__ == "__main__":
    main()


