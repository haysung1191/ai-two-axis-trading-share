from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_nightly_safe_summary"


SUMMARY = {
    "as_of_date": "2026-04-17",
    "repo": "momentum",
    "asset_class": "stocks_etfs",
    "operational_baseline": "rule_breadth_it_us5_cap",
    "aggressive_strongest": "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on",
    "broader_challenger": "hybrid_top2_plus_third00125",
    "strongest_metrics": {
        "cagr": "63.16%",
        "mdd": "-29.27%",
        "sharpe": "1.6892",
        "annual_turnover": "15.32",
    },
    "broader_challenger_metrics": {
        "cagr": "63.12%",
        "mdd": "-29.27%",
        "sharpe": "1.6895",
        "annual_turnover": "15.32",
    },
    "broader_challenger_delta_vs_strongest": {
        "cagr_delta": "-0.04%p",
        "mdd_delta": "+0.00%p",
        "sharpe_delta": "+0.0003",
        "cost_75bps_cagr_delta": "-0.04%p",
        "walkforward": "2 positive / 2 negative",
    },
    "benchmark_check": {
        "benchmark": "benchmark_xs_mom_12_1_top5_eq",
        "strongest_cost_75bps_cagr_delta": "+11.49%p",
        "start_shift_cagr_record": "5 positive / 0 negative",
    },
    "nightly_verdict": {
        "keep_strongest": True,
        "promote_broader_challenger": False,
        "reason": "strongest remains the stronger branch; broader challenger is close but still weaker on CAGR and promotion robustness",
    },
    "bonus_near_miss": {
        "variant": "bonus_schedule_first55_second45",
        "cagr": "63.58%",
        "mdd": "-29.33%",
        "sharpe": "1.6902",
        "cost_75bps_cagr_delta_vs_strongest": "+0.37%p",
        "walkforward": "2 positive / 2 negative",
        "verdict": "headline-strong but still below promotion grade because walk-forward stays mixed and drawdown is slightly worse",
    },
    "quality_near_miss": {
        "variant": "bonus_recipient_top1_third_85_15",
        "cagr": "65.43%",
        "mdd": "-29.52%",
        "sharpe": "1.6927",
        "cost_75bps_cagr_delta_vs_strongest": "+1.68%p",
        "walkforward": "3 positive / 1 negative",
        "verdict": "CAGR improves further and walk-forward stays strong, but drawdown is slightly worse and turnover remains higher",
    },
    "skip_entry_near_miss": {
        "variant": "tail_skip_entry_flowweakest_new_bottom4_top25_mid75",
        "cagr": "63.21%",
        "mdd": "-28.77%",
        "sharpe": "1.6625",
        "cost_75bps_cagr_delta_vs_strongest": "+0.53%p",
        "walkforward": "3 positive / 1 negative",
        "verdict": "headline, drawdown, and turnover all improve, but Sharpe still remains meaningfully weaker than the strongest",
    },
}


