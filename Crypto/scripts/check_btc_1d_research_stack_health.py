from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a one-line BTC 1d research stack health check from latest research stack artifacts. "
            "Standard operating check order: practical -> research -> contract -> brief."
        )
    )
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--as-json", action="store_true")
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_research_stack_health(*, analysis_dir: Path) -> dict[str, Any]:
    brief = _load_json(analysis_dir / "btc_1d_research_stack_operating_brief_latest.json")
    operating_brief = _load_json(analysis_dir / "btc_1d_operating_brief_latest.json")
    regression_lock_test = "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    standard_check_order_reference = brief.get(
        "standard_check_order_reference",
        ["practical", "research", "contract", "brief"],
    )
    operating = brief.get("operating_brief", {})
    models = brief.get("models", {})
    local_ceiling = brief.get("local_ceiling", {})
    attack_main = models.get("attack_main", {})
    attack_backup = models.get("attack_backup", {})
    attack_challenger = models.get("attack_challenger", {})
    near_miss = models.get("highest_priority_near_miss", {})

    return {
        "regression_lock_test": regression_lock_test,
        "standard_check_order_reference": standard_check_order_reference,
        "attack_frontier": operating.get("attack_frontier", "unknown"),
        "attack_backup": operating.get("attack_backup", "unknown"),
        "attack_challenger": operating.get("attack_challenger", "unknown"),
        "highest_priority_near_miss": operating.get("highest_priority_near_miss", "unknown"),
        "attack_frontier_cagr": attack_main.get("base_cagr"),
        "attack_frontier_max_drawdown": attack_main.get("base_mdd"),
        "attack_frontier_sharpe": attack_main.get("base_sharpe"),
        "attack_backup_drift": attack_backup.get("sensitivity_max_drift"),
        "attack_challenger_status": attack_challenger.get(
            "stack_read", attack_challenger.get("role", "unknown")
        ),
        "attack_challenger_cagr": attack_challenger.get("base_cagr"),
        "hold36_status_band": local_ceiling.get("status_band", ""),
        "hold36_primary_blocker": local_ceiling.get("primary_blocker", ""),
        "hold36_do_not_repeat_local_loop": local_ceiling.get(
            "do_not_repeat_local_loop", False
        ),
        "near_miss_status": near_miss.get("candidate_stage_status", "unknown"),
        "attack_challenger_remote_monitoring_deployment_handoff_ready": bool(
            operating_brief.get("attack_challenger_remote_monitoring_deployment_handoff_ready", False)
        ),
        "attack_challenger_next_step": str(
            operating_brief.get("attack_challenger_next_step", "")
        ),
        "attack_challenger_bridge_report": str(
            operating_brief.get("attack_challenger_bridge_report", "")
        ),
    }


def render_research_stack_health_line(result: dict[str, Any]) -> str:
    frontier_cagr = result["attack_frontier_cagr"]
    frontier_mdd = result["attack_frontier_max_drawdown"]
    frontier_sharpe = result["attack_frontier_sharpe"]
    backup_drift = result["attack_backup_drift"]
    cagr_part = f"{frontier_cagr:.2%}" if isinstance(frontier_cagr, (int, float)) else "n/a"
    mdd_part = f"{frontier_mdd:.2%}" if isinstance(frontier_mdd, (int, float)) else "n/a"
    sharpe_part = f"{frontier_sharpe:.4f}" if isinstance(frontier_sharpe, (int, float)) else "n/a"
    drift_part = f"{backup_drift:.4f}" if isinstance(backup_drift, (int, float)) else "n/a"
    challenger_cagr = result.get("attack_challenger_cagr")
    challenger_cagr_part = (
        f"{challenger_cagr:.2%}" if isinstance(challenger_cagr, (int, float)) else "n/a"
    )
    challenger_label = result.get("attack_challenger", result.get("defensive_hold", "unknown"))
    challenger_status = result.get(
        "attack_challenger_status", result.get("defensive_hold_status", "unknown")
    )
    return (
        f"BTC 1d research stack | frontier={result['attack_frontier']} | "
        f"cagr={cagr_part} | mdd={mdd_part} | sharpe={sharpe_part} | "
        f"backup={result['attack_backup']} | backup_drift={drift_part} | "
        f"challenger={challenger_label} ({challenger_status}, cagr={challenger_cagr_part}) | "
        f"hold36_ceiling={result.get('hold36_status_band', 'unknown')}/{result.get('hold36_primary_blocker', 'unknown')} "
        f"(do_not_repeat={result.get('hold36_do_not_repeat_local_loop', False)}) | "
        f"next_near_miss={result['highest_priority_near_miss']} ({result['near_miss_status']})"
        + (
            f" | attack_challenger_next={result['attack_challenger_next_step']}"
            if result.get("attack_challenger_next_step")
            else ""
        )
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = check_research_stack_health(analysis_dir=args.analysis_dir)
    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print(render_research_stack_health_line(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
