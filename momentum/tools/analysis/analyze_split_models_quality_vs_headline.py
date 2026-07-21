from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_quality_vs_headline_review"

STRONGEST = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"
QUALITY_NEAR_MISS = "bonus_recipient_top1_third_85_15"
SKIP_ENTRY_NEAR_MISS = "tail_skip_entry_flowweakest_new_bottom4_top25_mid75"
RISK_OFF_STRENGTH_NEAR_MISS = "risk_off_strength_breadth080"

ROWS = [
    {
        "Variant": STRONGEST,
        "CAGR": 0.6316,
        "MDD": -0.2927,
        "Sharpe": 1.6892,
        "AnnualTurnover": 15.32,
        "Cost75BpsCAGRDelta": 0.0,
        "PositiveCAGRWindows": 0,
        "NegativeCAGRWindows": 0,
        "Top3PositiveSymbolShare": 0.0,
        "CAGRDeltaVsStrongest": 0.0,
        "MDDDeltaVsStrongest": 0.0,
        "SharpeDeltaVsStrongest": 0.0,
    },
    {
        "Variant": QUALITY_NEAR_MISS,
        "CAGR": 0.6543,
        "MDD": -0.2952,
        "Sharpe": 1.6927,
        "AnnualTurnover": 15.81,
        "Cost75BpsCAGRDelta": 0.0168,
        "PositiveCAGRWindows": 3,
        "NegativeCAGRWindows": 1,
        "Top3PositiveSymbolShare": 0.4958,
        "CAGRDeltaVsStrongest": 0.0227,
        "MDDDeltaVsStrongest": -0.0025,
        "SharpeDeltaVsStrongest": 0.0035,
    },
    {
        "Variant": SKIP_ENTRY_NEAR_MISS,
        "CAGR": 0.6321,
        "MDD": -0.2877,
        "Sharpe": 1.6625,
        "AnnualTurnover": 14.73,
        "Cost75BpsCAGRDelta": 0.0053,
        "PositiveCAGRWindows": 3,
        "NegativeCAGRWindows": 1,
        "Top3PositiveSymbolShare": 0.4904,
        "CAGRDeltaVsStrongest": 0.0006,
        "MDDDeltaVsStrongest": 0.0051,
        "SharpeDeltaVsStrongest": -0.0268,
    },
    {
        "Variant": RISK_OFF_STRENGTH_NEAR_MISS,
        "CAGR": 0.6350,
        "MDD": -0.2995,
        "Sharpe": 1.6847,
        "AnnualTurnover": 15.57,
        "Cost75BpsCAGRDelta": 0.0012,
        "PositiveCAGRWindows": 3,
        "NegativeCAGRWindows": 1,
        "Top3PositiveSymbolShare": 0.4655,
        "CAGRDeltaVsStrongest": 0.0034,
        "MDDDeltaVsStrongest": -0.0068,
        "SharpeDeltaVsStrongest": -0.0046,
    },
]


