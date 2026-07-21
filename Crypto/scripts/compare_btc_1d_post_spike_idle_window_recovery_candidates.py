from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.post_spike_active_candidate import ACTIVE_CHALLENGER_LABEL

ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest(pattern: str) -> Path:
    matches = sorted(
        ANALYSIS_DIR.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not matches:
        raise FileNotFoundError(f"No analysis artifact matched pattern: {pattern}")
    return matches[0]


def _rank_key(row: dict) -> tuple[float, float, float]:
    return (
        float(row.get("base_cagr", 0.0)),
        float(row.get("base_sharpe", 0.0)),
        -float(row.get("sensitivity_max_drift", 0.0)),
    )


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    repair_batch = _load_json(
        analysis_dir / "btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch_latest.json"
    )
    active_stage_review = _load_json(
        analysis_dir / "btc_1d_post_spike_consolidation_breakout_candidate_stage_review_latest.json"
    )

    active_profile = dict(active_stage_review.get("candidate_profile", {}) or {})
    active_idle_windows = list(active_profile.get("idle_walk_forward_windows", []))
    active_negative_windows = list(active_profile.get("negative_walk_forward_windows", []))
    active_candidate_label = str(active_profile.get("label", ""))
    repair_focus = dict(repair_batch.get("repair_focus", {}) or {})
    repair_anchor = str(repair_focus.get("active_anchor", ""))
    repair_batch_matches_active_candidate = (
        not repair_anchor or repair_anchor == active_candidate_label
    )
    rows = list(repair_batch.get("results", []) or [])
    ranked_rows = sorted(rows, key=_rank_key, reverse=True)

    recovery_candidates: list[dict] = []
    for row in ranked_rows:
        negative_windows = list(row.get("negative_windows", []))
        idle_windows = list(row.get("idle_windows", []))
        recovery_candidates.append(
            {
                "variant_label": str(row.get("variant_label", "")),
                "base_cagr": float(row.get("base_cagr", 0.0)),
                "base_sharpe": float(row.get("base_sharpe", 0.0)),
                "base_max_drawdown": float(row.get("base_max_drawdown", 0.0)),
                "sensitivity_max_drift": float(row.get("sensitivity_max_drift", 0.0)),
                "negative_windows": negative_windows,
                "idle_windows": idle_windows,
                "same_negative_profile_as_active": negative_windows == active_negative_windows,
                "same_idle_profile_as_active": idle_windows == active_idle_windows,
                "cagr_delta_vs_active": float(row.get("base_cagr", 0.0))
                - float(active_profile.get("paper_validation_cagr", 0.0)),
                "sharpe_delta_vs_active": float(row.get("base_sharpe", 0.0))
                - float(active_profile.get("paper_validation_sharpe", 0.0)),
            }
        )

    same_profile_candidates = [
        row
        for row in recovery_candidates
        if row["same_negative_profile_as_active"] and row["same_idle_profile_as_active"]
    ]
    top_same_profile = same_profile_candidates[0] if same_profile_candidates else recovery_candidates[0]
    top_variant_matches_active = (
        top_same_profile["variant_label"] == ACTIVE_CHALLENGER_LABEL.removeprefix("post_spike_")
    )
    recommend_rotation_review = (
        repair_batch_matches_active_candidate
        and not top_variant_matches_active
        and top_same_profile["cagr_delta_vs_active"] > 0.0
    )
    next_step_now = (
        "expand_post_spike_trend_family_to_recover_idle_windows"
        if not repair_batch_matches_active_candidate
        else "validate_top_idle_window_recovery_variant_against_active_challenger"
        if recommend_rotation_review
        else "keep_active_challenger_and_open_new_idle_window_axis"
    )

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "active_challenger_reference": {
            "label": ACTIVE_CHALLENGER_LABEL,
            "candidate_label": str(active_profile.get("label", "")),
            "paper_validation_cagr": float(active_profile.get("paper_validation_cagr", 0.0)),
            "paper_validation_sharpe": float(active_profile.get("paper_validation_sharpe", 0.0)),
            "paper_validation_max_drawdown": float(
                active_profile.get("paper_validation_max_drawdown", 0.0)
            ),
            "sensitivity_max_drift": float(
                active_profile.get("walk_forward_sensitivity_max_drift", 0.0)
            ),
            "negative_walk_forward_windows": active_negative_windows,
            "idle_walk_forward_windows": active_idle_windows,
        },
        "repair_batch_context": {
            "active_anchor": repair_anchor,
            "repair_batch_matches_active_candidate": repair_batch_matches_active_candidate,
            "selected_variant_labels": list(repair_focus.get("selected_variant_labels", [])),
        },
        "idle_window_recovery_candidates": recovery_candidates,
        "idle_window_recovery_verdict": {
            "top_same_profile_variant": top_same_profile["variant_label"],
            "recommend_rotation_review": recommend_rotation_review,
            "next_step_now": next_step_now,
            "reason": (
                f"The latest repair batch is still anchored to `{repair_anchor}`, not the active candidate `{active_candidate_label}`, so open a new trend-family idle-window recovery search from the current challenger baseline."
                if not repair_batch_matches_active_candidate
                else
                f"{top_same_profile['variant_label']} keeps the same idle/negative-window profile as the active challenger "
                f"while improving CAGR by {top_same_profile['cagr_delta_vs_active']:.4f}."
                if recommend_rotation_review
                else "No same-profile repair-batch variant clearly beats the active challenger, so keep the slot stable and search a wider idle-window recovery axis."
            ),
        },
        "decision_summary": [
            f"Treat `{ACTIVE_CHALLENGER_LABEL}` as the current attack challenger reference.",
            (
                f"Do not open a direct rotation review off this repair batch because it is anchored to `{repair_anchor}` instead of `{active_candidate_label}`."
                if not repair_batch_matches_active_candidate
                else
                f"Open a rotation review for `{top_same_profile['variant_label']}` because it improves CAGR without worsening the current idle-window profile."
                if recommend_rotation_review
                else "Keep the active challenger in place because the repair batch did not surface a clearly stronger same-profile replacement."
            ),
            f"Next attack research step: `{next_step_now}`.",
        ],
    }


