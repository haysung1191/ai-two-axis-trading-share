from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_defensive_bridge_screen import (
    build_report as build_attack_defensive_bridge_screen,
)
from scripts.compare_btc_1d_attack_main_backup_screen import (
    build_report as build_attack_main_backup_screen,
)
from scripts.compare_btc_1d_attack_pivot_screen import build_report as build_attack_pivot_screen
from scripts.compare_btc_1d_trend_dip_family_handoff import (
    build_report as build_trend_dip_family_handoff,
)


ANALYSIS_DIR = Path("analysis_results")


def build_report() -> dict:
    pivot = build_attack_pivot_screen()
    main_backup = build_attack_main_backup_screen()
    bridge = build_attack_defensive_bridge_screen()
    trend_dip_handoff = build_trend_dip_family_handoff()

    attack_main = main_backup["stack_top"]["attack_main"]
    attack_backup = main_backup["stack_top"]["attack_backup"]
    defensive_hold = bridge["stack_top"]["defensive_hold"]
    pivot_verdict = pivot["pivot_verdict"]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "current_stack": {
            "attack_main": attack_main,
            "attack_backup": attack_backup,
            "defensive_hold": defensive_hold,
            "primary_mutation_space_closed": pivot["primary_lane_status"]["mutation_space_closed"],
            "secondary_promotion_ready": pivot["secondary_lane_status"]["promotion_ready"],
            "primary_lane_handoff_status": trend_dip_handoff["family"]["status"],
        },
        "next_family_brief": {
            "track": "aggressive_model_development",
            "post_pivot_mode": pivot_verdict["pivot_mode"],
            "selected_seed_label": defensive_hold,
            "selected_seed_role": "defensive_research_hold",
            "selection_reason": (
                "The primary trend-dip lane is exhausted, the secondary spike-reversal lane is not promotion-ready, "
                "the latest trend-dip repair handoff confirms no promotable repair branch, and the defensive hold is "
                "the highest-quality distinct family already on the board."
            ),
            "do_not_restart": [
                attack_main,
                attack_backup,
                pivot["secondary_lane_status"]["label"],
            ],
            "new_family_search_goal": "search a new attack-capable family from the calmer defensive seed without reopening exhausted trend-dip or blocked spike-reversal loops",
            "first_actions": [
                "derive mutation hypotheses from defensive_hold entry/exit asymmetry",
                "screen for upside extension without losing defensive drawdown base",
                "compare resulting family back against attack_main after candidate-stage evidence exists",
            ],
        },
        "trend_dip_handoff": {
            "family_status": trend_dip_handoff["family"]["status"],
            "best_stage1_candidate": trend_dip_handoff["stage1_summary"]["best_stage1_candidate"]["variant_label"],
            "best_cagr_repair": trend_dip_handoff["repair_summary"]["best_cagr_repair"]["variant_label"],
            "best_sensitivity_repair": trend_dip_handoff["repair_summary"]["best_sensitivity_repair"]["variant_label"],
            "next_transition_hint": trend_dip_handoff["exhaustion_verdict"]["next_transition_hint"],
        },
        "decision_summary": [
            f"Freeze `{attack_main}` as the active attack anchor and `{attack_backup}` as the backup; do not spend the next cycle reopening that family.",
            f"Do not keep pushing `{pivot['secondary_lane_status']['label']}` because the current secondary repair loop is exhausted.",
            f"Use `{defensive_hold}` as the next new-family search seed because it is the strongest distinct non-attack family already validated on the board.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    current = report["current_stack"]
    brief = report["next_family_brief"]
    trend_dip_handoff = report["trend_dip_handoff"]
    lines = [
        "# BTC 1d Attack Post-Pivot Next Family Brief",
        "",
        f"- Attack main: `{current['attack_main']}`",
        f"- Attack backup: `{current['attack_backup']}`",
        f"- Defensive hold: `{current['defensive_hold']}`",
        f"- Primary mutation space closed: `{current['primary_mutation_space_closed']}`",
        f"- Secondary promotion ready: `{current['secondary_promotion_ready']}`",
        f"- Primary lane handoff status: `{current['primary_lane_handoff_status']}`",
        f"- Selected seed label: `{brief['selected_seed_label']}`",
        f"- Selected seed role: `{brief['selected_seed_role']}`",
        f"- Search goal: {brief['new_family_search_goal']}",
        f"- Selection reason: {brief['selection_reason']}",
        f"- Trend-dip best stage1 candidate: `{trend_dip_handoff['best_stage1_candidate']}`",
        f"- Trend-dip best CAGR repair: `{trend_dip_handoff['best_cagr_repair']}`",
        f"- Trend-dip best sensitivity repair: `{trend_dip_handoff['best_sensitivity_repair']}`",
        "",
        "## First Actions",
    ]
    for item in brief["first_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Do Not Restart"])
    for item in brief["do_not_restart"]:
        lines.append(f"- `{item}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_post_pivot_next_family_brief_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_post_pivot_next_family_brief_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_attack_post_pivot_next_family_brief_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_attack_post_pivot_next_family_brief_latest.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    latest_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest_md.write_text(_render_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "latest_json_path": str(latest_json),
                "latest_md_path": str(latest_md),
                "report": report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
