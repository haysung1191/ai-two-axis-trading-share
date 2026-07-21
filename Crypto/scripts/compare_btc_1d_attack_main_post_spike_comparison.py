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


def _latest_base_validation(pattern: str) -> dict:
    matches = sorted(ANALYSIS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No analysis artifact matched pattern: {pattern}")
    for path in matches:
        payload = _load_json(path)
        config = payload.get("config", {})
        if float(config.get("fee_bps", 0.0)) == 8.0 and float(config.get("slippage_bps", 0.0)) == 8.0:
            return payload
    raise FileNotFoundError(f"No base 8bps validation artifact matched pattern: {pattern}")


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
    top_cost = _cost_level(friction["levels"])
    return {
        "label": "ratio112_tighter_stop_main",
        "role": "attack_main",
        "cagr": float(walk["base_metrics"]["cagr"]),
        "max_drawdown": float(walk["base_metrics"]["max_drawdown"]),
        "sharpe": float(walk["base_metrics"]["sharpe"]),
        "cost20_cagr": float(top_cost["cagr"]),
        "cost20_mdd": float(top_cost["max_drawdown"]),
        "cost20_sharpe": float(top_cost["sharpe"]),
        "cost_reference_bps": float(top_cost["cost_bps"]),
        "sensitivity_max_drift": float(walk["overfitting"]["sensitivity_max_drift"]),
    }


def _attack_backup() -> dict:
    walk_path = ANALYSIS_DIR / "btc_1d_walk_forward_diagnostic_20260415T164013Z.json"
    friction_path = ANALYSIS_DIR / "btc_1d_volatility_expansion_reclaim_sr111_tightstop_friction_20260415T164031Z.json"
    if not (walk_path.exists() and friction_path.exists()):
        return _scoreboard_row("ratio111_tighter_stop_backup", "attack_backup")
    walk = _load_json(walk_path)
    friction = _load_json(friction_path)
    top_cost = _cost_level(friction["levels"])
    return {
        "label": "ratio111_tighter_stop_backup",
        "role": "attack_backup",
        "cagr": float(walk["base_metrics"]["cagr"]),
        "max_drawdown": float(walk["base_metrics"]["max_drawdown"]),
        "sharpe": float(walk["base_metrics"]["sharpe"]),
        "cost20_cagr": float(top_cost["cagr"]),
        "cost20_mdd": float(top_cost["max_drawdown"]),
        "cost20_sharpe": float(top_cost["sharpe"]),
        "cost_reference_bps": float(top_cost["cost_bps"]),
        "sensitivity_max_drift": float(walk["overfitting"]["sensitivity_max_drift"]),
    }


def _post_spike() -> dict:
    validation = _latest_base_validation(
        f"btc_1d_post_spike_consolidation_breakout_v4_{ACTIVE_ARTIFACT_LABEL}_paper_validation_*.json"
    )
    friction = _load_json(_latest("btc_1d_post_spike_consolidation_breakout_friction_*.json"))
    walk = _load_json(_latest("btc_1d_walk_forward_diagnostic_*.json"))

    walk_candidates = sorted(ANALYSIS_DIR.glob("btc_1d_walk_forward_diagnostic_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in walk_candidates:
        payload = _load_json(path)
        if payload.get("config", {}).get("candidate_label") == ACTIVE_CANDIDATE_LABEL:
            walk = payload
            break

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
        "role": "attack_challenger",
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
    }


def _latest(pattern: str) -> Path:
    matches = sorted(ANALYSIS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No analysis artifact matched pattern: {pattern}")
    return matches[0]


def build_report() -> dict:
    main = _attack_main()
    backup = _attack_backup()
    challenger = _post_spike()

    challenger_has_clean_entry = not challenger["negative_walk_forward_windows"] and challenger["sensitivity_max_drift"] <= 0.20
    challenger_beats_backup_on_quality = (
        challenger["sharpe"] > backup["sharpe"]
        and challenger["max_drawdown"] < backup["max_drawdown"]
    )
    challenger_beats_main_on_cagr = challenger["cagr"] > main["cagr"]

    role_assignment = (
        "add_post_spike_as_attack_challenger_keep_main_and_backup"
        if challenger_has_clean_entry and not challenger_beats_main_on_cagr
        else "hold_existing_attack_stack"
    )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "stack_reference": {
            "attack_main": main["label"],
            "attack_backup": backup["label"],
            "candidate_challenger": challenger["label"],
        },
        "compared_models": [main, backup, challenger],
        "comparison_verdict": {
            "role_assignment": role_assignment,
            "keep_attack_main": True,
            "keep_attack_backup": True,
            "add_post_spike_challenger": challenger_has_clean_entry,
            "challenger_beats_backup_on_quality": challenger_beats_backup_on_quality,
            "challenger_beats_main_on_cagr": challenger_beats_main_on_cagr,
            "next_step_now": "promote_post_spike_into_attack_experiment_board" if challenger_has_clean_entry else "hold_post_spike_before_attack_board",
            "reason": (
                "The post-spike model does not beat the attack main on CAGR, but it is cleaner on drawdown and drift than the current attack stack, so it belongs on the attack experiment board as a challenger."
                if challenger_has_clean_entry
                else "The post-spike model is still not clean enough to join the attack experiment board."
            ),
        },
        "decision_summary": [
            f"Keep `{main['label']}` as attack main because it still owns the highest validated CAGR.",
            f"Keep `{backup['label']}` as attack backup because it preserves the existing high-CAGR backup lane.",
            (
                f"Add `{challenger['label']}` as an attack challenger because it is stage-ready and improves Sharpe/drawdown quality without overtaking the main on CAGR."
                if challenger_has_clean_entry
                else f"Hold `{challenger['label']}` outside the attack board until the remaining walk-forward cleanliness gap is repaired."
            ),
        ],
    }
    return report


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_main_post_spike_comparison_{stamp}.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
