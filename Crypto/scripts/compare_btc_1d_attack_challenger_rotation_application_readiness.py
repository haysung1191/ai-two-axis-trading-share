from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.attack_active_stack import ACTIVE_ATTACK_CHALLENGER_LABEL

ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _candidate_artifact_prefix(candidate: dict) -> str:
    params = dict(candidate.get("parameters", {}))
    trend = int(round(float(params.get("trend_ema_window", 0)) * 10))
    depth = int(round(float(params.get("max_consolidation_depth_pct", 0.0)) * 1000))
    volume = int(round(float(params.get("min_volume_ratio", 0.0)) * 100))
    hold = int(round(float(params.get("max_hold_bars", 0.0))))
    return f"btcusdt_1d_2200_trend{trend}_depth{depth:03d}_volume{volume:03d}_hold{hold}"


def _candidate_label_from_prefix(artifact_prefix: str) -> str:
    return f"post_spike_consolidation_breakout_{artifact_prefix.removeprefix('btcusdt_1d_2200_')}"


def _challenger_label_from_prefix(artifact_prefix: str) -> str:
    return f"post_spike_{artifact_prefix.removeprefix('btcusdt_1d_2200_')}"


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    promotion = _load_json(analysis_dir / "btc_1d_attack_challenger_promotion_review_latest.json")
    candidate = dict(promotion.get("approved_candidate_snapshot") or {})
    review = dict(promotion["promotion_review"])

    artifact_prefix = _candidate_artifact_prefix(candidate) if candidate else None
    candidate_label = _candidate_label_from_prefix(artifact_prefix) if artifact_prefix else None
    challenger_label = _challenger_label_from_prefix(artifact_prefix) if artifact_prefix else None
    rotation_already_applied = challenger_label == ACTIVE_ATTACK_CHALLENGER_LABEL and challenger_label is not None

    paper_validation_matches = (
        sorted(analysis_dir.glob(f"btc_1d_post_spike_consolidation_breakout_v4_{artifact_prefix}_paper_validation_*.json"))
        if artifact_prefix
        else []
    )
    friction_latest = analysis_dir / "btc_1d_post_spike_consolidation_breakout_friction_latest.json"
    walk_forward_matches = (
        sorted(analysis_dir.glob("btc_1d_walk_forward_diagnostic_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if artifact_prefix
        else []
    )
    walk_forward_match = None
    for path in walk_forward_matches:
        payload = _load_json(path)
        if str(payload.get("config", {}).get("candidate_label")) == candidate_label:
            walk_forward_match = path
            break

    stage_review_latest = analysis_dir / "btc_1d_post_spike_consolidation_breakout_candidate_stage_review_latest.json"
    stage_review_payload = _load_json(stage_review_latest) if stage_review_latest.exists() else {}
    latest_stage_review_matches_candidate = (
        str((stage_review_payload.get("candidate_profile", {}) or {}).get("label")) == candidate_label
    )

    readiness_checks = [
        {
            "name": "promotion_review_approved",
            "passed": bool(review.get("promote_attack_challenger_now")) or rotation_already_applied,
            "detail": "Promotion review must approve the challenger switch.",
        },
        {
            "name": "candidate_label_derivable",
            "passed": candidate_label is not None and challenger_label is not None,
            "detail": "Approved candidate must map to canonical candidate and challenger labels.",
        },
        {
            "name": "paper_validation_artifact_exists",
            "passed": bool(paper_validation_matches),
            "detail": "A canonical paper-validation artifact must exist for the approved candidate.",
        },
        {
            "name": "walk_forward_artifact_exists",
            "passed": walk_forward_match is not None,
            "detail": "A canonical walk-forward artifact must exist for the approved candidate label.",
        },
        {
            "name": "candidate_stage_review_is_aligned",
            "passed": latest_stage_review_matches_candidate,
            "detail": "Latest candidate-stage review must already point at the approved candidate label.",
        },
    ]
    failed_checks = [check["name"] for check in readiness_checks if not check["passed"]]
    ready_to_apply = not failed_checks and not rotation_already_applied

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "source_artifact": str(analysis_dir / "btc_1d_attack_challenger_promotion_review_latest.json"),
        "approved_candidate_mapping": {
            "approved_attack_challenger": review.get("approved_attack_challenger"),
            "candidate_label": candidate_label,
            "challenger_label": challenger_label,
            "artifact_prefix": artifact_prefix,
        },
        "application_readiness": {
            "ready_to_apply_rotation": ready_to_apply,
            "rotation_already_applied": rotation_already_applied,
            "failed_checks": failed_checks,
            "next_step_now": (
                "monitor_active_post_spike_challenger_against_attack_stack"
                if rotation_already_applied
                else
                "apply_approved_attack_challenger_rotation"
                if ready_to_apply
                else "publish_canonical_hold36_candidate_artifacts_before_rotation"
            ),
            "reason": (
                f"{challenger_label} is already installed as the active attack challenger, so artifact alignment is now a monitoring surface rather than a rotation blocker."
                if rotation_already_applied
                else
                f"Canonical candidate artifacts are aligned for {review.get('approved_attack_challenger')}, so the attack challenger rotation can be applied."
                if ready_to_apply
                else "The challenger switch is approved, but canonical post-spike candidate artifacts are not fully aligned for an active constant flip yet."
            ),
        },
        "artifact_evidence": {
            "paper_validation_matches": [str(path) for path in paper_validation_matches],
            "walk_forward_match": str(walk_forward_match) if walk_forward_match is not None else None,
            "candidate_stage_review_latest": str(stage_review_latest) if stage_review_latest.exists() else None,
            "candidate_stage_review_matches_candidate": latest_stage_review_matches_candidate,
            "friction_latest": str(friction_latest) if friction_latest.exists() else None,
        },
        "readiness_checks": readiness_checks,
        "decision_summary": [
            f"Use `{review.get('approved_attack_challenger')}` as the approved challenger target for application readiness.",
            (
                "The active challenger rotation is already applied."
                if rotation_already_applied
                else
                "The active challenger rotation can be applied now."
                if ready_to_apply
                else "Do not flip the active challenger constant yet; publish aligned candidate artifacts first."
            ),
            (
                "Next attack research step: `monitor_active_post_spike_challenger_against_attack_stack`."
                if rotation_already_applied
                else
                "Next attack research step: `apply_approved_attack_challenger_rotation`."
                if ready_to_apply
                else "Next attack research step: `publish_canonical_hold36_candidate_artifacts_before_rotation`."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    mapping = report["approved_candidate_mapping"]
    readiness = report["application_readiness"]
    lines = [
        "# BTC 1d Attack Challenger Rotation Application Readiness",
        "",
        f"- Approved attack challenger: `{mapping['approved_attack_challenger']}`",
        f"- Candidate label: `{mapping['candidate_label']}`",
        f"- Challenger label: `{mapping['challenger_label']}`",
        f"- Artifact prefix: `{mapping['artifact_prefix']}`",
        f"- Ready to apply rotation: `{readiness['ready_to_apply_rotation']}`",
        f"- Failed checks: `{readiness['failed_checks']}`",
        f"- Next step now: `{readiness['next_step_now']}`",
        f"- Reason: {readiness['reason']}",
        "",
        "## Checks",
    ]
    for check in report["readiness_checks"]:
        lines.append(f"- `{check['name']}`: passed=`{check['passed']}` | {check['detail']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_challenger_rotation_application_readiness_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_challenger_rotation_application_readiness_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_attack_challenger_rotation_application_readiness_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_attack_challenger_rotation_application_readiness_md_latest.md"
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
