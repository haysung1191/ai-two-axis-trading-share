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
from scripts.compare_btc_1d_post_spike_reopen_seed_attack_comparison import (
    build_report as build_reopen_seed_attack_comparison,
)


ANALYSIS_DIR = Path("analysis_results")


def build_report() -> dict:
    stack = build_attack_stack_screen()
    reopen = build_reopen_seed_attack_comparison()

    main = next(item for item in stack["compared_models"] if str(item["role"]) == "attack_main")
    active_backup = next(item for item in stack["compared_models"] if str(item["role"]) == "attack_backup")
    active_challenger = next(item for item in stack["compared_models"] if str(item["role"]) == "attack_challenger")
    metrics = dict(reopen["comparison_metrics"])
    reopen_status = dict(reopen["reopen_attack_comparison"])
    preferred_seed = str(reopen["reopen_seed_reference"]["preferred_seed_now"])
    backup_seed = str(reopen["reopen_seed_reference"]["backup_seed_now"])

    preferred_seed_promotes_into_backup = (
        bool(reopen_status["preferred_seed_has_clean_reopen"])
        and bool(reopen_status["preferred_seed_pressures_active_backup"])
    )
    challenger_stays_on_board = bool(reopen_status["backup_seed_is_viable"])
    active_backup_demotes_to_challenger = preferred_seed_promotes_into_backup

    board_lane = (
        "reopen_seed_backup_rotation_queue"
        if preferred_seed_promotes_into_backup
        else "reopen_seed_shadow_queue"
    )
    next_step_now = (
        "open_attack_backup_replacement_from_reopen_seed"
        if preferred_seed_promotes_into_backup
        else "keep_reopen_seed_as_shadow_candidate"
    )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "board_reference": dict(stack["stack_top"]),
        "reopen_seed_reference": dict(reopen["reopen_seed_reference"]),
        "reopen_seed_board_review": {
            "preferred_seed_promotes_into_backup": preferred_seed_promotes_into_backup,
            "active_backup_demotes_to_challenger": active_backup_demotes_to_challenger,
            "challenger_stays_on_board": challenger_stays_on_board,
            "proposed_attack_main": str(main["label"]),
            "proposed_attack_backup": preferred_seed if preferred_seed_promotes_into_backup else str(active_backup["label"]),
            "proposed_attack_challenger": str(active_backup["label"]) if active_backup_demotes_to_challenger else str(active_challenger["label"]),
            "secondary_shadow_seed": backup_seed,
            "board_lane": board_lane,
            "next_step_now": next_step_now,
        },
        "supporting_metrics": {
            "attack_main_base_cagr": float(main["base_cagr"]),
            "active_backup_base_cagr": float(active_backup["base_cagr"]),
            "active_challenger_base_cagr": float(active_challenger["base_cagr"]),
            "preferred_seed_base_cagr": float(metrics["preferred_seed_base_cagr"]),
            "preferred_seed_base_sharpe": float(metrics["preferred_seed_base_sharpe"]),
            "preferred_seed_base_mdd": float(metrics["preferred_seed_base_mdd"]),
            "preferred_seed_sensitivity_max_drift": float(metrics["preferred_seed_sensitivity_max_drift"]),
            "backup_seed_base_cagr": float(metrics["backup_seed_base_cagr"]),
            "backup_seed_base_sharpe": float(metrics["backup_seed_base_sharpe"]),
            "backup_seed_base_mdd": float(metrics["backup_seed_base_mdd"]),
        },
        "decision_summary": [
            (
                f"Promote `{preferred_seed}` into the attack backup comparison lane because it revalidated cleanly and now exceeds the active backup on base CAGR."
                if preferred_seed_promotes_into_backup
                else f"Keep `{preferred_seed}` outside the active board because it did not clear the backup pressure gate."
            ),
            f"Keep `{main['label']}` unchanged as attack main because the preferred reopen seed still trails the main on base CAGR.",
            f"Track `{backup_seed}` as the secondary shadow seed while the board reviews `{preferred_seed}` against the current backup/challenger layout.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    verdict = report["reopen_seed_board_review"]
    metrics = report["supporting_metrics"]
    lines = [
        "# BTC 1d Attack Reopen Seed Board Review",
        "",
        f"- Attack main: `{report['board_reference']['attack_main']}`",
        f"- Active backup: `{report['board_reference']['attack_backup']}`",
        f"- Active challenger: `{report['board_reference']['attack_challenger']}`",
        f"- Preferred reopen seed: `{report['reopen_seed_reference']['preferred_seed_now']}`",
        f"- Promote preferred seed into backup: `{verdict['preferred_seed_promotes_into_backup']}`",
        f"- Proposed attack backup: `{verdict['proposed_attack_backup']}`",
        f"- Proposed attack challenger: `{verdict['proposed_attack_challenger']}`",
        f"- Secondary shadow seed: `{verdict['secondary_shadow_seed']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        "",
        "## Metrics",
        f"- attack_main_base_cagr: `{metrics['attack_main_base_cagr']}`",
        f"- active_backup_base_cagr: `{metrics['active_backup_base_cagr']}`",
        f"- active_challenger_base_cagr: `{metrics['active_challenger_base_cagr']}`",
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
    json_path = ANALYSIS_DIR / f"btc_1d_attack_reopen_seed_board_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_reopen_seed_board_review_{stamp}.md"
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
