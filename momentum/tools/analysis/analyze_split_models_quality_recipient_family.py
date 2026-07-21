from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_quality_recipient_family_review"

STRONGEST = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"
FAMILY_ROWS = [
    {
        "Variant": "bonus_recipient_top1_third_67_33",
        "Top1Share": 0.67,
        "Top3Share": 0.33,
        "CAGR": 0.6321,
        "MDD": -0.2909,
        "Sharpe": 1.7018,
        "AnnualTurnover": 15.94,
        "Cost75BpsCAGRDeltaVsStrongest": -0.0046,
        "WalkForwardPositive": 2,
        "WalkForwardNegative": 2,
        "WalkForwardSharpeDelta": 0.0044,
        "Top3PositiveSymbolShare": 0.3509,
        "ResidualExTop3": 0.0006,
    },
    {
        "Variant": "bonus_recipient_top1_third_75_25",
        "Top1Share": 0.75,
        "Top3Share": 0.25,
        "CAGR": 0.6420,
        "MDD": -0.2928,
        "Sharpe": 1.6982,
        "AnnualTurnover": 15.87,
        "Cost75BpsCAGRDeltaVsStrongest": 0.0050,
        "WalkForwardPositive": 2,
        "WalkForwardNegative": 2,
        "WalkForwardSharpeDelta": -0.0026,
        "Top3PositiveSymbolShare": 0.4046,
        "ResidualExTop3": 0.0018,
    },
    {
        "Variant": "bonus_recipient_top1_third_80_20",
        "Top1Share": 0.80,
        "Top3Share": 0.20,
        "CAGR": 0.6482,
        "MDD": -0.2940,
        "Sharpe": 1.6956,
        "AnnualTurnover": 15.84,
        "Cost75BpsCAGRDeltaVsStrongest": 0.0109,
        "WalkForwardPositive": 3,
        "WalkForwardNegative": 1,
        "WalkForwardSharpeDelta": -0.0074,
        "Top3PositiveSymbolShare": 0.4537,
        "ResidualExTop3": 0.0026,
    },
    {
        "Variant": "bonus_recipient_top1_third_85_15",
        "Top1Share": 0.85,
        "Top3Share": 0.15,
        "CAGR": 0.6543,
        "MDD": -0.2952,
        "Sharpe": 1.6927,
        "AnnualTurnover": 15.81,
        "Cost75BpsCAGRDeltaVsStrongest": 0.0168,
        "WalkForwardPositive": 3,
        "WalkForwardNegative": 1,
        "WalkForwardSharpeDelta": -0.0124,
        "Top3PositiveSymbolShare": 0.4958,
        "ResidualExTop3": 0.0033,
    },
    {
        "Variant": "bonus_recipient_top1_third_90_10",
        "Top1Share": 0.90,
        "Top3Share": 0.10,
        "CAGR": 0.6603,
        "MDD": -0.2965,
        "Sharpe": 1.6896,
        "AnnualTurnover": 15.78,
        "Cost75BpsCAGRDeltaVsStrongest": 0.0226,
        "WalkForwardPositive": 3,
        "WalkForwardNegative": 1,
        "WalkForwardSharpeDelta": -0.0176,
        "Top3PositiveSymbolShare": 0.5335,
        "ResidualExTop3": 0.0040,
    },
]


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _pct_point(value: float) -> str:
    return f"{value * 100:.2f}%p"


