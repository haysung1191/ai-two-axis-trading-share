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


ANALYSIS_DIR = Path("analysis_results")
TERMINAL_SCREEN_PATH = ANALYSIS_DIR / "btc_1d_post_broad_search_terminal_screen_20260418T153750Z.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report() -> dict:
    terminal = _load_json(TERMINAL_SCREEN_PATH)
    main_backup = build_attack_main_backup_screen()
    bridge = build_attack_defensive_bridge_screen()

    attack_main = main_backup["stack_top"]["attack_main"]
    attack_backup = main_backup["stack_top"]["attack_backup"]
    defensive_hold = bridge["stack_top"]["defensive_hold"]
    hold = terminal["hold_status"]
    final_exhausted_seed = terminal["broad_search_terminal_summary"]["final_exhausted_seed"]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "terminal_state": {
            "broad_search_framework_closed": terminal["terminal_verdict"]["broad_search_framework_closed"],
            "final_exhausted_seed": final_exhausted_seed,
            "failed_hold_family": hold["family"],
            "failed_hold_promoted": hold["promoted_to_candidate_stage"],
        },
        "reframe_brief": {
            "track": "aggressive_model_development",
            "mode": "terminal_reframe",
            "selected_seed_label": defensive_hold,
            "selected_seed_role": "defensive_research_hold",
            "selection_reason": (
                "Broad-search rotation is exhausted and the failed-breakout hold still misses candidate-stage, "
                "so the next cycle should restart from the strongest distinct validated hold rather than another low-alpha broad-search lane."
            ),
            "preserve_references": [
                attack_main,
                attack_backup,
                defensive_hold,
            ],
            "do_not_restart": [
                final_exhausted_seed,
                hold["family"],
                "brief_close_above_reset_continuation",
                "reclaim_shelf_acceleration",
                "shallow_breakout_shelf_continuation",
            ],
            "reframe_goal": "define a fresh attack-capable search framework from the defensive hold and validated attack stack instead of reopening exhausted low-alpha lanes",
            "framework_rules": [
                "use ratio112 and ratio111 only as reference anchors, not as immediate mutation targets",
                "do not reopen failed_breakout_continuation as-is because hold refinement still capped below candidate-stage",
                "do not rotate back into the exhausted reclaim-grab or compression-reset broad-search pool",
                "start from defensive-hold asymmetry and require candidate-stage evidence above 0.20 CAGR with clean stage2 behavior",
            ],
            "first_actions": [
                "derive a fresh mutation family from volatility_expansion_pullthrough_shorter_hold entry and exit asymmetry",
                "screen that family against the same candidate-stage bar used in the failed-breakout hold refinement",
                "only compare back to ratio112_tighter_stop_main after a new family produces clean candidate-stage evidence",
            ],
            "success_gate": {
                "must_not_reuse_exhausted_broad_seed": True,
                "must_not_reuse_failed_hold_without_reframe": True,
                "must_target_clean_candidate_stage": True,
                "candidate_stage_floor_cagr": 0.20,
                "candidate_stage_max_drawdown": 0.16,
            },
        },
        "decision_summary": [
            f"Treat `{hold['family']}` as a closed hold experiment because refinement still topped out at `{hold['cagr']:.4f}` CAGR without candidate-stage promotion.",
            f"Use `{defensive_hold}` as the next reframe seed because it is the strongest distinct validated hold left after broad-search exhaustion.",
            "Start the next cycle with a new framework brief, not another broad-search rotation or failed-breakout micro-refinement.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    brief = report["reframe_brief"]
    terminal = report["terminal_state"]
    lines = [
        "# BTC 1d Terminal Reframe Brief",
        "",
        f"- Broad-search framework closed: `{terminal['broad_search_framework_closed']}`",
        f"- Final exhausted seed: `{terminal['final_exhausted_seed']}`",
        f"- Failed hold family: `{terminal['failed_hold_family']}`",
        f"- Selected seed label: `{brief['selected_seed_label']}`",
        f"- Selected seed role: `{brief['selected_seed_role']}`",
        f"- Reframe goal: {brief['reframe_goal']}",
        f"- Selection reason: {brief['selection_reason']}",
        "",
        "## Preserve References",
    ]
    for item in brief["preserve_references"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Do Not Restart"])
    for item in brief["do_not_restart"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## First Actions"])
    for item in brief["first_actions"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_terminal_reframe_brief_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_terminal_reframe_brief_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "report": report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
