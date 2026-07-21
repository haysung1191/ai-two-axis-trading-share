from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.post_spike_active_candidate import (
    ACTIVE_ARTIFACT_LABEL,
    ACTIVE_CANDIDATE_LABEL,
    ACTIVE_STRATEGY_NAME,
)


ANALYSIS_DIR = Path("analysis_results")
WALK_FORWARD_CANDIDATE = ACTIVE_CANDIDATE_LABEL
VALIDATION_STRATEGY = ACTIVE_STRATEGY_NAME


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest_json(analysis_dir: Path, pattern: str) -> Path:
    matches = sorted(analysis_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No analysis artifact matched pattern: {pattern}")
    return matches[0]


def _pick_validation(analysis_dir: Path) -> tuple[Path, dict]:
    path = _latest_json(
        analysis_dir,
        f"{VALIDATION_STRATEGY}_{ACTIVE_ARTIFACT_LABEL}_paper_validation_*.json",
    )
    return path, _load_json(path)


def _pick_friction(analysis_dir: Path) -> tuple[Path, dict]:
    candidates = sorted(
        analysis_dir.glob("btc_1d_post_spike_consolidation_breakout_friction_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        payload = _load_json(path)
        candidate = str(payload.get("candidate", "") or (payload.get("report", {}) or {}).get("candidate", ""))
        if candidate == WALK_FORWARD_CANDIDATE:
            return path, payload
    raise FileNotFoundError(f"No post-spike friction artifact found for {WALK_FORWARD_CANDIDATE} candidate.")


def _pick_walk_forward(analysis_dir: Path) -> tuple[Path, dict]:
    candidates = sorted(
        analysis_dir.glob("btc_1d_walk_forward_diagnostic_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        payload = _load_json(path)
        candidate = str(payload.get("config", {}).get("candidate_label", ""))
        if candidate == WALK_FORWARD_CANDIDATE:
            return path, payload
    raise FileNotFoundError(f"No walk-forward diagnostic artifact found for {WALK_FORWARD_CANDIDATE} candidate.")


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    friction_path, friction_payload = _pick_friction(analysis_dir)
    friction = dict((friction_payload.get("report", {}) if "report" in friction_payload else friction_payload) or {})
    validation_path, validation = _pick_validation(analysis_dir)
    walk_forward_path, walk_forward = _pick_walk_forward(analysis_dir)

    validation_decision = dict(validation.get("decision_record", {}) or {})
    validation_metrics = dict(validation_decision.get("key_metrics", {}) or {})
    walk_overfit = dict(walk_forward.get("overfitting", {}) or {})
    windows = list(walk_overfit.get("walk_forward", []) or [])

    negative_windows = [
        int(window.get("window", 0))
        for window in windows
        if float((window.get("metrics", {}) or {}).get("sharpe", 0.0)) < 0.0
        or float((window.get("metrics", {}) or {}).get("cagr", 0.0)) < 0.0
    ]
    idle_windows = [
        int(window.get("window", 0))
        for window in windows
        if int((window.get("metrics", {}) or {}).get("trades", 0)) == 0
    ]

    requirements = {
        "paper_validation_passed": str(validation_decision.get("decision", "")) == "PASS",
        "friction_stays_green": str(friction.get("final_decision", "")) == "continue",
        "walk_forward_passed": bool(walk_overfit.get("passed", False)),
        "walk_forward_no_negative_window": len(negative_windows) == 0,
        "sensitivity_drift_within_guardrail": float(walk_overfit.get("sensitivity_max_drift", 1.0)) <= 0.20,
        "unstable_parameters_clear": len(list(walk_overfit.get("unstable_parameters", []) or [])) == 0,
    }
    failed_requirement_keys = [key for key, value in requirements.items() if not value]

    review_ready = all(requirements.values())
    queue_lane = (
        "post_spike_candidate_stage_promotion_queue"
        if review_ready
        else "post_spike_candidate_stage_repair_hold"
    )
    next_step_now = (
        "promote_candidate_into_attack_comparison"
        if review_ready
        else "repair_candidate_walk_forward_or_sensitivity"
    )
    if review_ready:
        reason = "Validation, friction, and walk-forward all stayed aligned, so the post-spike candidate can advance into the attack-comparison lane."
    else:
        failed_read = ", ".join(failed_requirement_keys)
        reason = (
            "The post-spike candidate remains in repair hold because these requirements are still failing: "
            f"{failed_read}."
        )

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "candidate_profile": {
            "label": WALK_FORWARD_CANDIDATE,
            "strategy_name": VALIDATION_STRATEGY,
            "paper_validation_sharpe": float(validation_metrics.get("sharpe", 0.0)),
            "paper_validation_cagr": float(validation_metrics.get("cagr", 0.0)),
            "paper_validation_max_drawdown": float(validation_metrics.get("max_drawdown", 0.0)),
            "friction_final_decision": str(friction.get("final_decision", "")),
            "walk_forward_passed": bool(walk_overfit.get("passed", False)),
            "walk_forward_sensitivity_max_drift": float(walk_overfit.get("sensitivity_max_drift", 0.0)),
            "negative_walk_forward_windows": negative_windows,
            "idle_walk_forward_windows": idle_windows,
        },
        "artifact_paths": {
            "paper_validation_json": str(validation_path),
            "friction_json": str(friction_path),
            "walk_forward_json": str(walk_forward_path),
        },
        "post_spike_candidate_stage_review_requirements": requirements,
        "post_spike_candidate_stage_review_verdict": {
            "candidate_stage_ready": review_ready,
            "candidate_stage_lane": queue_lane,
            "next_step_now": next_step_now,
            "failed_requirements": failed_requirement_keys,
            "reason": reason,
        },
        "decision_summary": [
            f"Keep `{WALK_FORWARD_CANDIDATE}` as the active post-spike candidate-stage reference.",
            (
                "Advance this candidate into attack comparison because validation, friction, and walk-forward all stayed green."
                if review_ready
                else "Do not promote yet; repair the walk-forward or sensitivity gap before comparing this candidate against the attack main lane."
            ),
            f"Use windows `{negative_windows or ['none']}` as the immediate repair target and windows `{idle_windows or ['none']}` as deployment-profile context.",
        ],
    }


def _render_markdown(report: dict) -> str:
    candidate = report["candidate_profile"]
    requirements = report["post_spike_candidate_stage_review_requirements"]
    verdict = report["post_spike_candidate_stage_review_verdict"]
    paths = report["artifact_paths"]
    return "\n".join(
        [
            "# BTC 1d Post-Spike Candidate Stage Review",
            "",
            f"- Candidate: `{candidate['label']}`",
            f"- Strategy: `{candidate['strategy_name']}`",
            f"- Paper validation: Sharpe `{candidate['paper_validation_sharpe']:.4f}` / CAGR `{candidate['paper_validation_cagr']:.4f}` / MDD `{candidate['paper_validation_max_drawdown']:.4f}`",
            f"- Friction final decision: `{candidate['friction_final_decision']}`",
            f"- Walk-forward passed: `{candidate['walk_forward_passed']}`",
            f"- Walk-forward sensitivity drift: `{candidate['walk_forward_sensitivity_max_drift']:.4f}`",
            f"- Negative walk-forward windows: `{candidate['negative_walk_forward_windows']}`",
            f"- Idle walk-forward windows: `{candidate['idle_walk_forward_windows']}`",
            f"- Candidate stage ready: `{verdict['candidate_stage_ready']}`",
            f"- Queue lane: `{verdict['candidate_stage_lane']}`",
            f"- Next step now: `{verdict['next_step_now']}`",
            "",
            "## Requirements",
            *(f"- {key}: `{value}`" for key, value in requirements.items()),
            "",
            "## Artifacts",
            f"- paper validation: `{paths['paper_validation_json']}`",
            f"- friction: `{paths['friction_json']}`",
            f"- walk forward: `{paths['walk_forward_json']}`",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_consolidation_breakout_candidate_stage_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_consolidation_breakout_candidate_stage_review_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_post_spike_consolidation_breakout_candidate_stage_review_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_post_spike_consolidation_breakout_candidate_stage_review_md_latest.md"
    json_payload = json.dumps(report, indent=2)
    md_payload = _render_markdown(report)
    json_path.write_text(json_payload, encoding="utf-8")
    md_path.write_text(md_payload, encoding="utf-8")
    latest_json.write_text(json_payload, encoding="utf-8")
    latest_md.write_text(md_payload, encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
