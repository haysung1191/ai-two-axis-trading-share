from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
FRONTIER_CSV = ROOT / "output" / "split_models_tradeoff_frontier_review" / "tradeoff_frontier_compare.csv"
BASELINE_SUMMARY_JSON = ROOT / "output" / "split_models_backtest" / "split_models_backtest_summary.json"
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_candidates"

BASELINE_VARIANT = "rule_breadth_it_us5_cap"
STRONGEST_VARIANT = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"
NEAR_MISS_VARIANTS = [
    "hybrid_top2_plus_third00125",
    "bonus_recipient_top1_third_85_15",
    "tail_skip_entry_flowweakest_new_bottom4_top25_mid75",
    "regime_weight_defensive_if_top2flowsoft",
    "multi_step_confirm_top1_flowtop2",
    "tail_release_top50_mid50",
]


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _load_frontier_rows() -> list[dict[str, str]]:
    with FRONTIER_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _load_baseline_summary() -> dict:
    return json.loads(BASELINE_SUMMARY_JSON.read_text(encoding="utf-8"))


def _score_candidate(row: dict[str, float], baseline: dict[str, float]) -> tuple[float, list[str]]:
    notes: list[str] = []
    score = 0.0

    cagr_delta_vs_baseline = row["CAGR"] - baseline["CAGR"]
    sharpe_delta_vs_baseline = row["Sharpe"] - baseline["Sharpe"]
    mdd_gap_vs_baseline = abs(row["MDD"]) - abs(baseline["MDD"])
    turnover_gap_vs_baseline = row["AnnualTurnover"] - baseline["AnnualTurnover"]

    score += cagr_delta_vs_baseline * 100.0 * 0.8
    score += sharpe_delta_vs_baseline * 120.0
    score += row["PositiveCAGRWindows"] * 2.0
    score -= row["NegativeCAGRWindows"] * 4.0
    score += row["Cost75BpsCAGRDelta"] * 100.0 * 0.5
    score -= max(0.0, mdd_gap_vs_baseline) * 100.0 * 3.0
    score -= max(0.0, turnover_gap_vs_baseline) * 0.6
    score -= row["Top3PositiveSymbolShare"] * 12.0
    score += row["ResidualExTop3"] * 100.0 * 1.5

    if cagr_delta_vs_baseline > 0:
        notes.append(f"headline stronger than baseline by {_pct(cagr_delta_vs_baseline)}")
    else:
        notes.append(f"headline weaker than baseline by {_pct(-cagr_delta_vs_baseline)}")

    if sharpe_delta_vs_baseline > 0:
        notes.append(f"Sharpe stronger than baseline by {sharpe_delta_vs_baseline:+.4f}")
    else:
        notes.append(f"Sharpe weaker than baseline by {sharpe_delta_vs_baseline:+.4f}")

    if mdd_gap_vs_baseline <= 0:
        notes.append(f"drawdown no worse than baseline by {_pct(-mdd_gap_vs_baseline)}")
    else:
        notes.append(f"drawdown worse than baseline by {_pct(mdd_gap_vs_baseline)}")

    if row["NegativeCAGRWindows"] == 0:
        notes.append("no negative walk-forward CAGR windows")
    else:
        notes.append(f"{row['NegativeCAGRWindows']:.0f} negative walk-forward CAGR windows")

    if row["Cost75BpsCAGRDelta"] > 0:
        notes.append(f"still ahead of strongest at 75 bps by {_pct(row['Cost75BpsCAGRDelta'])}")
    else:
        notes.append(f"behind strongest at 75 bps by {_pct(-row['Cost75BpsCAGRDelta'])}")

    if row["Top3PositiveSymbolShare"] >= 0.70:
        notes.append("too concentrated for easy operating conversion")
    elif row["Top3PositiveSymbolShare"] >= 0.50:
        notes.append("concentration still elevated")
    else:
        notes.append("concentration looks more convertible")

    return score, notes


