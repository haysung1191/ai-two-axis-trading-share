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


def _challenger_label_from_candidate(candidate: dict | None) -> str | None:
    if not candidate:
        return None
    params = dict(candidate.get("parameters", {}))
    if not params:
        return None
    trend = int(round(float(params.get("trend_ema_window", 0.0)) * 10))
    depth = int(round(float(params.get("max_consolidation_depth_pct", 0.0)) * 1000))
    volume = int(round(float(params.get("min_volume_ratio", 0.0)) * 100))
    hold = int(round(float(params.get("max_hold_bars", 0.0))))
    return f"post_spike_trend{trend}_depth{depth:03d}_volume{volume:03d}_hold{hold}"


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    validation = _load_json(analysis_dir / "btc_1d_attack_challenger_validation_review_latest.json")
    active_label = str(validation["active_challenger_reference"]["label"])
    review = dict(validation["validation_review"])
    candidate = validation.get("validated_candidate")
    approved_challenger_label = _challenger_label_from_candidate(candidate)

    rotation_already_applied = approved_challenger_label == ACTIVE_ATTACK_CHALLENGER_LABEL and approved_challenger_label is not None
    promote_now = bool(review.get("approve_rotation_now")) and candidate is not None and not rotation_already_applied
    promoted_label = str(review["candidate_label"]) if candidate is not None else active_label

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "source_artifact": str(analysis_dir / "btc_1d_attack_challenger_validation_review_latest.json"),
        "current_attack_stack": {
            "active_attack_challenger": ACTIVE_ATTACK_CHALLENGER_LABEL,
            "validated_active_reference": active_label,
        },
        "promotion_review": {
            "promote_attack_challenger_now": promote_now,
            "rotation_already_applied": rotation_already_applied,
            "current_attack_challenger": ACTIVE_ATTACK_CHALLENGER_LABEL if rotation_already_applied else active_label,
            "approved_attack_challenger": promoted_label,
            "stack_constant_update_required": promote_now,
            "next_step_now": (
                "monitor_active_post_spike_challenger_against_attack_stack"
                if rotation_already_applied
                else
                "apply_approved_attack_challenger_rotation"
                if promote_now
                else "keep_current_attack_challenger"
            ),
            "reason": (
                f"{ACTIVE_ATTACK_CHALLENGER_LABEL} is already installed as the active attack challenger, so no further stack constant update is required."
                if rotation_already_applied
                else
                f"{promoted_label} is approved in the challenger validation review and should replace {active_label} in the active attack stack."
                if promote_now
                else f"{active_label} remains the active attack challenger because no approved replacement exists."
            ),
        },
        "approved_candidate_snapshot": candidate,
        "decision_summary": [
            (
                f"Treat `{ACTIVE_ATTACK_CHALLENGER_LABEL}` as the current active attack challenger reference."
                if rotation_already_applied
                else f"Treat `{active_label}` as the current active attack challenger reference."
            ),
            (
                f"`{ACTIVE_ATTACK_CHALLENGER_LABEL}` is already the promoted attack challenger."
                if rotation_already_applied
                else
                f"Approve `{promoted_label}` as the promoted attack challenger and prepare the stack constant update."
                if promote_now
                else f"Keep `{active_label}` as the active attack challenger."
            ),
            (
                "Next attack research step: `monitor_active_post_spike_challenger_against_attack_stack`."
                if rotation_already_applied
                else
                "Next attack research step: `apply_approved_attack_challenger_rotation`."
                if promote_now
                else "Next attack research step: `keep_current_attack_challenger`."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    review = report["promotion_review"]
    lines = [
        "# BTC 1d Attack Challenger Promotion Review",
        "",
        f"- Current attack challenger: `{review['current_attack_challenger']}`",
        f"- Approved attack challenger: `{review['approved_attack_challenger']}`",
        f"- Promote attack challenger now: `{review['promote_attack_challenger_now']}`",
        f"- Stack constant update required: `{review['stack_constant_update_required']}`",
        f"- Next step now: `{review['next_step_now']}`",
        f"- Reason: {review['reason']}",
        "",
    ]
    candidate = report["approved_candidate_snapshot"]
    if candidate is not None:
        lines.extend(
            [
                "## Approved Candidate",
                f"- Variant: `{candidate['variant_label']}`",
                f"- CAGR: `{candidate['base_cagr']}`",
                f"- Sharpe: `{candidate['base_sharpe']}`",
                f"- MDD: `{candidate['base_max_drawdown']}`",
                f"- Drift: `{candidate['sensitivity_max_drift']}`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_challenger_promotion_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_challenger_promotion_review_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_attack_challenger_promotion_review_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_attack_challenger_promotion_review_md_latest.md"
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
