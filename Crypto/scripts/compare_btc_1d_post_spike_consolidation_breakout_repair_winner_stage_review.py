from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.post_spike_active_candidate import ACTIVE_ARTIFACT_LABEL


ANALYSIS_DIR = Path("analysis_results")
REPAIR_BATCH_GLOB = "btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch_*.json"
BASELINE_VALIDATION_PATTERN = (
    f"btc_1d_post_spike_consolidation_breakout_v4_{ACTIVE_ARTIFACT_LABEL}_paper_validation_*.json"
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest_json(analysis_dir: Path, pattern: str) -> Path:
    matches = sorted(analysis_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No analysis artifact matched pattern: {pattern}")
    return matches[0]


def _latest_repair_batch(analysis_dir: Path) -> dict:
    return _load_json(_latest_json(analysis_dir, REPAIR_BATCH_GLOB))


def _repair_winner_snapshot(analysis_dir: Path) -> dict:
    payload = _latest_repair_batch(analysis_dir)
    best = dict(payload["best_variant"])
    return {
        "candidate_label": f"post_spike_walk_forward_repair::{best['variant_label']}",
        "artifact_label_prefix": f"btcusdt_1d_2200_{best['variant_label']}_friction",
        "walk_forward_json": str(best["analysis_result_json"]),
        "variant_label": str(best["variant_label"]),
        "strategy_name": str(best["strategy_name"]),
        "parameters": dict(best["parameters"]),
    }


def _pick_friction_validation(analysis_dir: Path, artifact_label_prefix: str, cost_bps: int) -> tuple[Path, dict]:
    path = _latest_json(
        analysis_dir,
        f"btc_1d_post_spike_consolidation_breakout_v4_{artifact_label_prefix}_{cost_bps}bps_paper_validation_*.json",
    )
    return path, _load_json(path)


def _pick_baseline_validation(analysis_dir: Path) -> tuple[Path, dict]:
    path = _latest_json(analysis_dir, BASELINE_VALIDATION_PATTERN)
    return path, _load_json(path)


def _pick_walk_forward(path: str) -> tuple[Path, dict]:
    walk_forward_path = ROOT / path
    return walk_forward_path, _load_json(walk_forward_path)


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    winner = _repair_winner_snapshot(analysis_dir)
    friction8_path, validation8 = _pick_friction_validation(analysis_dir, winner["artifact_label_prefix"], 8)
    friction20_path, validation20 = _pick_friction_validation(analysis_dir, winner["artifact_label_prefix"], 20)
    baseline_path, baseline = _pick_baseline_validation(analysis_dir)
    walk_forward_path, walk_forward = _pick_walk_forward(winner["walk_forward_json"])

    validation_decision = dict(validation8.get("decision_record", {}) or {})
    validation20_decision = dict(validation20.get("decision_record", {}) or {})
    baseline_decision = dict(baseline.get("decision_record", {}) or {})
    validation_metrics = dict(validation_decision.get("key_metrics", {}) or {})
    baseline_metrics = dict(baseline_decision.get("key_metrics", {}) or {})
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
        "friction_20bps_passed": str(validation20_decision.get("decision", "")) == "PASS",
        "walk_forward_passed": bool(walk_overfit.get("passed", False)),
        "walk_forward_no_negative_window": len(negative_windows) == 0,
        "sensitivity_drift_within_guardrail": float(walk_overfit.get("sensitivity_max_drift", 1.0)) <= 0.20,
        "unstable_parameters_clear": len(list(walk_overfit.get("unstable_parameters", []) or [])) == 0,
    }
    candidate_stage_ready = all(requirements.values())

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "repair_winner_profile": {
            "candidate_label": winner["candidate_label"],
            "variant_label": winner["variant_label"],
            "strategy_name": winner["strategy_name"],
            "validation_sharpe": float(validation_metrics.get("sharpe", 0.0)),
            "validation_cagr": float(validation_metrics.get("cagr", 0.0)),
            "validation_max_drawdown": float(validation_metrics.get("max_drawdown", 0.0)),
            "baseline_sharpe": float(baseline_metrics.get("sharpe", 0.0)),
            "baseline_cagr": float(baseline_metrics.get("cagr", 0.0)),
            "baseline_max_drawdown": float(baseline_metrics.get("max_drawdown", 0.0)),
            "walk_forward_sensitivity_max_drift": float(walk_overfit.get("sensitivity_max_drift", 0.0)),
            "negative_walk_forward_windows": negative_windows,
            "idle_walk_forward_windows": idle_windows,
        },
        "artifact_paths": {
            "validation_8bps_json": str(friction8_path),
            "validation_20bps_json": str(friction20_path),
            "baseline_validation_json": str(baseline_path),
            "walk_forward_json": str(walk_forward_path),
        },
        "repair_winner_stage_requirements": requirements,
        "repair_winner_stage_verdict": {
            "candidate_stage_ready": candidate_stage_ready,
            "candidate_stage_lane": (
                "post_spike_candidate_stage_promotion_queue"
                if candidate_stage_ready
                else "post_spike_candidate_stage_repair_hold"
            ),
            "next_step_now": (
                "replace_anchor_candidate_with_repair_winner"
                if candidate_stage_ready
                else "continue_repair_on_idle_window"
            ),
            "reason": (
                "The repair winner keeps validation and friction green while removing the negative walk-forward window, so it can replace the current anchor candidate."
                if candidate_stage_ready
                else "The repair winner improved the candidate profile, but it still needs more repair before replacing the current anchor."
            ),
        },
        "decision_summary": [
            "Promote the repair winner over the current anchor if all gates remain green.",
            f"Baseline candidate metrics were Sharpe {baseline_metrics.get('sharpe', 0.0):.4f} / CAGR {baseline_metrics.get('cagr', 0.0):.4f}.",
            f"Repair winner metrics are Sharpe {validation_metrics.get('sharpe', 0.0):.4f} / CAGR {validation_metrics.get('cagr', 0.0):.4f}.",
            f"Idle windows remain {idle_windows or ['none']}, but the immediate blocker negative windows are {negative_windows or ['none']}.",
        ],
    }


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_consolidation_breakout_repair_winner_stage_review_{stamp}.json"
    latest_json = ANALYSIS_DIR / "btc_1d_post_spike_consolidation_breakout_repair_winner_stage_review_latest.json"
    payload = json.dumps(report, indent=2)
    json_path.write_text(payload, encoding="utf-8")
    latest_json.write_text(payload, encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
