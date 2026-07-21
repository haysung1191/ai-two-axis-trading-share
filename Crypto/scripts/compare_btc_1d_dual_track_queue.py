from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_experiment_spec import build_report as build_attack_experiment_spec
from scripts.compare_btc_1d_new_family_search_queue import build_report as build_new_family_search_queue


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report() -> dict:
    attack_spec = build_attack_experiment_spec()
    new_family_queue = build_new_family_search_queue()
    hold36_handoff = _load_json(ANALYSIS_DIR / "btc_1d_hold36_local_ceiling_handoff_latest.json")
    rotation_review = _load_json(ANALYSIS_DIR / "btc_1d_attack_challenger_rotation_review_latest.json")

    cagr_lane = new_family_queue["next_family_lane"]
    cagr_verdict = new_family_queue["queue_verdict"]
    mdd_spec = attack_spec["experiment_spec"]
    mdd_mutations = attack_spec["mutation_plan"]["primary_mutation_axes"]
    rotation_gate = rotation_review["rotation_gate"]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "queue_mode": "dual_track_autonomous",
        "constraints": {
            "hold36_ceiling_confirmed": bool(hold36_handoff["local_ceiling_status"]["ceiling_confirmed"]),
            "hold36_next_step": hold36_handoff["local_ceiling_status"]["next_step_now"],
            "do_not_restart_local_axes": list(hold36_handoff["handoff_rules"]["do_not_restart"]),
            "rotation_gate_open": bool(rotation_gate["gate_open"]),
            "rotation_blockers": list(rotation_gate["blocking_reasons"]),
        },
        "cagr_track": {
            "track_name": "cagr_maximization",
            "lane": cagr_lane["label"],
            "category": cagr_lane["category"],
            "queue_mode": new_family_queue["search_queue_summary"]["queue_mode"],
            "next_step_now": cagr_verdict["next_step_now"],
            "runner_sequence": [
                row["runner"] for row in new_family_queue["repair_queue"]["execution_sequence"]
            ],
            "advance_condition": cagr_verdict["advance_condition"],
            "selected_reason": cagr_verdict["selected_reason"],
        },
        "mdd_track": {
            "track_name": "drawdown_minimization",
            "primary_label": mdd_spec["primary_label"],
            "primary_family": mdd_spec["primary_family"],
            "goal": mdd_spec["primary_goal"],
            "mutation_axes": [
                {
                    "axis": row["axis"],
                    "runner": row["runner"],
                    "reason": row["reason"],
                }
                for row in mdd_mutations
            ],
            "validation_sequence": [
                row["runner"] for row in attack_spec["mutation_plan"]["validation_sequence"]
            ],
            "success_gate": dict(attack_spec["success_gate"]),
        },
        "bridge_context": {
            "deferred_seed_label": new_family_queue["transition_context"]["deferred_seed_label"],
            "rotation_candidate": rotation_review["rotation_candidate"]["variant_label"],
            "rotation_next_step": rotation_review["rotation_gate"]["next_step_now"],
            "current_attack_challenger": rotation_review["rotation_review"]["current_attack_challenger"],
            "proposed_attack_challenger": rotation_review["rotation_review"]["proposed_attack_challenger"],
        },
        "decision_summary": [
            (
                f"CAGR track opens on `{cagr_lane['label']}` because the hold36 local loop is explicitly closed and the "
                f"queue now prefers `{cagr_verdict['next_step_now']}`."
            ),
            (
                f"MDD track stays on `{mdd_spec['primary_label']}` because the primary goal is still "
                f"`{mdd_spec['primary_goal']}`."
            ),
            (
                "Do not restart the closed hold36 local axes; use the CAGR lane for wider-family search and the MDD lane "
                "for drawdown compression retests."
            ),
            (
                f"Keep challenger rotation in review only: blockers remain `{', '.join(rotation_gate['blocking_reasons'])}`."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    constraints = report["constraints"]
    cagr_track = report["cagr_track"]
    mdd_track = report["mdd_track"]
    bridge = report["bridge_context"]
    lines = [
        "# BTC 1d Dual Track Queue",
        "",
        f"- Queue mode: `{report['queue_mode']}`",
        f"- Hold36 next step: `{constraints['hold36_next_step']}`",
        f"- Rotation blockers: `{', '.join(constraints['rotation_blockers'])}`",
        "",
        "## CAGR Track",
        f"- Lane: `{cagr_track['lane']}`",
        f"- Category: `{cagr_track['category']}`",
        f"- Queue mode: `{cagr_track['queue_mode']}`",
        f"- Next step now: `{cagr_track['next_step_now']}`",
        f"- Advance condition: {cagr_track['advance_condition']}",
        f"- Selected reason: {cagr_track['selected_reason']}",
        "",
        "## MDD Track",
        f"- Primary label: `{mdd_track['primary_label']}`",
        f"- Primary family: `{mdd_track['primary_family']}`",
        f"- Goal: `{mdd_track['goal']}`",
        "",
        "## Bridge Context",
        f"- Deferred seed: `{bridge['deferred_seed_label']}`",
        f"- Current attack challenger: `{bridge['current_attack_challenger']}`",
        f"- Proposed attack challenger: `{bridge['proposed_attack_challenger']}`",
        f"- Rotation candidate: `{bridge['rotation_candidate']}`",
        f"- Rotation next step: `{bridge['rotation_next_step']}`",
        "",
        "## Runner Queue",
    ]
    for runner in cagr_track["runner_sequence"]:
        lines.append(f"- CAGR: `{runner}`")
    for row in mdd_track["mutation_axes"]:
        lines.append(f"- MDD mutate `{row['axis']}`: `{row['runner']}`")
    for runner in mdd_track["validation_sequence"]:
        lines.append(f"- MDD validate: `{runner}`")
    lines.extend(["", "## Decision Summary"])
    lines.extend(f"- {line}" for line in report["decision_summary"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_dual_track_queue_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_dual_track_queue_{stamp}.md"
    latest_json_path = ANALYSIS_DIR / "btc_1d_dual_track_queue_latest.json"
    latest_md_path = ANALYSIS_DIR / "btc_1d_dual_track_queue_md_latest.md"
    payload = json.dumps(report, indent=2)
    markdown = _render_markdown(report)
    json_path.write_text(payload, encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    latest_json_path.write_text(payload, encoding="utf-8")
    latest_md_path.write_text(markdown, encoding="utf-8")
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
