from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_main_backup_screen import (
    build_report as build_attack_stack_screen,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_json(prefix: str) -> Path:
    matches = sorted(ANALYSIS_DIR.glob(f"{prefix}*.json"))
    if not matches:
        raise FileNotFoundError(f"No analysis result found for prefix: {prefix}")
    return matches[-1]


def _seed_cycle() -> dict:
    payload = _load_json(_latest_json("btc_1d_post_spike_reopen_seed_cycle_"))
    results = list(payload.get("seed_results", []))
    preferred_label = str(payload["reopen_seed_cycle"]["preferred_seed_now"])
    preferred = next(item for item in results if str(item["seed_label"]) == preferred_label)
    backup = next(item for item in results if str(item["seed_label"]) != preferred_label)
    return {
        "requested_preferred_seed": str(payload["cycle_reference"]["requested_preferred_seed"]),
        "requested_backup_seed": str(payload["cycle_reference"]["requested_backup_seed"]),
        "preferred_seed": preferred,
        "backup_seed": backup,
        "cycle_json": str(_latest_json("btc_1d_post_spike_reopen_seed_cycle_")),
    }


def build_report() -> dict:
    stack = build_attack_stack_screen()
    cycle = _seed_cycle()

    main = next(item for item in stack["compared_models"] if str(item["role"]) == "attack_main")
    active_backup = next(item for item in stack["compared_models"] if str(item["role"]) == "attack_backup")
    preferred = dict(cycle["preferred_seed"])
    backup_seed = dict(cycle["backup_seed"])

    preferred_has_clean_reopen = (
        bool(preferred["paper_validation_passed"])
        and bool(preferred["walk_forward_passed"])
        and int(preferred["negative_window_count"]) == 0
    )
    preferred_pressures_active_backup = float(preferred["base_cagr"]) >= float(active_backup["base_cagr"])
    preferred_pressures_main = float(preferred["base_cagr"]) >= float(main["base_cagr"])
    backup_seed_is_viable = (
        bool(backup_seed["paper_validation_passed"])
        and bool(backup_seed["walk_forward_passed"])
        and int(backup_seed["negative_window_count"]) == 0
    )

    next_step_now = (
        "open_revalidated_seed_board_comparison"
        if preferred_has_clean_reopen
        else "hold_seed_outside_attack_board"
    )
    reopen_lane = (
        "attack_reopen_comparison_queue"
        if preferred_has_clean_reopen
        else "reopen_repair_hold"
    )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "attack_stack_reference": dict(stack["stack_top"]),
        "reopen_seed_reference": {
            "requested_preferred_seed": cycle["requested_preferred_seed"],
            "requested_backup_seed": cycle["requested_backup_seed"],
            "preferred_seed_now": str(preferred["seed_label"]),
            "backup_seed_now": str(backup_seed["seed_label"]),
        },
        "reopen_attack_comparison": {
            "preferred_seed_has_clean_reopen": preferred_has_clean_reopen,
            "preferred_seed_pressures_active_backup": preferred_pressures_active_backup,
            "preferred_seed_pressures_attack_main": preferred_pressures_main,
            "backup_seed_is_viable": backup_seed_is_viable,
            "reopen_lane": reopen_lane,
            "next_step_now": next_step_now,
        },
        "comparison_metrics": {
            "attack_main_base_cagr": float(main["base_cagr"]),
            "active_backup_base_cagr": float(active_backup["base_cagr"]),
            "preferred_seed_base_cagr": float(preferred["base_cagr"]),
            "preferred_seed_base_sharpe": float(preferred["base_sharpe"]),
            "preferred_seed_base_mdd": float(preferred["base_max_drawdown"]),
            "preferred_seed_sensitivity_max_drift": float(preferred["sensitivity_max_drift"]),
            "backup_seed_base_cagr": float(backup_seed["base_cagr"]),
            "backup_seed_base_sharpe": float(backup_seed["base_sharpe"]),
            "backup_seed_base_mdd": float(backup_seed["base_max_drawdown"]),
        },
        "artifact_paths": {
            "seed_cycle_json": cycle["cycle_json"],
            "preferred_seed_validation_json": str(preferred["validation_json"]),
            "preferred_seed_walk_forward_json": str(preferred["walk_forward_json"]),
            "backup_seed_validation_json": str(backup_seed["validation_json"]),
            "backup_seed_walk_forward_json": str(backup_seed["walk_forward_json"]),
        },
        "decision_summary": [
            (
                f"Preferred reopen seed `{preferred['seed_label']}` is clean enough to reopen attack comparison."
                if preferred_has_clean_reopen
                else f"Preferred reopen seed `{preferred['seed_label']}` still needs repair before attack comparison."
            ),
            f"Preferred reopen seed base CAGR is `{preferred['base_cagr']:.6f}` vs active backup `{active_backup['base_cagr']:.6f}` and attack main `{main['base_cagr']:.6f}`.",
            f"Backup seed `{backup_seed['seed_label']}` remains `{'viable' if backup_seed_is_viable else 'not_viable'}` as the secondary reopen line.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    status = report["reopen_attack_comparison"]
    metrics = report["comparison_metrics"]
    lines = [
        "# BTC 1d Post-Spike Reopen Seed Attack Comparison",
        "",
        f"- Attack main: `{report['attack_stack_reference']['attack_main']}`",
        f"- Active backup: `{report['attack_stack_reference']['attack_backup']}`",
        f"- Preferred seed now: `{report['reopen_seed_reference']['preferred_seed_now']}`",
        f"- Backup seed now: `{report['reopen_seed_reference']['backup_seed_now']}`",
        f"- Reopen lane: `{status['reopen_lane']}`",
        f"- Next step now: `{status['next_step_now']}`",
        "",
        "## Metrics",
        f"- attack_main_base_cagr: `{metrics['attack_main_base_cagr']}`",
        f"- active_backup_base_cagr: `{metrics['active_backup_base_cagr']}`",
        f"- preferred_seed_base_cagr: `{metrics['preferred_seed_base_cagr']}`",
        f"- preferred_seed_base_sharpe: `{metrics['preferred_seed_base_sharpe']}`",
        f"- preferred_seed_base_mdd: `{metrics['preferred_seed_base_mdd']}`",
        f"- preferred_seed_sensitivity_max_drift: `{metrics['preferred_seed_sensitivity_max_drift']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_reopen_seed_attack_comparison_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_reopen_seed_attack_comparison_{stamp}.md"
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