def _build_summary() -> dict:
    best_quality = max(FAMILY_ROWS, key=lambda row: row["Sharpe"])
    best_headline = max(FAMILY_ROWS, key=lambda row: row["CAGR"])
    best_blended = next(row for row in FAMILY_ROWS if row["Variant"] == "bonus_recipient_top1_third_85_15")

    return {
        "strongest_variant": STRONGEST,
        "family": "bonus_recipient_top1_third_sweep",
        "best_quality_point": best_quality["Variant"],
        "best_blended_point": best_blended["Variant"],
        "best_headline_point": best_headline["Variant"],
        "family_takeaway": (
            "moving from 67/33 toward 90/10 keeps increasing headline CAGR, "
            "but walk-forward Sharpe robustness weakens; 85/15 is the best blended point"
        ),
        "rows": [
            {
                "variant": row["Variant"],
                "top1_share": _pct(row["Top1Share"]),
                "top3_share": _pct(row["Top3Share"]),
                "cagr": _pct(row["CAGR"]),
                "mdd": _pct(row["MDD"]),
                "sharpe": f"{row['Sharpe']:.4f}",
                "annual_turnover": f"{row['AnnualTurnover']:.2f}",
                "cost_75bps_cagr_delta_vs_strongest": _pct_point(row["Cost75BpsCAGRDeltaVsStrongest"]),
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
    best_quality = rows[summary["best_quality_point"]]
    best_blended = rows[summary["best_blended_point"]]
    best_headline = rows[summary["best_headline_point"]]

    return "\n".join(
        [
            "# Split Models Quality Recipient Family Review",
            "",
            "## Scope",
            "",
            "- freeze the validated `top1 / top3` bonus-recipient family in one place",
            f"- strongest reference: `{STRONGEST}`",
            "- reviewed family points:",
            "  - `67 / 33`",
            "  - `75 / 25`",
            "  - `80 / 20`",
            "  - `85 / 15`",
            "  - `90 / 10`",
            "",
            "## Family Pattern",
            "",
            "- moving from `67 / 33` toward `90 / 10` increases raw CAGR steadily",
            "- the same move also pushes walk-forward Sharpe robustness lower",
            "- concentration rises as the split becomes more top1-heavy",
            "- the family does not produce a promotion-grade strongest replacement",
            "",
            "## Best Quality Point",
            "",
            f"- variant: `{summary['best_quality_point']}`",
            f"- CAGR: `{best_quality['cagr']}`",
            f"- MDD: `{best_quality['mdd']}`",
            f"- Sharpe: `{best_quality['sharpe']}`",
            f"- walk-forward: `{best_quality['walkforward']}`",
            f"- `75 bps` cost CAGR delta vs strongest: `{best_quality['cost_75bps_cagr_delta_vs_strongest']}`",
            "",
            "## Best Blended Point",
            "",
            f"- variant: `{summary['best_blended_point']}`",
            f"- CAGR: `{best_blended['cagr']}`",
            f"- MDD: `{best_blended['mdd']}`",
            f"- Sharpe: `{best_blended['sharpe']}`",
            f"- walk-forward: `{best_blended['walkforward']}`",
            f"- walk-forward Sharpe delta: `{best_blended['walkforward_sharpe_delta']}`",
            f"- `75 bps` cost CAGR delta vs strongest: `{best_blended['cost_75bps_cagr_delta_vs_strongest']}`",
            "",
            "## Best Headline Point",
            "",
            f"- variant: `{summary['best_headline_point']}`",
            f"- CAGR: `{best_headline['cagr']}`",
            f"- MDD: `{best_headline['mdd']}`",
            f"- Sharpe: `{best_headline['sharpe']}`",
            f"- walk-forward: `{best_headline['walkforward']}`",
            f"- walk-forward Sharpe delta: `{best_headline['walkforward_sharpe_delta']}`",
            f"- `75 bps` cost CAGR delta vs strongest: `{best_headline['cost_75bps_cagr_delta_vs_strongest']}`",
            "",
            "## Interpretation",
            "",
            "- `67/33` is the best pure quality point, but it gives up too much headline strength",
            "- `85/15` is the best blended point because it keeps the strongest mix of CAGR, cost support, and still-reasonable robustness",
            "- `90/10` is the headline boundary point: stronger raw CAGR, but weaker robustness than `85/15`",
            "",
            "## Verdict",
            "",
            "- keep `bonus_recipient_top1_third_85_15` as the quality/blended near-miss current truth",
            "- stop re-litigating this family unless a new validation axis is introduced",
            "- move future search effort to a different family rather than pushing `top1 / top3` more aggressively",
            "",
        ]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = _build_summary()

    compare_csv = (
        "Variant,Top1Share,Top3Share,CAGR,MDD,Sharpe,AnnualTurnover,"
        "Cost75BpsCAGRDeltaVsStrongest,WalkForwardPositive,WalkForwardNegative,"
        "WalkForwardSharpeDelta,Top3PositiveSymbolShare,ResidualExTop3\n"
    )
    for row in FAMILY_ROWS:
        compare_csv += (
            f"{row['Variant']},{row['Top1Share']},{row['Top3Share']},{row['CAGR']},{row['MDD']},"
            f"{row['Sharpe']},{row['AnnualTurnover']},{row['Cost75BpsCAGRDeltaVsStrongest']},"
            f"{row['WalkForwardPositive']},{row['WalkForwardNegative']},{row['WalkForwardSharpeDelta']},"
            f"{row['Top3PositiveSymbolShare']},{row['ResidualExTop3']}\n"
        )

    (OUTPUT_DIR / "quality_recipient_family_compare.csv").write_text(compare_csv, encoding="utf-8-sig")
    (OUTPUT_DIR / "quality_recipient_family_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "quality_recipient_family_review.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
