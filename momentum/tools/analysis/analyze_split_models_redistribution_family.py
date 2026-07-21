from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_redistribution_family_review"

STRONGEST = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"
FAMILY_ROWS = [
    {
        "Variant": "tail_release_to_nonbottom_proportional",
        "Top2Share": 0.00,
        "MidShare": 1.00,
        "CAGR": 0.7094,
        "MDD": -0.3773,
        "Sharpe": 1.5096,
        "AnnualTurnover": 15.50,
        "Cost75BpsCAGRDeltaVsStrongest": 0.0700,
        "Cost75BpsSharpeDeltaVsStrongest": -0.1248,
        "WalkForwardPositive": 3,
        "WalkForwardNegative": 1,
        "WalkForwardSharpeDelta": -0.1515,
        "Top3PositiveSymbolShare": 0.3920,
        "ResidualExTop3": 0.0023,
    },
    {
        "Variant": "tail_release_top25_mid75",
        "Top2Share": 0.25,
        "MidShare": 0.75,
        "CAGR": 0.7555,
        "MDD": -0.3401,
        "Sharpe": 1.6951,
        "AnnualTurnover": 14.47,
        "Cost75BpsCAGRDeltaVsStrongest": 0.1222,
        "Cost75BpsSharpeDeltaVsStrongest": 0.0548,
        "WalkForwardPositive": 4,
        "WalkForwardNegative": 0,
        "WalkForwardSharpeDelta": 0.0457,
        "Top3PositiveSymbolShare": 0.4342,
        "ResidualExTop3": 0.0045,
    },
    {
        "Variant": "tail_release_top50_mid50",
        "Top2Share": 0.50,
        "MidShare": 0.50,
        "CAGR": 0.7647,
        "MDD": -0.3464,
        "Sharpe": 1.6967,
        "AnnualTurnover": 14.41,
        "Cost75BpsCAGRDeltaVsStrongest": 0.1313,
        "Cost75BpsSharpeDeltaVsStrongest": 0.0593,
        "WalkForwardPositive": 4,
        "WalkForwardNegative": 0,
        "WalkForwardSharpeDelta": 0.0503,
        "Top3PositiveSymbolShare": 0.4374,
        "ResidualExTop3": 0.0050,
    },
    {
        "Variant": "tail_rescue_bestflow_if_above_median",
        "Top2Share": 0.50,
        "MidShare": 0.50,
        "CAGR": 0.7622,
        "MDD": -0.3492,
        "Sharpe": 1.6909,
        "AnnualTurnover": 14.45,
        "Cost75BpsCAGRDeltaVsStrongest": 0.1287,
        "Cost75BpsSharpeDeltaVsStrongest": 0.0535,
        "WalkForwardPositive": 4,
        "WalkForwardNegative": 0,
        "WalkForwardSharpeDelta": 0.0457,
        "Top3PositiveSymbolShare": 0.4399,
        "ResidualExTop3": 0.0049,
    },
]


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _pct_point(value: float) -> str:
    return f"{value * 100:.2f}%p"


def _build_summary() -> dict:
    best_headline = max(FAMILY_ROWS, key=lambda row: row["CAGR"])
    best_quality = max(FAMILY_ROWS, key=lambda row: row["Sharpe"])
    best_drawdown = max(FAMILY_ROWS, key=lambda row: row["MDD"])
    best_blended = next(row for row in FAMILY_ROWS if row["Variant"] == "tail_release_top50_mid50")

    return {
        "strongest_variant": STRONGEST,
        "family": "tail_release_redistribution_sweep",
        "best_headline_point": best_headline["Variant"],
        "best_quality_point": best_quality["Variant"],
        "best_drawdown_point": best_drawdown["Variant"],
        "best_blended_point": best_blended["Variant"],
        "family_takeaway": (
            "moving released tail weight from broad non-bottom redistribution toward a partial top2 mix "
            "improves Sharpe, turnover, walk-forward, and cost, while tail-rescue variants land in almost the "
            "same saturation zone; the whole family still fails promotion because drawdown remains too weak"
        ),
        "rows": [
            {
                "variant": row["Variant"],
                "top2_share": _pct(row["Top2Share"]),
                "mid_share": _pct(row["MidShare"]),
                "cagr": _pct(row["CAGR"]),
                "mdd": _pct(row["MDD"]),
                "sharpe": f"{row['Sharpe']:.4f}",
                "annual_turnover": f"{row['AnnualTurnover']:.2f}",
                "cost_75bps_cagr_delta_vs_strongest": _pct_point(row["Cost75BpsCAGRDeltaVsStrongest"]),
                "cost_75bps_sharpe_delta_vs_strongest": f"{row['Cost75BpsSharpeDeltaVsStrongest']:+.4f}",
                "walkforward": f"{row['WalkForwardPositive']} positive / {row['WalkForwardNegative']} negative",
                "walkforward_sharpe_delta": f"{row['WalkForwardSharpeDelta']:+.4f}",
                "top3_positive_symbol_share": _pct(row["Top3PositiveSymbolShare"]),
                "residual_ex_top3": _pct_point(row["ResidualExTop3"]),
            }
            for row in FAMILY_ROWS
        ],
    }


