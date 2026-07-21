from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_overnight_guardrail"


SUMMARY = {
    "as_of_date": "2026-04-17",
    "repo": "momentum",
    "asset_class": "stocks_etfs",
    "operational_baseline": "rule_breadth_it_us5_cap",
    "aggressive_strongest": "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on",
    "broader_challenger": "hybrid_top2_plus_third00125",
    "quality_near_miss": "bonus_recipient_top1_third_85_15",
    "headline_near_miss": "tail_skip_entry_flowweakest_new_bottom4_top25_mid75",
    "kill_immediately_if": [
        "full-period CAGR is below the strongest by more than 0.50%p",
        "walk-forward CAGR windows are net negative",
        "75 bps cost CAGR delta vs strongest is negative by more than 0.25%p",
        "residual ex PLTR/NVDA/MU turns clearly negative",
    ],
    "promote_to_deeper_validation_if": [
        "full-period CAGR delta vs strongest is non-negative",
        "walk-forward CAGR windows are at least 3 positive and no more than 1 negative",
        "75 bps cost CAGR delta vs strongest is non-negative",
        "residual ex PLTR/NVDA/MU is non-negative",
    ],
    "document_as_near_miss_if": [
        "the candidate clearly wins one axis such as broader, higher-quality, or lower-turnover",
        "but it still fails promotion robustness on walk-forward, cost-adjusted Sharpe, or drawdown",
    ],
    "interpretation": {
        "stronger_axis": "headline CAGR plus promotion robustness",
        "broader_axis": "lower concentration and better breadth with only small CAGR give-up",
        "quality_axis": "higher Sharpe and better MDD even if turnover or cost-adjusted CAGR worsens",
        "headline_axis": "higher CAGR and lower turnover even if Sharpe stays weaker",
    },
    "nightly_default": "keep the current strongest unless a candidate clears the stronger-axis gate across full-period, walk-forward, cost, and residual together",
}


def _build_markdown(summary: dict) -> str:
    return "\n".join(
        [
            "# Split Models Overnight Guardrail",
            "",
            "## Purpose",
            "",
            "- freeze the overnight triage rule before another search run",
            "- keep the project from promoting a candidate just because one axis looks good",
            "",
            "## Current truth",
            "",
            f"- repo: `{summary['repo']}`",
            f"- asset class: `{summary['asset_class']}`",
            f"- operational baseline: `{summary['operational_baseline']}`",
            f"- aggressive strongest: `{summary['aggressive_strongest']}`",
            f"- broader challenger: `{summary['broader_challenger']}`",
            f"- quality near-miss: `{summary['quality_near_miss']}`",
            f"- headline near-miss: `{summary['headline_near_miss']}`",
            "",
            "## Kill Immediately",
            "",
            *[f"- {rule}" for rule in summary["kill_immediately_if"]],
            "",
            "## Deeper Validation",
            "",
            *[f"- {rule}" for rule in summary["promote_to_deeper_validation_if"]],
            "",
            "## Document As Near-Miss",
            "",
            *[f"- {rule}" for rule in summary["document_as_near_miss_if"]],
            "",
            "## Axis Reading",
            "",
            f"- stronger axis: `{summary['interpretation']['stronger_axis']}`",
            f"- broader axis: `{summary['interpretation']['broader_axis']}`",
            f"- quality axis: `{summary['interpretation']['quality_axis']}`",
            f"- headline axis: `{summary['interpretation']['headline_axis']}`",
            "",
            "## Default Overnight Rule",
            "",
            f"- {summary['nightly_default']}",
            "",
        ]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "overnight_guardrail_summary.json").write_text(json.dumps(SUMMARY, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "overnight_guardrail.md").write_text(_build_markdown(SUMMARY), encoding="utf-8")
    print(json.dumps(SUMMARY, indent=2))


if __name__ == "__main__":
    main()
