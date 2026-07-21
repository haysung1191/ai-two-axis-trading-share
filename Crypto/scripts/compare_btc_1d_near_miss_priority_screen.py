from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_research_stack_gap_screen import build_report as build_gap_report


ANALYSIS_DIR = Path("analysis_results")


def build_report() -> dict:
    gap_report = build_gap_report()
    rows = gap_report["recent_attack_near_miss_holds"]

    by_label = {row["label"]: row for row in rows}
    trend_dip = by_label["trend_dip_reversal_breakout_tighter_stop_mid_hold"]
    spike_reversal = by_label["volatility_spike_reversal_continuation_slower_trend"]

    priority_rows = [
        {
            **trend_dip,
            "priority_read": "validated_but_failed_candidate",
            "next_value": "higher",
            "priority_reason": "Closer drawdown gap to the attack main and already candidate-tested, so it gives more actionable evidence than a raw stage-1 hold.",
        },
        {
            **spike_reversal,
            "priority_read": "raw_upside_near_miss",
            "next_value": "secondary",
            "priority_reason": "Closer CAGR to the attack main, but still stage-1 only and materially wider on drawdown.",
        },
    ]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "attack_frontier": gap_report["gap_summary"]["preferred_attack_frontier"],
        "priority_rows": priority_rows,
        "priority_verdict": {
            "highest_priority_near_miss": trend_dip["label"],
            "highest_raw_upside_near_miss": spike_reversal["label"],
            "reason": "Trend-dip reversal breakout is the better next near-miss to revisit because it is closer on drawdown and already has candidate-stage evidence, while spike reversal continuation remains a raw upside hold with less validation depth.",
        },
        "decision_summary": [
            "trend_dip_reversal_breakout_tighter_stop_mid_hold is the highest-priority near-miss to revisit if the attack frontier is reopened.",
            "volatility_spike_reversal_continuation_slower_trend remains the highest raw-upside near-miss, but it is less validated.",
            "Neither near-miss is close enough on drawdown to displace the current attack frontier.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    lines = [
        "# BTC 1d Near-Miss Priority Screen",
        "",
        f"- Attack frontier: `{report['attack_frontier']}`",
        f"- Highest-priority near-miss: `{report['priority_verdict']['highest_priority_near_miss']}`",
        f"- Highest raw-upside near-miss: `{report['priority_verdict']['highest_raw_upside_near_miss']}`",
        f"- Reason: {report['priority_verdict']['reason']}",
        "",
    ]
    for row in report["priority_rows"]:
        lines.extend(
            [
                f"## {row['label']}",
                f"- priority read: `{row['priority_read']}`",
                f"- next value: `{row['next_value']}`",
                f"- base: `{row['base_cagr']:.4f}` CAGR / `{row['base_mdd']:.4f}` MDD / Sharpe `{row['base_sharpe']:.4f}`",
                f"- gap to attack main: CAGR `{row['cagr_gap_to_attack_main_pct']:.2f}%`, MDD `{row['mdd_gap_to_attack_main_pct']:.2f}%`, Sharpe `{row['sharpe_gap_to_attack_main']:.4f}`",
                f"- stage status: `{row['candidate_stage_status']}`",
                f"- reason: {row['priority_reason']}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_near_miss_priority_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_near_miss_priority_screen_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