def _build_markdown(summary: dict) -> str:
    rows = {row["variant"]: row for row in summary["rows"]}
    best_headline = rows[summary["best_headline_point"]]
    best_quality = rows[summary["best_quality_point"]]
    best_drawdown = rows[summary["best_drawdown_point"]]
    best_blended = rows[summary["best_blended_point"]]

    return "\n".join(
        [
            "# Split Models Redistribution Family Review",
            "",
            "## Scope",
            "",
            "- freeze the validated tail-release redistribution family in one place",
            f"- strongest reference: `{STRONGEST}`",
            "- reviewed family points:",
            "  - `top0 / mid100`",
            "  - `top25 / mid75`",
            "  - `top50 / mid50`",
            "  - `tail rescue best-flow`",
            "",
            "## Family Pattern",
            "",
            "- all reviewed redistribution points produce much higher headline CAGR than the strongest",
            "- adding some top2 share improves Sharpe, cost response, and turnover materially",
            "- the tail-rescue variant lands in almost the same zone as `top50 / mid50`, not in a separate family frontier",
            "- the family stays non-promotable because drawdown remains too weak even at the best blended point",
            "",
            "## Best Headline Point",
            "",
            f"- variant: `{summary['best_headline_point']}`",
            f"- CAGR: `{best_headline['cagr']}`",
            f"- MDD: `{best_headline['mdd']}`",
            f"- Sharpe: `{best_headline['sharpe']}`",
            f"- walk-forward: `{best_headline['walkforward']}`",
            f"- `75 bps` cost CAGR delta vs strongest: `{best_headline['cost_75bps_cagr_delta_vs_strongest']}`",
            "",
            "## Best Quality Point",
            "",
            f"- variant: `{summary['best_quality_point']}`",
            f"- CAGR: `{best_quality['cagr']}`",
            f"- MDD: `{best_quality['mdd']}`",
            f"- Sharpe: `{best_quality['sharpe']}`",
            f"- walk-forward: `{best_quality['walkforward']}`",
            f"- walk-forward Sharpe delta: `{best_quality['walkforward_sharpe_delta']}`",
            "",
            "## Best Drawdown Point",
            "",
            f"- variant: `{summary['best_drawdown_point']}`",
            f"- CAGR: `{best_drawdown['cagr']}`",
            f"- MDD: `{best_drawdown['mdd']}`",
            f"- Sharpe: `{best_drawdown['sharpe']}`",
            f"- walk-forward: `{best_drawdown['walkforward']}`",
            "",
            "## Best Blended Point",
            "",
            f"- variant: `{summary['best_blended_point']}`",
            f"- CAGR: `{best_blended['cagr']}`",
            f"- MDD: `{best_blended['mdd']}`",
            f"- Sharpe: `{best_blended['sharpe']}`",
            f"- Annual turnover: `{best_blended['annual_turnover']}`",
            f"- walk-forward: `{best_blended['walkforward']}`",
            f"- `75 bps` cost CAGR delta vs strongest: `{best_blended['cost_75bps_cagr_delta_vs_strongest']}`",
            f"- `75 bps` cost Sharpe delta vs strongest: `{best_blended['cost_75bps_sharpe_delta_vs_strongest']}`",
            "",
            "## Interpretation",
            "",
            "- `top0 / mid100` is the raw boundary point: very strong headline, but quality collapses too much",
            "- `top25 / mid75` improves quality a lot while keeping very strong headline support",
            "- `top50 / mid50` is the best blended redistribution point because Sharpe, walk-forward, cost, and turnover all remain strong",
            "- `tail_rescue_bestflow_if_above_median` is effectively a redistribution saturation variant: it stays very close to `top50 / mid50` but does not beat it on any major axis",
            "- even `top50 / mid50` still fails promotion grade because drawdown deterioration is too large",
            "",
            "## Verdict",
            "",
            "- keep `tail_release_top50_mid50` as the redistribution-family current truth",
            "- treat the whole redistribution family as a strong but non-promotable aggressive frontier",
            "- stop re-litigating this family unless a new drawdown-control axis is introduced",
            "",
        ]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = _build_summary()

    compare_csv = (
        "Variant,Top2Share,MidShare,CAGR,MDD,Sharpe,AnnualTurnover,"
        "Cost75BpsCAGRDeltaVsStrongest,Cost75BpsSharpeDeltaVsStrongest,"
        "WalkForwardPositive,WalkForwardNegative,WalkForwardSharpeDelta,"
        "Top3PositiveSymbolShare,ResidualExTop3\n"
    )
    for row in FAMILY_ROWS:
        compare_csv += (
            f"{row['Variant']},{row['Top2Share']},{row['MidShare']},{row['CAGR']},{row['MDD']},"
            f"{row['Sharpe']},{row['AnnualTurnover']},{row['Cost75BpsCAGRDeltaVsStrongest']},"
            f"{row['Cost75BpsSharpeDeltaVsStrongest']},{row['WalkForwardPositive']},"
            f"{row['WalkForwardNegative']},{row['WalkForwardSharpeDelta']},"
            f"{row['Top3PositiveSymbolShare']},{row['ResidualExTop3']}\n"
        )

    (OUTPUT_DIR / "redistribution_family_compare.csv").write_text(compare_csv, encoding="utf-8-sig")
    (OUTPUT_DIR / "redistribution_family_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "redistribution_family_review.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