def _pct_point(value: float) -> str:
    return f"{value * 100:.2f}%p"


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _build_summary() -> dict:
    strongest = next(row for row in ROWS if row["Variant"] == STRONGEST)
    quality = next(row for row in ROWS if row["Variant"] == QUALITY_NEAR_MISS)
    skip_entry = next(row for row in ROWS if row["Variant"] == SKIP_ENTRY_NEAR_MISS)
    risk_off = next(row for row in ROWS if row["Variant"] == RISK_OFF_STRENGTH_NEAR_MISS)

    summary = {
        "strongest_variant": STRONGEST,
        "quality_near_miss_variant": QUALITY_NEAR_MISS,
        "skip_entry_near_miss_variant": SKIP_ENTRY_NEAR_MISS,
        "risk_off_strength_near_miss_variant": RISK_OFF_STRENGTH_NEAR_MISS,
        "headline_leader": max(ROWS, key=lambda row: row["CAGR"])["Variant"],
        "quality_leader": max(ROWS, key=lambda row: row["Sharpe"])["Variant"],
        "lowest_turnover_variant": min(ROWS, key=lambda row: row["AnnualTurnover"])["Variant"],
        "quality_vs_headline_takeaway": (
            "skip-entry near miss is the best headline extension, "
            "risk-off-strength near miss is the closest defensive headline-ish extension, "
            "quality near miss is the best quality extension, "
            "and the strongest remains the only balanced promotion-grade branch"
        ),
        "rows": [
            {
                "variant": str(row["Variant"]),
                "cagr": _pct(float(row["CAGR"])),
                "mdd": _pct(float(row["MDD"])),
                "sharpe": f"{float(row['Sharpe']):.4f}",
                "annual_turnover": f"{float(row['AnnualTurnover']):.2f}",
                "cost_75bps_cagr_delta_vs_strongest": _pct_point(float(row["Cost75BpsCAGRDelta"])),
                "walkforward": f"{int(row['PositiveCAGRWindows'])} positive / {int(row['NegativeCAGRWindows'])} negative",
                "top3_positive_symbol_share": _pct(float(row["Top3PositiveSymbolShare"])),
            }
            for row in ROWS
        ],
        "quality_near_miss_delta_vs_strongest": {
            "cagr_delta": _pct_point(float(quality["CAGRDeltaVsStrongest"])),
            "mdd_delta": _pct_point(float(quality["MDDDeltaVsStrongest"])),
            "sharpe_delta": f"{float(quality['SharpeDeltaVsStrongest']):+.4f}",
            "cost_75bps_cagr_delta": _pct_point(float(quality["Cost75BpsCAGRDelta"])),
        },
        "skip_entry_near_miss_delta_vs_strongest": {
            "cagr_delta": _pct_point(float(skip_entry["CAGRDeltaVsStrongest"])),
            "mdd_delta": _pct_point(float(skip_entry["MDDDeltaVsStrongest"])),
            "sharpe_delta": f"{float(skip_entry['SharpeDeltaVsStrongest']):+.4f}",
            "cost_75bps_cagr_delta": _pct_point(float(skip_entry["Cost75BpsCAGRDelta"])),
        },
        "risk_off_strength_near_miss_delta_vs_strongest": {
            "cagr_delta": _pct_point(float(risk_off["CAGRDeltaVsStrongest"])),
            "mdd_delta": _pct_point(float(risk_off["MDDDeltaVsStrongest"])),
            "sharpe_delta": f"{float(risk_off['SharpeDeltaVsStrongest']):+.4f}",
            "cost_75bps_cagr_delta": _pct_point(float(risk_off["Cost75BpsCAGRDelta"])),
        },
    }
    return summary