def _build_summary() -> dict:
    baseline_summary = _load_baseline_summary()["trading_book"]
    rows = _load_frontier_rows()
    chosen = [row for row in rows if row["Variant"] in {STRONGEST_VARIANT, *NEAR_MISS_VARIANTS}]

    parsed_rows = []
    reference_row: dict | None = None
    for row in chosen:
        parsed = {
            "Variant": row["Variant"],
            "CAGR": float(row["CAGR"]),
            "MDD": float(row["MDD"]),
            "Sharpe": float(row["Sharpe"]),
            "AnnualTurnover": float(row["AnnualTurnover"]),
            "PositiveCAGRWindows": float(row["PositiveCAGRWindows"]),
            "NegativeCAGRWindows": float(row["NegativeCAGRWindows"]),
            "Cost75BpsCAGRDelta": float(row["Cost75BpsCAGRDelta"]),
            "AvgMonthlyDelta": float(row["AvgMonthlyDelta"]),
            "ResidualExTop3": float(row["ResidualExTop3"]),
            "Top3PositiveSymbolShare": float(row["Top3PositiveSymbolShare"]),
        }
        if parsed["Variant"] == STRONGEST_VARIANT:
            reference_row = {
                "variant": parsed["Variant"],
                "conversion_score": None,
                "conversion_grade": "reference",
                "cagr": parsed["CAGR"],
                "mdd": parsed["MDD"],
                "sharpe": parsed["Sharpe"],
                "annual_turnover": parsed["AnnualTurnover"],
                "positive_cagr_windows": int(parsed["PositiveCAGRWindows"]),
                "negative_cagr_windows": int(parsed["NegativeCAGRWindows"]),
                "cost_75bps_cagr_delta_vs_strongest": parsed["Cost75BpsCAGRDelta"],
                "avg_monthly_delta_vs_strongest": parsed["AvgMonthlyDelta"],
                "residual_ex_top3": parsed["ResidualExTop3"],
                "top3_positive_symbol_share": None,
                "notes": [
                    "current aggressive strongest reference branch",
                    "not scored as an operating-conversion candidate inside this ranking",
                    "frontier file stores self-relative fragility fields as zero, so candidate ranking excludes it",
                ],
            }
            continue

        score, notes = _score_candidate(parsed, baseline_summary)
        conversion_grade = "monitor"
        if (
            parsed["CAGR"] > baseline_summary["CAGR"]
            and parsed["Sharpe"] > baseline_summary["Sharpe"]
            and abs(parsed["MDD"]) <= abs(baseline_summary["MDD"]) + 0.01
            and parsed["NegativeCAGRWindows"] <= 1
            and parsed["Top3PositiveSymbolShare"] < 0.60
        ):
            conversion_grade = "candidate"
        elif parsed["NegativeCAGRWindows"] == 0 and parsed["Top3PositiveSymbolShare"] < 0.50:
            conversion_grade = "research_watch"

        parsed_rows.append(
            {
                "variant": parsed["Variant"],
                "conversion_score": round(score, 4),
                "conversion_grade": conversion_grade,
                "cagr": parsed["CAGR"],
                "mdd": parsed["MDD"],
                "sharpe": parsed["Sharpe"],
                "annual_turnover": parsed["AnnualTurnover"],
                "positive_cagr_windows": int(parsed["PositiveCAGRWindows"]),
                "negative_cagr_windows": int(parsed["NegativeCAGRWindows"]),
                "cost_75bps_cagr_delta_vs_strongest": parsed["Cost75BpsCAGRDelta"],
                "avg_monthly_delta_vs_strongest": parsed["AvgMonthlyDelta"],
                "residual_ex_top3": parsed["ResidualExTop3"],
                "top3_positive_symbol_share": parsed["Top3PositiveSymbolShare"],
                "notes": notes,
            }
        )

    ranked = sorted(parsed_rows, key=lambda row: row["conversion_score"], reverse=True)
    return {
        "baseline_variant": BASELINE_VARIANT,
        "aggressive_strongest_variant": STRONGEST_VARIANT,
        "baseline_metrics": {
            "cagr": baseline_summary["CAGR"],
            "mdd": baseline_summary["MDD"],
            "sharpe": baseline_summary["Sharpe"],
            "annual_turnover": baseline_summary["AnnualTurnover"],
        },
        "best_operational_conversion_candidate": ranked[0]["variant"] if ranked else None,
        "candidate_count": sum(1 for row in ranked if row["conversion_grade"] == "candidate"),
        "research_watch_count": sum(1 for row in ranked if row["conversion_grade"] == "research_watch"),
        "reference_row": reference_row,
        "rows": ranked,
        "verdict": (
            "no near-miss is ready for direct operational promotion yet; keep the operating baseline in production, "
            "but prioritize the highest-ranked conversion candidate for the next drawdown-control search"
        ),
    }


