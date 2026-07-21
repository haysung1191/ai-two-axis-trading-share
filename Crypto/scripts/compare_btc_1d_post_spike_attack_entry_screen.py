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
    ACTIVE_CHALLENGER_LABEL,
)

ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _scoreboard_row(label: str, role: str) -> dict:
    scoreboard = _load_json(ANALYSIS_DIR / "btc_1d_model_scoreboard_latest.json")
    rows = list(scoreboard.get("top_models", [])) + list(scoreboard.get("top_new_models", []))
    row = next((item for item in rows if str(item.get("variant")) == label), None)
    if row is None:
        return {
            "label": label,
            "role": role,
            "cagr": 0.0,
            "max_drawdown": 0.0,
            "sharpe": 0.0,
            "cost20_cagr": 0.0,
            "cost20_mdd": 0.0,
            "cost20_sharpe": 0.0,
            "sensitivity_max_drift": 0.0,
        }
    cagr = float(row.get("cagr") or 0.0)
    mdd = float(row.get("mdd") or 0.0)
    sharpe = float(row.get("sharpe") or 0.0)
    return {
        "label": label,
        "role": role,
        "cagr": cagr,
        "max_drawdown": mdd,
        "sharpe": sharpe,
        "cost20_cagr": float(row.get("cost_cagr") if row.get("cost_cagr") is not None else cagr),
        "cost20_mdd": mdd,
        "cost20_sharpe": sharpe,
        "sensitivity_max_drift": 0.0,
    }