def _build_markdown(summary: dict) -> str:
    rows = {row["variant"]: row for row in summary["rows"]}
    quality = rows[QUALITY_NEAR_MISS]
    skip_entry = rows[SKIP_ENTRY_NEAR_MISS]
    risk_off = rows[RISK_OFF_STRENGTH_NEAR_MISS]
    return "\n".join(
        [
            "# Split Models Quality vs Headline Review",
            "",
            "## Scope",
            "",
            "- compare the current strongest against two different near-miss directions",
            "- strongest:",
            f"  - `{STRONGEST}`",
            "- quality near-miss:",
            f"  - `{QUALITY_NEAR_MISS}`",
            "- skip-entry near-miss:",
            f"  - `{SKIP_ENTRY_NEAR_MISS}`",
            "- risk-off-strength near-miss:",
            f"  - `{RISK_OFF_STRENGTH_NEAR_MISS}`",
            "",
            "## Result",
            "",
            f"- headline leader: `{summary['headline_leader']}`",
            f"- quality leader: `{summary['quality_leader']}`",
            f"- lowest turnover variant: `{summary['lowest_turnover_variant']}`",
            "",
            "## Quality Near-Miss",
            "",
            f"- CAGR: `{quality['cagr']}`",
            f"- MDD: `{quality['mdd']}`",
            f"- Sharpe: `{quality['sharpe']}`",
            f"- Annual turnover: `{quality['annual_turnover']}`",
            f"- `75 bps` cost CAGR delta vs strongest: `{quality['cost_75bps_cagr_delta_vs_strongest']}`",
            f"- walk-forward: `{quality['walkforward']}`",
            f"- top 3 positive symbol share: `{quality['top3_positive_symbol_share']}`",
            "",
            "## Skip-Entry Near-Miss",
            "",
            f"- CAGR: `{skip_entry['cagr']}`",
            f"- MDD: `{skip_entry['mdd']}`",
            f"- Sharpe: `{skip_entry['sharpe']}`",
            f"- Annual turnover: `{skip_entry['annual_turnover']}`",
            f"- `75 bps` cost CAGR delta vs strongest: `{skip_entry['cost_75bps_cagr_delta_vs_strongest']}`",
            f"- walk-forward: `{skip_entry['walkforward']}`",
            f"- top 3 positive symbol share: `{skip_entry['top3_positive_symbol_share']}`",
            "",
            "## Risk-Off-Strength Near-Miss",
            "",
            f"- CAGR: `{risk_off['cagr']}`",
            f"- MDD: `{risk_off['mdd']}`",
            f"- Sharpe: `{risk_off['sharpe']}`",
            f"- Annual turnover: `{risk_off['annual_turnover']}`",
            f"- `75 bps` cost CAGR delta vs strongest: `{risk_off['cost_75bps_cagr_delta_vs_strongest']}`",
            f"- walk-forward: `{risk_off['walkforward']}`",
            f"- top 3 positive symbol share: `{risk_off['top3_positive_symbol_share']}`",
            "",
            "## Interpretation",
            "",
            "- `bonus_recipient_top1_third_85_15` is the best blended quality extension",
            "  - CAGR improves even more",
            "  - walk-forward stays at `3-1` and cost stays positive",
            "  - but drawdown is slightly worse and turnover still rises",
            "- `tail_skip_entry_flowweakest_new_bottom4_top25_mid75` is the best headline extension",
            "  - CAGR and turnover improve together",
            "  - but Sharpe still stays materially below the strongest",
            "- `risk_off_strength_breadth080` is the closest defensive headline-ish extension",
            "  - CAGR is slightly above the strongest",
            "  - but drawdown gets worse and Sharpe still slips",
            "- the strongest remains the only branch that stays balanced enough across headline, quality, and promotion robustness",
            "",
            "## Verdict",
            "",
            "- keep the current strongest as the single aggressive mainline branch",
            "- treat the quality near-miss as the best quality-tilted alternative",
            "- treat the skip-entry near-miss as the best headline-tilted alternative",
            "- treat the risk-off-strength near-miss as a defensive headline-ish alternative, not a promotion",
            "- do not promote either near-miss without solving their remaining quality gap",
            "",
        ]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = _build_summary()
    rows = json.loads(json.dumps(ROWS))
    compare_csv = "Variant,CAGR,MDD,Sharpe,AnnualTurnover,Cost75BpsCAGRDelta,PositiveCAGRWindows,NegativeCAGRWindows,Top3PositiveSymbolShare,CAGRDeltaVsStrongest,MDDDeltaVsStrongest,SharpeDeltaVsStrongest\n"
    for row in rows:
        compare_csv += (
            f"{row['Variant']},{row['CAGR']},{row['MDD']},{row['Sharpe']},{row['AnnualTurnover']},"
            f"{row['Cost75BpsCAGRDelta']},{row['PositiveCAGRWindows']},{row['NegativeCAGRWindows']},"
            f"{row['Top3PositiveSymbolShare']},{row['CAGRDeltaVsStrongest']},{row['MDDDeltaVsStrongest']},{row['SharpeDeltaVsStrongest']}\n"
        )
    (OUTPUT_DIR / "quality_vs_headline_compare.csv").write_text(compare_csv, encoding="utf-8-sig")
    (OUTPUT_DIR / "quality_vs_headline_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "quality_vs_headline_review.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
