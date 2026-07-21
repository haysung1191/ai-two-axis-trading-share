from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_main_backup_screen import build_report as build_attack_stack_report


ANALYSIS_DIR = Path("analysis_results")


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest_json(analysis_dir: Path, pattern: str) -> dict[str, Any]:
    matches = sorted(
        analysis_dir.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not matches and pattern == "btc_1d_near_miss_priority_screen_*.json":
        scoreboard = _load_optional_json(analysis_dir / "btc_1d_model_scoreboard_latest.json")
        rows = [
            row
            for row in list(scoreboard.get("top_models", [])) + list(scoreboard.get("top_new_models", []))
            if str(row.get("role", "")).lower() not in {"attack_main", "attack_backup", "attack_challenger"}
        ]
        priority_rows = []
        for row in rows[:2]:
            priority_rows.append(
                {
                    "label": str(row.get("variant", "")),
                    "base_cagr": float(row.get("cagr") or 0.0),
                    "base_mdd": float(row.get("mdd") or 0.0),
                    "base_sharpe": float(row.get("sharpe") or 0.0),
                    "candidate_stage_status": str(row.get("candidate_stage") or row.get("gate_failure_reason") or "scoreboard_latest_fallback"),
                    "mdd_gap_to_attack_main_pct": 0.0,
                    "source": "scoreboard_latest_fallback",
                }
            )
        while len(priority_rows) < 2:
            priority_rows.append(
                {
                    "label": "none",
                    "base_cagr": 0.0,
                    "base_mdd": 0.0,
                    "base_sharpe": 0.0,
                    "candidate_stage_status": "scoreboard_latest_fallback_empty",
                    "mdd_gap_to_attack_main_pct": 0.0,
                    "source": "scoreboard_latest_fallback_empty",
                }
            )
        return {"priority_rows": priority_rows}
    if not matches:
        raise FileNotFoundError(f"No analysis artifact matched pattern: {pattern}")
    return _load_optional_json(matches[0])


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    attack_stack = build_attack_stack_report()
    near_miss_priority = _latest_json(
        analysis_dir, "btc_1d_near_miss_priority_screen_*.json"
    )
    hold36_local_ceiling = _load_optional_json(
        analysis_dir / "btc_1d_hold36_local_ceiling_handoff_latest.json"
    )
    local_ceiling_status = hold36_local_ceiling.get("local_ceiling_status", {})

    attack_main = next(
        item
        for item in attack_stack["compared_models"]
        if item["label"] == attack_stack["stack_top"]["attack_main"]
    )
    attack_backup = next(
        item
        for item in attack_stack["compared_models"]
        if item["label"] == attack_stack["stack_top"]["attack_backup"]
    )
    attack_challenger = next(
        item
        for item in attack_stack["compared_models"]
        if item["label"] == attack_stack["stack_top"]["attack_challenger"]
    )
    highest_priority_near_miss = near_miss_priority["priority_rows"][0]
    highest_raw_upside_near_miss = near_miss_priority["priority_rows"][1]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
        "standard_check_order_reference": ["practical", "research", "contract", "brief"],
        "quick_read_order_version": "research_stack_v2",
        "quick_read_order": [
            "quick_read",
            "stack_roles",
            "stack",
            "local_ceiling",
            "near_miss_priority",
            "operating_read",
        ],
        "stack_top": attack_stack["stack_top"],
        "operating_brief": {
            "attack_frontier": attack_main["label"],
            "attack_backup": attack_backup["label"],
            "attack_challenger": attack_challenger["label"],
            "highest_priority_near_miss": highest_priority_near_miss["label"],
            "highest_raw_upside_near_miss": highest_raw_upside_near_miss["label"],
        },
        "quick_read": [
            f"Attack frontier: {attack_main['label']} ({attack_main['base_cagr']:.2%} / {attack_main['base_mdd']:.2%} / Sharpe {attack_main['base_sharpe']:.4f})",
            f"Attack backup: {attack_backup['label']} ({attack_backup['base_cagr']:.2%} / {attack_backup['base_mdd']:.2%} / Sharpe {attack_backup['base_sharpe']:.4f})",
            f"Attack challenger: {attack_challenger['label']} ({attack_challenger['base_cagr']:.2%} / {attack_challenger['base_mdd']:.2%} / Sharpe {attack_challenger['base_sharpe']:.4f})",
            (
                "Hold36 local ceiling: "
                f"{local_ceiling_status.get('status_band', 'unknown')} / "
                f"{local_ceiling_status.get('primary_blocker', 'unknown')} / "
                f"do_not_repeat={local_ceiling_status.get('do_not_repeat_local_loop', False)}"
            ),
            f"Next near-miss to revisit: {highest_priority_near_miss['label']} ({highest_priority_near_miss['base_cagr']:.2%} / {highest_priority_near_miss['base_mdd']:.2%})",
        ],
        "models": {
            "attack_main": attack_main,
            "attack_backup": attack_backup,
            "attack_challenger": attack_challenger,
            "highest_priority_near_miss": highest_priority_near_miss,
            "highest_raw_upside_near_miss": highest_raw_upside_near_miss,
        },
        "local_ceiling": {
            "active_backup": hold36_local_ceiling.get("handoff_reference", {}).get(
                "active_backup", ""
            ),
            "status_band": local_ceiling_status.get("status_band", ""),
            "ceiling_confirmed": local_ceiling_status.get("ceiling_confirmed", False),
            "primary_blocker": local_ceiling_status.get("primary_blocker", ""),
            "remaining_base_cagr_gap_to_open": local_ceiling_status.get(
                "remaining_base_cagr_gap_to_open"
            ),
            "remaining_cost20_cagr_gap_to_open": local_ceiling_status.get(
                "remaining_cost20_cagr_gap_to_open"
            ),
            "closed_local_axes": local_ceiling_status.get("closed_local_axes", []),
            "do_not_repeat_local_loop": local_ceiling_status.get(
                "do_not_repeat_local_loop", False
            ),
            "next_step_now": local_ceiling_status.get("next_step_now", ""),
        },
        "brief_verdict": {
            "preferred_attack_frontier": attack_main["label"],
            "preferred_attack_backup": attack_backup["label"],
            "preferred_attack_challenger": attack_challenger["label"],
            "highest_priority_near_miss": highest_priority_near_miss["label"],
            "reason": "Operate off the ratio112 attack frontier, keep bridge_28_relief as the active backup, keep the approved trend960 post-spike line in the challenger lane, and treat the hold36 pressure-watch loop as closed local context unless a wider frame or new family opens.",
        },
        "paths": {
            "quick_read_contract_screen": "analysis_results\\btc_1d_quick_read_contract_screen_latest.json",
            "quick_read_contract_screen_md": "analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md",
            "meta_contract_screen": "analysis_results\\btc_1d_meta_contract_screen_latest.json",
            "meta_contract_screen_md": "analysis_results\\btc_1d_meta_contract_screen_md_latest.md",
        },
    }
    return report


