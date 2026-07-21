from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.attack_active_stack import (
    ACTIVE_ATTACK_BACKUP_LABEL,
    ACTIVE_ATTACK_MAIN_LABEL,
)
from scripts.compare_btc_1d_attack_defensive_bridge_screen import build_report as build_attack_defensive_report
from scripts.compare_btc_1d_attack_main_backup_screen import build_report as build_attack_main_backup_report


ANALYSIS_DIR = Path("analysis_results")


def build_report() -> dict:
    attack_backup = build_attack_main_backup_report()
    attack_defensive = build_attack_defensive_report()

    attack_main = next(
        item for item in attack_backup["compared_models"] if item["label"] == ACTIVE_ATTACK_MAIN_LABEL
    )
    attack_backup_model = next(
        item for item in attack_backup["compared_models"] if item["label"] == ACTIVE_ATTACK_BACKUP_LABEL
    )
    defensive_hold = next(
        item for item in attack_defensive["compared_models"] if item["label"] == "volatility_expansion_pullthrough_shorter_hold"
    )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "stack_top": {
            "attack_main": attack_main["label"],
            "attack_backup": attack_backup_model["label"],
            "defensive_hold": defensive_hold["label"],
        },
        "models": [attack_main, attack_backup_model, defensive_hold],
        "stack_verdict": {
            "top_attack_model": attack_main["label"],
            "backup_attack_model": attack_backup_model["label"],
            "top_defensive_hold": defensive_hold["label"],
            "roles_are_distinct": True,
            "reason": "The active attack stack keeps ratio112 as the return anchor, bridge_28_relief as the live backup, and pullthrough shorter-hold as the best defensive research hold without replacing the attack stack.",
        },
        "decision_summary": [
            "ratio112 tighter_stop is still the stack-top attack main.",
            "bridge_28_relief is now the stack-top attack backup under the active attack stack contract.",
            "pullthrough shorter_hold is still the best defensive research hold, but it does not replace either attack model.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    lines = [
        "# BTC 1d Research Stack Top Screen",
        "",
        f"- Attack main: `{report['stack_top']['attack_main']}`",
        f"- Attack backup: `{report['stack_top']['attack_backup']}`",
        f"- Defensive hold: `{report['stack_top']['defensive_hold']}`",
        f"- Roles are distinct: `{report['stack_verdict']['roles_are_distinct']}`",
        f"- Reason: {report['stack_verdict']['reason']}",
        "",
    ]
    for row in report["models"]:
        lines.extend(
            [
                f"## {row['label']}",
                f"- role: `{row['role']}`",
                f"- base: `{row['base_cagr']:.4f}` CAGR / `{row['base_mdd']:.4f}` MDD / Sharpe `{row['base_sharpe']:.4f}`",
                f"- OOS Sharpe: `{row['oos_sharpe']:.4f}`",
                f"- drift: `{row['sensitivity_max_drift']:.4f}`",
                f"- cost20 Sharpe: `{row['cost20_sharpe']:.4f}`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_research_stack_top_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_research_stack_top_screen_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
