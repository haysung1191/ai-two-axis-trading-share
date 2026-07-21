from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _build_rotation_gate(
    *,
    active_reference: dict,
    candidate_summary: dict | None,
    open_rotation_review: bool,
) -> dict:
    if not open_rotation_review or candidate_summary is None:
        return {
            "gate_open": False,
            "approve_challenger_rotation_now": False,
            "manual_review_required": False,
            "blocking_reasons": ["no_rotation_candidate"],
            "checks": [],
            "next_step_now": "keep_active_challenger_and_continue_idle_window_search",
        }

    checks = [
        {
            "name": "same_negative_profile",
            "passed": bool(candidate_summary["same_negative_profile_as_active"]),
            "detail": "Candidate must preserve the active challenger's no-negative-window profile.",
        },
        {
            "name": "same_idle_profile",
            "passed": bool(candidate_summary["same_idle_profile_as_active"]),
            "detail": "Candidate must preserve the active challenger's idle-window footprint.",
        },
        {
            "name": "cagr_improves",
            "passed": float(candidate_summary["cagr_delta_vs_active"]) > 0.0,
            "detail": "Candidate must improve paper-validation CAGR versus the active challenger.",
        },
        {
            "name": "sharpe_improves",
            "passed": float(candidate_summary["sharpe_delta_vs_active"]) > 0.0,
            "detail": "Candidate should improve Sharpe versus the active challenger.",
        },
        {
            "name": "max_drawdown_not_worse",
            "passed": float(candidate_summary["max_drawdown_delta_vs_active"]) >= 0.0,
            "detail": "Candidate must not worsen max drawdown versus the active challenger.",
        },
        {
            "name": "drift_not_worse",
            "passed": candidate_summary["drift_delta_vs_active"] is not None
            and float(candidate_summary["drift_delta_vs_active"]) >= 0.0,
            "detail": "Candidate must not worsen walk-forward drift versus the active challenger.",
        },
    ]
    failed_checks = [check["name"] for check in checks if not check["passed"]]
    approve_now = not failed_checks
    next_step_now = (
        "approve_attack_challenger_rotation"
        if approve_now
        else "repair_hold36_drift_gap_before_rotation"
        if failed_checks == ["drift_not_worse"]
        else "hold_rotation_and_repair_failed_gate"
    )
    return {
        "gate_open": True,
        "approve_challenger_rotation_now": approve_now,
        "manual_review_required": not approve_now,
        "blocking_reasons": failed_checks,
        "checks": checks,
        "next_step_now": next_step_now,
    }


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    source = _load_json(analysis_dir / "btc_1d_post_spike_idle_window_recovery_candidates_latest.json")
    active_reference = dict(source["active_challenger_reference"])
    verdict = dict(source["idle_window_recovery_verdict"])
    candidates = list(source.get("idle_window_recovery_candidates", []))
    active_variant_label = str(active_reference["label"]).removeprefix("post_spike_")
    active_candidate = next(
        (row for row in candidates if str(row.get("variant_label")) == active_variant_label),
        None,
    )

    top_variant_label = verdict.get("top_same_profile_variant")
    top_candidate = next(
        (row for row in candidates if str(row.get("variant_label")) == str(top_variant_label)),
        None,
    )

    open_rotation_review = bool(verdict.get("recommend_rotation_review")) and top_candidate is not None
    next_step_now = (
        "open_attack_challenger_rotation_review"
        if open_rotation_review
        else "keep_active_challenger_and_continue_idle_window_search"
    )

    candidate_summary = None
    if top_candidate is not None:
        active_drift = (
            float(active_reference["sensitivity_max_drift"])
            if "sensitivity_max_drift" in active_reference
            else float(active_candidate["sensitivity_max_drift"])
            if active_candidate is not None
            else None
        )
        candidate_summary = {
            "variant_label": str(top_candidate["variant_label"]),
            "base_cagr": float(top_candidate["base_cagr"]),
            "base_sharpe": float(top_candidate["base_sharpe"]),
            "base_max_drawdown": float(top_candidate["base_max_drawdown"]),
            "sensitivity_max_drift": float(top_candidate["sensitivity_max_drift"]),
            "negative_windows": list(top_candidate.get("negative_windows", [])),
            "idle_windows": list(top_candidate.get("idle_windows", [])),
            "cagr_delta_vs_active": float(top_candidate.get("cagr_delta_vs_active", 0.0)),
            "sharpe_delta_vs_active": float(top_candidate.get("sharpe_delta_vs_active", 0.0)),
            "max_drawdown_delta_vs_active": (
                float(active_reference["paper_validation_max_drawdown"])
                - float(top_candidate["base_max_drawdown"])
            ),
            "drift_delta_vs_active": (
                active_drift - float(top_candidate["sensitivity_max_drift"])
                if active_drift is not None
                else None
            ),
            "same_negative_profile_as_active": list(top_candidate.get("negative_windows", []))
            == list(active_reference.get("negative_walk_forward_windows", [])),
            "same_idle_profile_as_active": list(top_candidate.get("idle_windows", []))
            == list(active_reference.get("idle_walk_forward_windows", [])),
        }
        if active_drift is not None:
            active_reference["sensitivity_max_drift"] = active_drift

    rotation_gate = _build_rotation_gate(
        active_reference=active_reference,
        candidate_summary=candidate_summary,
        open_rotation_review=open_rotation_review,
    )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "source_artifact": str(
            analysis_dir / "btc_1d_post_spike_idle_window_recovery_candidates_latest.json"
        ),
        "active_challenger_reference": active_reference,
        "rotation_candidate": candidate_summary,
        "rotation_review": {
            "open_rotation_review": open_rotation_review,
            "keep_attack_main_unchanged": True,
            "keep_attack_backup_unchanged": True,
            "keep_current_challenger_live_until_validation": True,
            "current_attack_challenger": str(active_reference["label"]),
            "proposed_attack_challenger": (
                candidate_summary["variant_label"]
                if candidate_summary is not None
                else str(active_reference["label"])
            ),
            "approve_challenger_rotation_now": bool(rotation_gate["approve_challenger_rotation_now"]),
            "manual_review_required": bool(rotation_gate["manual_review_required"]),
            "next_step_now": str(rotation_gate["next_step_now"]),
            "reason": (
                f"{candidate_summary['variant_label']} preserves the current idle/negative-window profile and improves CAGR by "
                f"{candidate_summary['cagr_delta_vs_active']:.4f} versus {active_reference['label']}, "
                f"but rotation is blocked by {', '.join(rotation_gate['blocking_reasons'])}."
                if open_rotation_review
                and candidate_summary is not None
                and rotation_gate["blocking_reasons"]
                else f"{candidate_summary['variant_label']} clears the challenger rotation gate and can replace {active_reference['label']}."
                if open_rotation_review and candidate_summary is not None
                else "No same-profile idle-window recovery variant is strong enough to open a challenger rotation review."
            ),
        },
        "rotation_gate": rotation_gate,
        "decision_summary": [
            f"Treat `{active_reference['label']}` as the current active attack challenger reference.",
            (
                f"Open a direct rotation review for `{candidate_summary['variant_label']}` against `{active_reference['label']}`."
                if open_rotation_review and candidate_summary is not None
                else f"Keep `{active_reference['label']}` as the active challenger and continue searching for a same-profile upgrade."
            ),
            (
                f"Do not approve the challenger rotation yet because `{', '.join(rotation_gate['blocking_reasons'])}` is still failing."
                if rotation_gate["gate_open"] and rotation_gate["blocking_reasons"]
                else f"Approve `{candidate_summary['variant_label']}` as the next attack challenger."
                if rotation_gate["approve_challenger_rotation_now"] and candidate_summary is not None
                else "No challenger rotation approval is available yet."
            ),
            f"Next attack research step: `{rotation_gate['next_step_now']}`.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    active = report["active_challenger_reference"]
    candidate = report["rotation_candidate"]
    verdict = report["rotation_review"]
    lines = [
        "# BTC 1d Attack Challenger Rotation Review",
        "",
        f"- Active challenger: `{active['label']}`",
        f"- Active paper CAGR: `{active['paper_validation_cagr']}`",
        f"- Active paper Sharpe: `{active['paper_validation_sharpe']}`",
        f"- Active paper MDD: `{active['paper_validation_max_drawdown']}`",
        f"- Active negative windows: `{active['negative_walk_forward_windows']}`",
        f"- Active idle windows: `{active['idle_walk_forward_windows']}`",
        f"- Open rotation review: `{verdict['open_rotation_review']}`",
        f"- Approve challenger rotation now: `{verdict['approve_challenger_rotation_now']}`",
        f"- Manual review required: `{verdict['manual_review_required']}`",
        f"- Proposed challenger: `{verdict['proposed_attack_challenger']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
    ]
    if candidate is not None:
        lines.extend(
            [
                "## Rotation Candidate",
                f"- Variant: `{candidate['variant_label']}`",
                f"- Base CAGR: `{candidate['base_cagr']}`",
                f"- Base Sharpe: `{candidate['base_sharpe']}`",
                f"- Base MDD: `{candidate['base_max_drawdown']}`",
                f"- Drift: `{candidate['sensitivity_max_drift']}`",
                f"- CAGR delta vs active: `{candidate['cagr_delta_vs_active']}`",
                f"- Sharpe delta vs active: `{candidate['sharpe_delta_vs_active']}`",
                f"- MDD delta vs active: `{candidate['max_drawdown_delta_vs_active']}`",
                (
                    f"- Drift delta vs active: `{candidate['drift_delta_vs_active']}`"
                    if candidate["drift_delta_vs_active"] is not None
                    else "- Drift delta vs active: `n/a`"
                ),
                f"- Same negative profile: `{candidate['same_negative_profile_as_active']}`",
                f"- Same idle profile: `{candidate['same_idle_profile_as_active']}`",
                "",
            ]
        )
    gate = report["rotation_gate"]
    lines.extend(
        [
            "## Rotation Gate",
            f"- Gate open: `{gate['gate_open']}`",
            f"- Approve now: `{gate['approve_challenger_rotation_now']}`",
            f"- Blocking reasons: `{gate['blocking_reasons']}`",
            f"- Next step now: `{gate['next_step_now']}`",
        ]
    )
    for check in gate["checks"]:
        lines.append(f"- `{check['name']}`: passed=`{check['passed']}` | {check['detail']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_challenger_rotation_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_challenger_rotation_review_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_attack_challenger_rotation_review_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_attack_challenger_rotation_review_md_latest.md"
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