def _render_markdown(report: dict) -> str:
    lines = [
        "# BTC 1d Research Stack Operating Brief",
        "",
        "## Quick Read",
        "",
    ]
    for line in report["quick_read"]:
        lines.append(f"- {line}")
    lines.extend(
        [
            "",
            "## Stack Roles",
            "",
            f"- Attack frontier: `{report['operating_brief']['attack_frontier']}`",
            f"- Attack backup: `{report['operating_brief']['attack_backup']}`",
            f"- Attack challenger: `{report['operating_brief']['attack_challenger']}`",
            f"- Highest-priority near-miss: `{report['operating_brief']['highest_priority_near_miss']}`",
            f"- Highest raw-upside near-miss: `{report['operating_brief']['highest_raw_upside_near_miss']}`",
            "",
            "## Stack",
            "",
            f"- Attack main: `{report['models']['attack_main']['label']}` | `{report['models']['attack_main']['base_cagr']:.2%} / {report['models']['attack_main']['base_mdd']:.2%} / Sharpe {report['models']['attack_main']['base_sharpe']:.4f}`",
            f"- Attack backup: `{report['models']['attack_backup']['label']}` | `{report['models']['attack_backup']['base_cagr']:.2%} / {report['models']['attack_backup']['base_mdd']:.2%} / Sharpe {report['models']['attack_backup']['base_sharpe']:.4f}`",
            f"- Attack challenger: `{report['models']['attack_challenger']['label']}` | `{report['models']['attack_challenger']['base_cagr']:.2%} / {report['models']['attack_challenger']['base_mdd']:.2%} / Sharpe {report['models']['attack_challenger']['base_sharpe']:.4f}`",
            "",
            "## Local Ceiling",
            "",
            f"- Active backup: `{report['local_ceiling']['active_backup']}`",
            f"- Status band: `{report['local_ceiling']['status_band']}`",
            f"- Ceiling confirmed: `{report['local_ceiling']['ceiling_confirmed']}`",
            f"- Primary blocker: `{report['local_ceiling']['primary_blocker']}`",
            f"- Remaining base cagr gap: `{report['local_ceiling']['remaining_base_cagr_gap_to_open']}`",
            f"- Remaining cost20 cagr gap: `{report['local_ceiling']['remaining_cost20_cagr_gap_to_open']}`",
            f"- Closed local axes: `{' | '.join(report['local_ceiling']['closed_local_axes'])}`",
            f"- Do not repeat local loop: `{report['local_ceiling']['do_not_repeat_local_loop']}`",
            f"- Next step now: `{report['local_ceiling']['next_step_now']}`",
            "",
            "## Near-Miss Priority",
            "",
            f"- Highest-priority near-miss: `{report['models']['highest_priority_near_miss']['label']}` | stage `{report['models']['highest_priority_near_miss']['candidate_stage_status']}` | gap MDD `{report['models']['highest_priority_near_miss']['mdd_gap_to_attack_main_pct']:.2f}%`",
            f"- Highest raw-upside near-miss: `{report['models']['highest_raw_upside_near_miss']['label']}` | stage `{report['models']['highest_raw_upside_near_miss']['candidate_stage_status']}` | gap MDD `{report['models']['highest_raw_upside_near_miss']['mdd_gap_to_attack_main_pct']:.2f}%`",
            "",
            "## Operating Read",
            "",
            f"- Reason: {report['brief_verdict']['reason']}",
            f"- Quick-read contract screen: `{report['paths']['quick_read_contract_screen_md']}`",
            f"- Meta contract screen: `{report['paths']['meta_contract_screen_md']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _write_latest_aliases(json_path: Path, md_path: Path) -> dict:
    latest_json = json_path.with_name("btc_1d_research_stack_operating_brief_latest.json")
    latest_md = md_path.with_name("btc_1d_research_stack_operating_brief_md_latest.md")
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    return {
        "btc_1d_research_stack_operating_brief": str(latest_json),
        "btc_1d_research_stack_operating_brief_md": str(latest_md),
    }


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_research_stack_operating_brief_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_research_stack_operating_brief_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    latest_aliases = _write_latest_aliases(json_path, md_path)
    print(
        json.dumps(
            {
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "latest_aliases": latest_aliases,
                "report": report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