def _latest(pattern: str) -> Path:
    matches = sorted(ANALYSIS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No analysis artifact matched pattern: {pattern}")
    return matches[0]


def _cost_level(levels: list[dict], target_bps: float = 20.0) -> dict:
    if not levels:
        raise ValueError("Friction artifact has no cost levels.")
    exact = [level for level in levels if float(level["cost_bps"]) == target_bps]
    if exact:
        return exact[0]
    below = [level for level in levels if float(level["cost_bps"]) <= target_bps]
    if below:
        return max(below, key=lambda level: float(level["cost_bps"]))
    return min(levels, key=lambda level: float(level["cost_bps"]))


def _attack_main() -> dict:
    walk_path = ANALYSIS_DIR / "btc_1d_walk_forward_diagnostic_20260415T162959Z.json"
    friction_path = ANALYSIS_DIR / "btc_1d_volatility_expansion_reclaim_sr112_tightstop_friction_20260415T163017Z.json"
    if not (walk_path.exists() and friction_path.exists()):
        return _scoreboard_row("ratio112_tighter_stop_main", "attack_main")
    walk = _load_json(walk_path)
    friction = _load_json(friction_path)
    level20 = _cost_level(friction["levels"])
    return {
        "label": "ratio112_tighter_stop_main",
        "role": "attack_main",
        "cagr": float(walk["base_metrics"]["cagr"]),
        "max_drawdown": float(walk["base_metrics"]["max_drawdown"]),
        "sharpe": float(walk["base_metrics"]["sharpe"]),
        "cost20_cagr": float(level20["cagr"]),
        "cost20_mdd": float(level20["max_drawdown"]),
        "cost20_sharpe": float(level20["sharpe"]),
        "cost_reference_bps": float(level20["cost_bps"]),
        "sensitivity_max_drift": float(walk["overfitting"]["sensitivity_max_drift"]),
    }


def _attack_backup() -> dict:
    walk_path = ANALYSIS_DIR / "btc_1d_walk_forward_diagnostic_20260415T164013Z.json"
    friction_path = ANALYSIS_DIR / "btc_1d_volatility_expansion_reclaim_sr111_tightstop_friction_20260415T164031Z.json"
    if not (walk_path.exists() and friction_path.exists()):
        return _scoreboard_row("ratio111_tighter_stop_backup", "attack_backup")
    walk = _load_json(walk_path)
    friction = _load_json(friction_path)
    level20 = _cost_level(friction["levels"])
    return {
        "label": "ratio111_tighter_stop_backup",
        "role": "attack_backup",
        "cagr": float(walk["base_metrics"]["cagr"]),
        "max_drawdown": float(walk["base_metrics"]["max_drawdown"]),
        "sharpe": float(walk["base_metrics"]["sharpe"]),
        "cost20_cagr": float(level20["cagr"]),
        "cost20_mdd": float(level20["max_drawdown"]),
        "cost20_sharpe": float(level20["sharpe"]),
        "cost_reference_bps": float(level20["cost_bps"]),
        "sensitivity_max_drift": float(walk["overfitting"]["sensitivity_max_drift"]),
    }


def _post_spike_candidate() -> dict:
    walk_path = _latest("btc_1d_walk_forward_diagnostic_*.json")
    walk_candidates = sorted(
        ANALYSIS_DIR.glob("btc_1d_walk_forward_diagnostic_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    walk = None
    walk_path = None
    for path in walk_candidates:
        payload = _load_json(path)
        if payload.get("config", {}).get("candidate_label") == ACTIVE_CANDIDATE_LABEL:
            walk = payload
            walk_path = path
            break
    if walk is None or walk_path is None:
        raise FileNotFoundError("No walk-forward artifact found for post-spike active candidate.")

    validation_path = _latest(
        f"btc_1d_post_spike_consolidation_breakout_v4_{ACTIVE_ARTIFACT_LABEL}_paper_validation_*.json"
    )
    validation = _load_json(validation_path)
    friction_path = _latest("btc_1d_post_spike_consolidation_breakout_friction_*.json")
    friction = _load_json(friction_path)
    report = friction["report"] if "report" in friction else friction
    level20 = _cost_level(report["levels"])

    windows = list(walk["overfitting"]["walk_forward"])
    negative_windows = [
        int(window["window"])
        for window in windows
        if float(window["metrics"]["sharpe"]) < 0.0 or float(window["metrics"]["cagr"]) < 0.0
    ]
    idle_windows = [
        int(window["window"])
        for window in windows
        if int(window["metrics"]["trades"]) == 0
    ]

    return {
        "label": ACTIVE_CHALLENGER_LABEL,
        "role": "candidate_stage_ready",
        "cagr": float(validation["decision_record"]["key_metrics"]["cagr"]),
        "max_drawdown": float(validation["decision_record"]["key_metrics"]["max_drawdown"]),
        "sharpe": float(validation["decision_record"]["key_metrics"]["sharpe"]),
        "cost20_cagr": float(level20["cagr"]),
        "cost20_mdd": float(level20["max_drawdown"]),
        "cost20_sharpe": float(level20["sharpe"]),
        "cost_reference_bps": float(level20["cost_bps"]),
        "sensitivity_max_drift": float(walk["overfitting"]["sensitivity_max_drift"]),
        "negative_walk_forward_windows": negative_windows,
        "idle_walk_forward_windows": idle_windows,
        "friction_final_decision": str(report["final_decision"]),
        "validation_path": str(validation_path),
        "friction_path": str(friction_path),
        "walk_forward_path": str(walk_path),
    }


def build_report() -> dict:
    attack_main = _attack_main()
    attack_backup = _attack_backup()
    candidate = _post_spike_candidate()

    cagr_gap_to_main = round(candidate["cagr"] - attack_main["cagr"], 6)
    drawdown_gap_to_main = round(candidate["max_drawdown"] - attack_main["max_drawdown"], 6)
    attack_entry_ready = (
        candidate["friction_final_decision"] == "continue"
        and not candidate["negative_walk_forward_windows"]
        and candidate["sensitivity_max_drift"] <= 0.20
    )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "attack_stack_reference": {
            "attack_main": attack_main["label"],
            "attack_backup": attack_backup["label"],
        },
        "compared_models": [attack_main, attack_backup, candidate],
        "post_spike_attack_entry_verdict": {
            "attack_entry_ready": attack_entry_ready,
            "queue_lane": "attack_comparison_entry_queue" if attack_entry_ready else "candidate_stage_hold",
            "next_step_now": "run_attack_main_comparison_with_post_spike_candidate" if attack_entry_ready else "repair_candidate_before_attack_entry",
            "candidate_label": candidate["label"],
            "cagr_gap_to_attack_main": cagr_gap_to_main,
            "drawdown_gap_to_attack_main": drawdown_gap_to_main,
            "reason": (
                "The post-spike candidate is not the top CAGR model, but it is stage-ready and can now be compared directly against the current attack stack."
                if attack_entry_ready
                else "The post-spike candidate still lacks a clean candidate-stage profile, so it should not enter attack comparison yet."
            ),
        },
        "decision_summary": [
            f"Attack main remains `{attack_main['label']}` and attack backup remains `{attack_backup['label']}`.",
            f"Post-spike candidate `{candidate['label']}` is stage-ready with CAGR {candidate['cagr']:.4f}, MDD {candidate['max_drawdown']:.4f}, Sharpe {candidate['sharpe']:.4f}.",
            f"CAGR gap to attack main is {cagr_gap_to_main:.4f}, while drawdown gap is {drawdown_gap_to_main:.4f}.",
            "Enter the post-spike candidate into attack comparison only after candidate-stage gates are green.",
        ],
    }
    return report


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_attack_entry_screen_{stamp}.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
