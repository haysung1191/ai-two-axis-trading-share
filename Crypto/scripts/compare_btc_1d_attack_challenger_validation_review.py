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
    drift_repair = _load_json(analysis_dir / "btc_1d_post_spike_hold36_drift_repair_candidates_latest.json")
    active = dict(drift_repair["active_challenger_reference"])
    repair_candidates = list(drift_repair.get("hold36_drift_repair_candidates", []))
    verdict = dict(drift_repair["drift_repair_verdict"])
    candidate_label = verdict.get("top_candidate")
    candidate = next(
        (row for row in repair_candidates if str(row.get("variant_label")) == str(candidate_label)),
        None,
    )

    approved_challenger_label = _challenger_label_from_candidate(candidate)
    rotation_already_applied = approved_challenger_label == ACTIVE_ATTACK_CHALLENGER_LABEL
    approve_rotation_now = bool(candidate and candidate.get("beats_active_rotation_gate")) and not rotation_already_applied
    keep_current_challenger = not approve_rotation_now
    next_step_now = (
        "monitor_active_post_spike_challenger_against_attack_stack"
        if rotation_already_applied
        else "approve_hold36_drift_repair_challenger_rotation"
        if approve_rotation_now
        else "keep_active_challenger_and_continue_validation"
    )

    approval_checks = []
    if candidate is not None:
        approval_checks = [
            {
                "name": "candidate_clears_rotation_gate",
                "passed": bool(candidate["beats_active_rotation_gate"]),
                "detail": "Candidate must clear the drift-repair rotation gate.",
            },
            {
                "name": "cagr_above_active",
                "passed": float(candidate["cagr_delta_vs_active"]) > 0.0,
                "detail": "Candidate must improve CAGR versus the active challenger.",
            },
            {
                "name": "sharpe_above_active",
                "passed": float(candidate["sharpe_delta_vs_active"]) > 0.0,
                "detail": "Candidate must improve Sharpe versus the active challenger.",
            },
            {
                "name": "drawdown_not_worse",
                "passed": float(candidate["max_drawdown_delta_vs_active"]) >= 0.0,
                "detail": "Candidate must not worsen max drawdown versus the active challenger.",
            },
            {
                "name": "drift_above_active",
                "passed": float(candidate["drift_delta_vs_active"]) >= 0.0,
                "detail": "Candidate must improve walk-forward drift versus the active challenger.",
            },
        ]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "source_artifact": str(
            analysis_dir / "btc_1d_post_spike_hold36_drift_repair_candidates_latest.json"
        ),
        "active_challenger_reference": active,
        "validated_candidate": candidate,
        "validation_review": {
            "candidate_found": candidate is not None,
            "candidate_label": candidate_label,
            "approve_rotation_now": approve_rotation_now,
            "rotation_already_applied": rotation_already_applied,
            "keep_current_challenger_until_switch": keep_current_challenger,
            "proposed_attack_challenger": (
                candidate_label
                if approve_rotation_now
                else ACTIVE_ATTACK_CHALLENGER_LABEL
                if rotation_already_applied
                else active["label"]
            ),
            "next_step_now": next_step_now,
            "reason": (
                f"{ACTIVE_ATTACK_CHALLENGER_LABEL} already reflects the approved drift-repair challenger, so the next step is to monitor the live challenger profile."
                if rotation_already_applied
                else f"{candidate_label} improves CAGR, Sharpe, max drawdown, and drift versus {active['label']}, so the challenger rotation can be approved."
                if approve_rotation_now and candidate is not None
                else "No validated drift-repair candidate is strong enough to approve the challenger rotation yet."
            ),
        },
        "approval_checks": approval_checks,
        "decision_summary": [
            (
                f"Use `{ACTIVE_ATTACK_CHALLENGER_LABEL}` as the active attack challenger reference."
                if rotation_already_applied
                else f"Use `{active['label']}` as the active attack challenger reference."
            ),
            (
                f"`{ACTIVE_ATTACK_CHALLENGER_LABEL}` is already installed as the active attack challenger."
                if rotation_already_applied
                else f"Approve `{candidate_label}` as the next attack challenger."
                if approve_rotation_now and candidate is not None
                else f"Keep `{active['label']}` as the active challenger."
            ),
            f"Next attack research step: `{next_step_now}`.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    active = report["active_challenger_reference"]
    candidate = report["validated_candidate"]
    verdict = report["validation_review"]
    lines = [
        "# BTC 1d Attack Challenger Validation Review",
        "",
        f"- Active challenger: `{active['label']}`",
        f"- Candidate label: `{verdict['candidate_label']}`",
        f"- Approve rotation now: `{verdict['approve_rotation_now']}`",
        f"- Proposed attack challenger: `{verdict['proposed_attack_challenger']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
    ]
    if candidate is not None:
        lines.extend(
            [
                "## Candidate Metrics",
                f"- CAGR: `{candidate['base_cagr']}`",
                f"- Sharpe: `{candidate['base_sharpe']}`",
                f"- MDD: `{candidate['base_max_drawdown']}`",
                f"- Drift: `{candidate['sensitivity_max_drift']}`",
                f"- CAGR delta vs active: `{candidate['cagr_delta_vs_active']}`",
                f"- Sharpe delta vs active: `{candidate['sharpe_delta_vs_active']}`",
                f"- MDD delta vs active: `{candidate['max_drawdown_delta_vs_active']}`",
                f"- Drift delta vs active: `{candidate['drift_delta_vs_active']}`",
                "",
                "## Approval Checks",
            ]
        )
        for check in report["approval_checks"]:
            lines.append(f"- `{check['name']}`: passed=`{check['passed']}` | {check['detail']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_challenger_validation_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_challenger_validation_review_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_attack_challenger_validation_review_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_attack_challenger_validation_review_md_latest.md"
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