def _render_markdown(report: dict) -> str:
    active = report["active_challenger_reference"]
    batch = report["repair_batch_context"]
    verdict = report["idle_window_recovery_verdict"]
    lines = [
        "# BTC 1d Post-Spike Idle Window Recovery Candidates",
        "",
        f"- Active challenger: `{active['label']}`",
        f"- Active candidate label: `{active['candidate_label']}`",
        f"- Active CAGR: `{active['paper_validation_cagr']:.4f}`",
        f"- Active Sharpe: `{active['paper_validation_sharpe']:.4f}`",
        f"- Active idle windows: `{active['idle_walk_forward_windows']}`",
        f"- Repair-batch active anchor: `{batch['active_anchor']}`",
        f"- Repair batch matches active candidate: `{batch['repair_batch_matches_active_candidate']}`",
        f"- Top same-profile variant: `{verdict['top_same_profile_variant']}`",
        f"- Recommend rotation review: `{verdict['recommend_rotation_review']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Candidates",
    ]
    for row in report["idle_window_recovery_candidates"]:
        lines.extend(
            [
                f"- `{row['variant_label']}` | CAGR=`{row['base_cagr']:.4f}` | Sharpe=`{row['base_sharpe']:.4f}` | MDD=`{row['base_max_drawdown']:.4f}`",
                f"  drift=`{row['sensitivity_max_drift']:.4f}` | idle_windows=`{row['idle_windows']}` | negative_windows=`{row['negative_windows']}`",
                f"  cagr_delta_vs_active=`{row['cagr_delta_vs_active']:.4f}` | sharpe_delta_vs_active=`{row['sharpe_delta_vs_active']:.4f}`",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_idle_window_recovery_candidates_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_idle_window_recovery_candidates_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_post_spike_idle_window_recovery_candidates_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_post_spike_idle_window_recovery_candidates_md_latest.md"
    json_payload = json.dumps(report, indent=2)
    md_payload = _render_markdown(report)
    json_path.write_text(json_payload, encoding="utf-8")
    md_path.write_text(md_payload, encoding="utf-8")
    latest_json.write_text(json_payload, encoding="utf-8")
    latest_md.write_text(md_payload, encoding="utf-8")
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
