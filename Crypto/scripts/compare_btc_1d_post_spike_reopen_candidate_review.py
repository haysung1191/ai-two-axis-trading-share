from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_main_pressure_axis_closure_review import (
    build_report as build_axis_closure_review,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_json(prefix: str) -> Path:
    matches = sorted(ANALYSIS_DIR.glob(f"{prefix}*.json"))
    if not matches:
        raise FileNotFoundError(f"No analysis result found for prefix: {prefix}")
    return matches[-1]


def _repair_winner_candidate() -> dict:
    payload = _load_json(ANALYSIS_DIR / "btc_1d_post_spike_consolidation_breakout_repair_winner_stage_review_latest.json")
    profile = payload["repair_winner_profile"]
    verdict = payload["repair_winner_stage_verdict"]
    return {
        "candidate_label": str(profile["candidate_label"]),
        "source": "repair_winner_stage_review",
        "base_cagr": float(profile["validation_cagr"]),
        "base_sharpe": float(profile["validation_sharpe"]),
        "base_max_drawdown": float(profile["validation_max_drawdown"]),
        "sensitivity_max_drift": float(profile["walk_forward_sensitivity_max_drift"]),
        "negative_window_count": len(list(profile.get("negative_walk_forward_windows", []) or [])),
        "candidate_stage_ready": bool(verdict["candidate_stage_ready"]),
        "reopen_reason": "stage_ready_repair_winner",
        "source_json": str(ANALYSIS_DIR / "btc_1d_post_spike_consolidation_breakout_repair_winner_stage_review_latest.json"),
    }


def _frontier_candidates() -> list[dict]:
    payload = _load_json(_latest_json("btc_1d_post_spike_exit_tradeoff_frontier_"))
    rows = []
    for item in payload.get("pareto_frontier", []):
        rows.append(
            {
                "candidate_label": str(item["variant_label"]),
                "source": str(item["source"]),
                "base_cagr": float(item["base_cagr"]),
                "base_sharpe": float(item["base_sharpe"]),
                "base_max_drawdown": float(item["base_max_drawdown"]),
                "sensitivity_max_drift": float(item["sensitivity_max_drift"]),
                "negative_window_count": int(item["negative_window_count"]),
                "candidate_stage_ready": bool(item["rotation_gap_passed"]),
                "drift_guardrail_passed": bool(item["drift_guardrail_passed"]),
                "exact_hit": bool(item["rotation_gap_passed"]) and bool(item["drift_guardrail_passed"]) and int(item["negative_window_count"]) == 0,
                "reopen_reason": (
                    "frontier_exact_hit"
                    if bool(item["rotation_gap_passed"]) and bool(item["drift_guardrail_passed"]) and int(item["negative_window_count"]) == 0
                    else "frontier_candidate_with_drift_guardrail"
                    if bool(item["drift_guardrail_passed"])
                    else "frontier_candidate_gap_only"
                ),
                "source_json": str(item["source_json"]),
            }
        )
    return rows


def build_report() -> dict:
    closure = build_axis_closure_review()
    repair = _repair_winner_candidate()
    frontier = _frontier_candidates()
    frontier_payload = _load_json(_latest_json("btc_1d_post_spike_exit_tradeoff_frontier_"))
    frontier_verdict = dict(frontier_payload.get("frontier_verdict", {}))

    frontier_sorted = sorted(
        frontier,
        key=lambda item: (
            not bool(item.get("exact_hit", False)),
            not bool(item.get("drift_guardrail_passed", False)),
            not bool(item["candidate_stage_ready"]),
            int(item["negative_window_count"]),
            -float(item["base_cagr"]),
            float(item["sensitivity_max_drift"]),
        ),
    )
    top_frontier = frontier_sorted[:3]

    reopen_candidates = [repair, *top_frontier]
    exact_hit = next((candidate for candidate in frontier_sorted if bool(candidate.get("exact_hit", False))), None)
    if exact_hit is not None or bool(frontier_verdict.get("exact_hit_found", False)):
        next_step_now = "promote_exact_hit_into_rotation_review"
        preferred_seed = str((exact_hit or top_frontier[0])["candidate_label"])
    else:
        next_step_now = "reopen_candidate_search_outside_hold36_local_axes"
        preferred_seed = repair["candidate_label"] if repair["candidate_stage_ready"] else top_frontier[0]["candidate_label"]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "reopen_reference": {
            "attack_main": closure["closure_reference"]["attack_main"],
            "promoted_backup": closure["closure_reference"]["promoted_backup"],
            "monitoring_candidate": closure["closure_reference"]["monitoring_candidate"],
            "current_hold36_line_closed": closure["axis_closure_summary"]["all_current_hold36_axes_closed"],
        },
        "reopen_gate": {
            "remaining_base_cagr_gap": closure["open_blocker_state"]["remaining_base_cagr_gap"],
            "remaining_cost20_cagr_gap": closure["open_blocker_state"]["remaining_cost20_cagr_gap"],
            "next_step_now": next_step_now,
            "preferred_reopen_seed": preferred_seed,
        },
        "reopen_candidates": reopen_candidates,
        "decision_summary": [
            (
                "An exact frontier hit now exists, so the next step is promotion review rather than another reopen search."
                if next_step_now == "promote_exact_hit_into_rotation_review"
                else "The current hold36 local axis family is closed, so the next step is to reopen candidate search outside that family."
            ),
            f"Preferred reopen seed is `{preferred_seed}` based on the strongest currently available external evidence.",
            (
                f"Remaining blocker is still base CAGR gap `{closure['open_blocker_state']['remaining_base_cagr_gap']:.6f}`."
                if next_step_now != "promote_exact_hit_into_rotation_review"
                else "The remaining task is to convert the exact-hit candidate into the promotion and rotation review lane."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    gate = report["reopen_gate"]
    lines = [
        "# BTC 1d Post-Spike Reopen Candidate Review",
        "",
        f"- Attack main: `{report['reopen_reference']['attack_main']}`",
        f"- Promoted backup: `{report['reopen_reference']['promoted_backup']}`",
        f"- Monitoring candidate: `{report['reopen_reference']['monitoring_candidate']}`",
        f"- Current hold36 line closed: `{report['reopen_reference']['current_hold36_line_closed']}`",
        f"- Remaining base CAGR gap: `{gate['remaining_base_cagr_gap']}`",
        f"- Next step now: `{gate['next_step_now']}`",
        f"- Preferred reopen seed: `{gate['preferred_reopen_seed']}`",
        "",
        "## Reopen Candidates",
    ]
    for candidate in report["reopen_candidates"]:
        lines.append(
            f"- `{candidate['candidate_label']}` | source=`{candidate['source']}` "
            f"cagr=`{candidate['base_cagr']}` sharpe=`{candidate['base_sharpe']}` "
            f"mdd=`{candidate['base_max_drawdown']}` drift=`{candidate['sensitivity_max_drift']}` "
            f"reason=`{candidate['reopen_reason']}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_reopen_candidate_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_reopen_candidate_review_{stamp}.md"
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