def _build_markdown(summary: dict) -> str:
    lines = [
        "# Split Models Operational Conversion Candidates",
        "",
        "## Purpose",
        "",
        "- score the current aggressive strongest and main near-miss branches against operational-conversion needs",
        "- separate direct operating candidates from branches that still need drawdown or fragility work",
        "",
        "## Baseline Anchor",
        "",
        f"- operational baseline: `{summary['baseline_variant']}`",
        f"- CAGR: `{_pct(summary['baseline_metrics']['cagr'])}`",
        f"- MDD: `{_pct(summary['baseline_metrics']['mdd'])}`",
        f"- Sharpe: `{summary['baseline_metrics']['sharpe']:.4f}`",
        f"- Annual turnover: `{summary['baseline_metrics']['annual_turnover']:.2f}`",
        "",
        "## Ranked Conversion Watchlist",
        "",
        "| Rank | Variant | Grade | Score | CAGR | MDD | Sharpe | Neg WF | Top3 Share |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for idx, row in enumerate(summary["rows"], start=1):
        lines.append(
            "| "
            f"{idx} | `{row['variant']}` | `{row['conversion_grade']}` | {row['conversion_score']:.2f} | "
            f"{_pct(row['cagr'])} | {_pct(row['mdd'])} | {row['sharpe']:.4f} | "
            f"{row['negative_cagr_windows']} | {_pct(row['top3_positive_symbol_share'])} |"
        )

    lines.extend(
        [
            "",
            "## Strongest Reference",
            "",
            f"- `{summary['reference_row']['variant']}`",
        ]
    )

    for note in summary["reference_row"]["notes"]:
        lines.append(f"  - {note}")

    lines.extend(
        [
            "",
            "## Candidate Read",
            "",
        ]
    )

    for row in summary["rows"][:3]:
        lines.append(f"- `{row['variant']}`")
        for note in row["notes"]:
            lines.append(f"  - {note}")

    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"- best conversion candidate right now: `{summary['best_operational_conversion_candidate']}`",
            f"- direct operating candidates: `{summary['candidate_count']}`",
            f"- research-watch candidates: `{summary['research_watch_count']}`",
            f"- {summary['verdict']}",
            "",
        ]
    )
    return "\n".join(lines)


def _write_csv(summary: dict) -> None:
    fieldnames = [
        "variant",
        "conversion_grade",
        "conversion_score",
        "cagr",
        "mdd",
        "sharpe",
        "annual_turnover",
        "positive_cagr_windows",
        "negative_cagr_windows",
        "cost_75bps_cagr_delta_vs_strongest",
        "avg_monthly_delta_vs_strongest",
        "residual_ex_top3",
        "top3_positive_symbol_share",
    ]
    with (OUTPUT_DIR / "operational_conversion_candidates.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary["rows"]:
            writer.writerow({key: row[key] for key in fieldnames})


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = _build_summary()
    (OUTPUT_DIR / "operational_conversion_candidates_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "operational_conversion_candidates.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    _write_csv(summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