def _build_markdown(summary: dict) -> str:
    strongest = summary["aggressive_strongest"]
    broader = summary["broader_challenger"]
    strongest_metrics = summary["strongest_metrics"]
    broader_metrics = summary["broader_challenger_metrics"]
    broader_delta = summary["broader_challenger_delta_vs_strongest"]
    benchmark = summary["benchmark_check"]
    bonus_near_miss = summary["bonus_near_miss"]
    quality_near_miss = summary["quality_near_miss"]
    skip_entry_near_miss = summary["skip_entry_near_miss"]

    return "\n".join(
        [
            "# Split Models Nightly Safe Summary",
            "",
            "## Current truth",
            "",
            f"- repo: `{summary['repo']}`",
            f"- asset class: `{summary['asset_class']}`",
            f"- operational baseline: `{summary['operational_baseline']}`",
            f"- aggressive strongest: `{strongest}`",
            f"- broader challenger: `{broader}`",
            "",
            "## Strongest snapshot",
            "",
            f"- CAGR: `{strongest_metrics['cagr']}`",
            f"- MDD: `{strongest_metrics['mdd']}`",
            f"- Sharpe: `{strongest_metrics['sharpe']}`",
            f"- Annual turnover: `{strongest_metrics['annual_turnover']}`",
            "",
            "## Broader challenger snapshot",
            "",
            f"- variant: `{broader}`",
            f"- CAGR: `{broader_metrics['cagr']}`",
            f"- MDD: `{broader_metrics['mdd']}`",
            f"- Sharpe: `{broader_metrics['sharpe']}`",
            f"- Annual turnover: `{broader_metrics['annual_turnover']}`",
            "",
            "## Why strongest still stays",
            "",
            f"- CAGR delta vs strongest: `{broader_delta['cagr_delta']}`",
            f"- MDD delta vs strongest: `{broader_delta['mdd_delta']}`",
            f"- Sharpe delta vs strongest: `{broader_delta['sharpe_delta']}`",
            f"- `75 bps` cost CAGR delta: `{broader_delta['cost_75bps_cagr_delta']}`",
            f"- walk-forward: `{broader_delta['walkforward']}`",
            "",
            "## Benchmark guardrail",
            "",
            f"- benchmark: `{benchmark['benchmark']}`",
            f"- strongest `75 bps` CAGR delta vs benchmark: `{benchmark['strongest_cost_75bps_cagr_delta']}`",
            f"- strongest start-date shift record: `{benchmark['start_shift_cagr_record']}`",
            "",
            "## Bonus Near-Miss",
            "",
            f"- variant: `{bonus_near_miss['variant']}`",
            f"- CAGR: `{bonus_near_miss['cagr']}`",
            f"- MDD: `{bonus_near_miss['mdd']}`",
            f"- Sharpe: `{bonus_near_miss['sharpe']}`",
            f"- `75 bps` cost CAGR delta vs strongest: `{bonus_near_miss['cost_75bps_cagr_delta_vs_strongest']}`",
            f"- walk-forward: `{bonus_near_miss['walkforward']}`",
            f"- verdict: `{bonus_near_miss['verdict']}`",
            "",
            "## Quality Near-Miss",
            "",
            f"- variant: `{quality_near_miss['variant']}`",
            f"- CAGR: `{quality_near_miss['cagr']}`",
            f"- MDD: `{quality_near_miss['mdd']}`",
            f"- Sharpe: `{quality_near_miss['sharpe']}`",
            f"- `75 bps` cost CAGR delta vs strongest: `{quality_near_miss['cost_75bps_cagr_delta_vs_strongest']}`",
            f"- walk-forward: `{quality_near_miss['walkforward']}`",
            f"- verdict: `{quality_near_miss['verdict']}`",
            "",
            "## Skip-Entry Near-Miss",
            "",
            f"- variant: `{skip_entry_near_miss['variant']}`",
            f"- CAGR: `{skip_entry_near_miss['cagr']}`",
            f"- MDD: `{skip_entry_near_miss['mdd']}`",
            f"- Sharpe: `{skip_entry_near_miss['sharpe']}`",
            f"- `75 bps` cost CAGR delta vs strongest: `{skip_entry_near_miss['cost_75bps_cagr_delta_vs_strongest']}`",
            f"- walk-forward: `{skip_entry_near_miss['walkforward']}`",
            f"- verdict: `{skip_entry_near_miss['verdict']}`",
            "",
            "## Nightly verdict",
            "",
            "- keep the current strongest as the mainline aggressive branch",
            "- treat the broader challenger as a near-miss, not a promotion",
            "- treat the quality near-miss as a quality-tilted alternative, not a promotion",
            "- treat the skip-entry near-miss as a stronger-but-lower-quality alternative, not a promotion",
            "- if more overnight work is run, prefer broader-challenger exploration over disturbing the strongest baseline again",
            "",
        ]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "nightly_safe_summary.json").write_text(json.dumps(SUMMARY, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "nightly_safe_summary.md").write_text(_build_markdown(SUMMARY), encoding="utf-8")
    print(json.dumps(SUMMARY, indent=2))


if __name__ == "__main__":
    main()
