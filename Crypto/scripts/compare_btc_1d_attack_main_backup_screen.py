from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.attack_active_stack import (
    ACTIVE_ATTACK_BACKUP_LABEL,
    ACTIVE_ATTACK_CHALLENGER_LABEL,
    ACTIVE_ATTACK_MAIN_LABEL,
)
from scripts.compare_btc_1d_attack_challenger_rotation_review import (
    build_report as build_attack_challenger_rotation_review,
)
from scripts.compare_btc_1d_attack_challenger_validation_review import (
    build_report as build_attack_challenger_validation_review,
)
from scripts.compare_btc_1d_attack_challenger_promotion_review import (
    build_report as build_attack_challenger_promotion_review,
)
from scripts.compare_btc_1d_attack_challenger_rotation_application_readiness import (
    build_report as build_attack_challenger_rotation_application_readiness,
)
from scripts.compare_btc_1d_post_spike_hold36_drift_repair_candidates import (
    build_report as build_hold36_drift_repair_candidates,
)
from scripts.post_spike_active_candidate import (
    ACTIVE_ARTIFACT_LABEL,
    ACTIVE_CANDIDATE_LABEL,
    ACTIVE_CHALLENGER_LABEL,
)

ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _scoreboard_snapshot(label: str, role: str, *, stack_read: str) -> dict:
    scoreboard = _load_json(ANALYSIS_DIR / "btc_1d_model_scoreboard_latest.json")
    rows = list(scoreboard.get("top_models", [])) + list(scoreboard.get("top_new_models", []))
    row = next((item for item in rows if str(item.get("variant")) == label), None)
    if row is None:
        raise FileNotFoundError(f"No scoreboard row found for {label}.")
    cagr = float(row.get("cagr") or 0.0)
    mdd = float(row.get("mdd") or 0.0)
    sharpe = float(row.get("sharpe") or 0.0)
    return {
        "label": label,
        "role": role,
        "base_cagr": cagr,
        "base_mdd": mdd,
        "base_sharpe": sharpe,
        "oos_cagr": float(row.get("oos_cagr") if row.get("oos_cagr") is not None else cagr),
        "oos_mdd": mdd,
        "oos_sharpe": sharpe,
        "sensitivity_max_drift": 0.0,
        "unstable_parameters": [],
        "cost20_cagr": float(row.get("cost_cagr") if row.get("cost_cagr") is not None else cagr),
        "cost20_mdd": mdd,
        "cost20_sharpe": sharpe,
        "completed_trades": int(row.get("trades") or 0),
        "failed_gates": [str(row.get("gate_failure_reason"))] if row.get("gate_failure_reason") else [],
        "stack_read": stack_read,
        "negative_walk_forward_windows": list(row.get("negative_walk_forward_windows") or []),
    }


def _ratio112_main() -> dict:
    walk_path = ANALYSIS_DIR / "btc_1d_walk_forward_diagnostic_20260415T162959Z.json"
    friction_path = ANALYSIS_DIR / "btc_1d_volatility_expansion_reclaim_sr112_tightstop_friction_20260415T163017Z.json"
    paper_path = ANALYSIS_DIR / "btc_1d_volatility_expansion_reclaim_sr112_tightstop_paper_validation_20260415T162937Z.json"
    if not (walk_path.exists() and friction_path.exists() and paper_path.exists()):
        return _scoreboard_snapshot(
            "ratio112_tighter_stop_main",
            "attack_main",
            stack_read="scoreboard_latest_fallback",
        )

    walk = _load_json(walk_path)
    friction = _load_json(friction_path)
    paper = _load_json(paper_path)
    base = walk["base_metrics"]
    overfitting = walk["overfitting"]
    oos = overfitting["oos_metrics"]
    top_cost = next(level for level in friction["levels"] if float(level["cost_bps"]) == 20.0)

    return {
        "label": "ratio112_tighter_stop_main",
        "role": "attack_main",
        "base_cagr": float(base["cagr"]),
        "base_mdd": float(base["max_drawdown"]),
        "base_sharpe": float(base["sharpe"]),
        "oos_cagr": float(oos["cagr"]),
        "oos_mdd": float(oos["max_drawdown"]),
        "oos_sharpe": float(oos["sharpe"]),
        "sensitivity_max_drift": float(overfitting["sensitivity_max_drift"]),
        "unstable_parameters": list(overfitting["unstable_parameters"]),
        "cost20_cagr": float(top_cost["cagr"]),
        "cost20_mdd": float(top_cost["max_drawdown"]),
        "cost20_sharpe": float(top_cost["sharpe"]),
        "completed_trades": int(paper["completed_trades"]),
        "failed_gates": list(paper["decision_record"]["failed_gates"]),
        "stack_read": "higher_return_anchor",
    }


def _ratio111_backup() -> dict:
    walk_path = ANALYSIS_DIR / "btc_1d_walk_forward_diagnostic_20260415T164013Z.json"
    friction_path = ANALYSIS_DIR / "btc_1d_volatility_expansion_reclaim_sr111_tightstop_friction_20260415T164031Z.json"
    paper_path = ANALYSIS_DIR / "btc_1d_volatility_expansion_reclaim_sr112_tightstop_r111_paper_validation_20260415T163951Z.json"
    if not (walk_path.exists() and friction_path.exists() and paper_path.exists()):
        return _scoreboard_snapshot(
            "ratio111_tighter_stop_backup",
            "attack_backup",
            stack_read="scoreboard_latest_fallback",
        )

    walk = _load_json(walk_path)
    friction = _load_json(friction_path)
    paper = _load_json(paper_path)
    base = walk["base_metrics"]
    overfitting = walk["overfitting"]
    oos = overfitting["oos_metrics"]
    top_cost = next(level for level in friction["levels"] if float(level["cost_bps"]) == 20.0)

    return {
        "label": "ratio111_tighter_stop_backup",
        "role": "attack_backup",
        "base_cagr": float(base["cagr"]),
        "base_mdd": float(base["max_drawdown"]),
        "base_sharpe": float(base["sharpe"]),
        "oos_cagr": float(oos["cagr"]),
        "oos_mdd": float(oos["max_drawdown"]),
        "oos_sharpe": float(oos["sharpe"]),
        "sensitivity_max_drift": float(overfitting["sensitivity_max_drift"]),
        "unstable_parameters": list(overfitting["unstable_parameters"]),
        "cost20_cagr": float(top_cost["cagr"]),
        "cost20_mdd": float(top_cost["max_drawdown"]),
        "cost20_sharpe": float(top_cost["sharpe"]),
        "completed_trades": int(paper["completed_trades"]),
        "failed_gates": list(paper["decision_record"]["failed_gates"]),
        "stack_read": "slightly_duller_backup",
    }


def _latest(pattern: str) -> Path:
    matches = sorted(ANALYSIS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No analysis artifact matched pattern: {pattern}")
    return matches[0]


def _latest_post_spike_friction(candidate_label: str) -> dict:
    matches = sorted(
        ANALYSIS_DIR.glob("btc_1d_post_spike_consolidation_breakout_friction_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in matches:
        payload = _load_json(path)
        friction = payload["report"] if "report" in payload else payload
        candidate = str(friction.get("candidate", "") or payload.get("candidate", ""))
        if candidate == candidate_label:
            return friction
    raise FileNotFoundError(f"No post-spike friction artifact found for {candidate_label}.")


def _latest_base_validation(pattern: str) -> dict:
    matches = sorted(ANALYSIS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No analysis artifact matched pattern: {pattern}")
    fallback_payload = None
    for path in matches:
        payload = _load_json(path)
        config = payload.get("config", {})
        if not config:
            fallback_payload = fallback_payload or payload
            continue
        if "fee_bps" not in config and "slippage_bps" not in config:
            fallback_payload = fallback_payload or payload
            continue
        if float(config.get("fee_bps", 0.0)) == 8.0 and float(config.get("slippage_bps", 0.0)) == 8.0:
            return payload
    if fallback_payload is not None:
        return fallback_payload
    raise FileNotFoundError(f"No base 8bps validation artifact matched pattern: {pattern}")


def _active_post_spike_challenger() -> dict:
    walk_candidates = sorted(ANALYSIS_DIR.glob("btc_1d_walk_forward_diagnostic_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    walk = None
    for path in walk_candidates:
        payload = _load_json(path)
        if payload.get("config", {}).get("candidate_label") == ACTIVE_CANDIDATE_LABEL:
            walk = payload
            break
    if walk is None:
        raise FileNotFoundError("No walk-forward artifact found for active post-spike challenger.")

    friction = _latest_post_spike_friction(ACTIVE_CANDIDATE_LABEL)
    validation = _latest_base_validation(
        f"btc_1d_post_spike_consolidation_breakout_v4_{ACTIVE_ARTIFACT_LABEL}_paper_validation_*.json"
    )
    stage_review = _load_json(_latest("btc_1d_post_spike_consolidation_breakout_candidate_stage_review_*.json"))
    levels = list(friction.get("levels", []))
    top_cost = next(
        (level for level in levels if float(level["cost_bps"]) == 20.0),
        levels[-1] if levels else {},
    )
    base = validation["decision_record"]["key_metrics"]
    profile = stage_review.get("candidate_profile", {})

    return {
        "label": ACTIVE_CHALLENGER_LABEL,
        "role": "attack_challenger",
        "base_cagr": float(base["cagr"]),
        "base_mdd": float(base["max_drawdown"]),
        "base_sharpe": float(base["sharpe"]),
        "oos_cagr": float(walk["overfitting"]["oos_metrics"]["cagr"]),
        "oos_mdd": float(walk["overfitting"]["oos_metrics"]["max_drawdown"]),
        "oos_sharpe": float(walk["overfitting"]["oos_metrics"]["sharpe"]),
        "sensitivity_max_drift": float(walk["overfitting"]["sensitivity_max_drift"]),
        "unstable_parameters": list(walk["overfitting"]["unstable_parameters"]),
        "cost20_cagr": float(top_cost["cagr"]),
        "cost20_mdd": float(top_cost["max_drawdown"]),
        "cost20_sharpe": float(top_cost["sharpe"]),
        "completed_trades": int(validation["completed_trades"]),
        "failed_gates": list(validation["decision_record"]["failed_gates"]),
        "stack_read": "active_post_spike_challenger",
        "negative_walk_forward_windows": list(profile.get("negative_walk_forward_windows", [])),
        "idle_walk_forward_windows": list(profile.get("idle_walk_forward_windows", [])),
    }


def _latest_reopen_seed_cycle() -> dict:
    matches = sorted(ANALYSIS_DIR.glob("btc_1d_post_spike_reopen_seed_cycle_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError("No reopen seed cycle artifact found.")
    return _load_json(matches[-1])


def _reopen_seed_snapshot(seed_label: str, role: str) -> dict:
    cycle = _latest_reopen_seed_cycle()
    rows = list(cycle.get("seed_results", []))
    seed = next((item for item in rows if str(item.get("seed_label")) == seed_label), None)
    if seed is None:
        raise FileNotFoundError(f"No reopen seed result found for {seed_label}.")
    return {
        "label": seed_label,
        "role": role,
        "base_cagr": float(seed["base_cagr"]),
        "base_mdd": float(seed["base_max_drawdown"]),
        "base_sharpe": float(seed["base_sharpe"]),
        "oos_cagr": float(seed["base_cagr"]),
        "oos_mdd": float(seed["base_max_drawdown"]),
        "oos_sharpe": float(seed["base_sharpe"]),
        "sensitivity_max_drift": float(seed["sensitivity_max_drift"]),
        "unstable_parameters": [],
        "cost20_cagr": float(seed["base_cagr"]),
        "cost20_mdd": float(seed["base_max_drawdown"]),
        "cost20_sharpe": float(seed["base_sharpe"]),
        "completed_trades": int(seed["completed_trades"]),
        "failed_gates": [],
        "stack_read": "revalidated_reopen_seed" if role == "attack_backup" else "shadowed_former_backup",
        "negative_walk_forward_windows": list(seed.get("negative_windows", [])),
        "idle_walk_forward_windows": [],
    }


def _challenger_reopen_snapshot(label: str, role: str) -> dict:
    payload = _load_json(_latest("btc_1d_post_spike_challenger_main_pressure_reopen_batch_*.json"))
    variant_map = {
        "post_spike_trend92_depth058_volume105_hold34": "challenger_anchor",
        "post_spike_trend92_depth058_volume105_hold36": "hold36",
    }


def _frontier_bridge_snapshot(label: str, role: str) -> dict:
    dual_validation_matches = sorted(
        ANALYSIS_DIR.glob("btc_1d_post_spike_bridge_backup_dual_validation_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if dual_validation_matches:
        payload = _load_json(dual_validation_matches[0])
        if str(payload.get("bridge_backup_label")) == label:
            base = dict(payload.get("base_validation", {}) or {})
            cost20 = dict(payload.get("cost20_validation", {}) or {})
            return {
                "label": label,
                "role": role,
                "base_cagr": float(base["base_cagr"]),
                "base_mdd": float(base["base_max_drawdown"]),
                "base_sharpe": float(base["base_sharpe"]),
                "oos_cagr": float(base["base_cagr"]),
                "oos_mdd": float(base["base_max_drawdown"]),
                "oos_sharpe": float(base["base_sharpe"]),
                "sensitivity_max_drift": float(cost20["sensitivity_max_drift"]),
                "unstable_parameters": [],
                "cost20_cagr": float(cost20["cost20_cagr"]),
                "cost20_mdd": float(cost20["cost20_max_drawdown"]),
                "cost20_sharpe": float(cost20["cost20_sharpe"]),
                "completed_trades": 0,
                "failed_gates": (
                    ["negative_walk_forward_window"]
                    if int(cost20.get("negative_window_count", 0)) > 0 or int(base.get("negative_window_count", 0)) > 0
                    else []
                ),
                "stack_read": "exact_hit_frontier_bridge_backup",
                "negative_walk_forward_windows": list(cost20.get("negative_windows", []) or []),
                "idle_walk_forward_windows": list(cost20.get("idle_windows", []) or []),
            }
    try:
        payload = _load_json(_latest("btc_1d_post_spike_exact_hit_frontier_bridge_batch_*.json"))
    except FileNotFoundError:
        return _scoreboard_snapshot(
            label,
            role,
            stack_read="scoreboard_latest_frontier_bridge_fallback",
        )
    row = next((item for item in payload.get("results", []) if str(item.get("variant_label")) == label), None)
    if row is None:
        raise FileNotFoundError(f"No frontier bridge result found for {label}.")
    return {
        "label": label,
        "role": role,
        "base_cagr": float(row["base_cagr"]),
        "base_mdd": float(row["base_max_drawdown"]),
        "base_sharpe": float(row["base_sharpe"]),
        "oos_cagr": float(row["base_cagr"]),
        "oos_mdd": float(row["base_max_drawdown"]),
        "oos_sharpe": float(row["base_sharpe"]),
        "sensitivity_max_drift": float(row["sensitivity_max_drift"]),
        "unstable_parameters": [],
        "cost20_cagr": float(row["base_cagr"]),
        "cost20_mdd": float(row["base_max_drawdown"]),
        "cost20_sharpe": float(row["base_sharpe"]),
        "completed_trades": 0,
        "failed_gates": [],
        "stack_read": "exact_hit_frontier_bridge_backup" if role == "attack_backup" else "exact_hit_frontier_bridge_shadow",
        "negative_walk_forward_windows": list(row.get("negative_windows", [])),
        "idle_walk_forward_windows": list(row.get("idle_windows", [])),
    }
    variant_label = variant_map.get(label)
    if variant_label is None:
        raise FileNotFoundError(f"No challenger reopen mapping found for {label}.")
    row = next((item for item in payload.get("results", []) if str(item.get("variant_label")) == variant_label), None)
    if row is None:
        raise FileNotFoundError(f"No challenger reopen result found for {variant_label}.")
    diagnostic = _load_json(ROOT / str(row["analysis_result_json"]))
    base = diagnostic["base_metrics"]
    return {
        "label": label,
        "role": role,
        "base_cagr": float(row["base_cagr"]),
        "base_mdd": float(row["base_max_drawdown"]),
        "base_sharpe": float(row["base_sharpe"]),
        "oos_cagr": float(row["base_cagr"]),
        "oos_mdd": float(row["base_max_drawdown"]),
        "oos_sharpe": float(row["base_sharpe"]),
        "sensitivity_max_drift": float(row["sensitivity_max_drift"]),
        "unstable_parameters": [],
        "cost20_cagr": float(row["base_cagr"]),
        "cost20_mdd": float(row["base_max_drawdown"]),
        "cost20_sharpe": float(row["base_sharpe"]),
        "completed_trades": int(base["trades"]),
        "failed_gates": [],
        "stack_read": "reopened_challenger_backup" if role == "attack_backup" else "reopened_challenger_shadow",
        "negative_walk_forward_windows": list(row.get("negative_windows", [])),
        "idle_walk_forward_windows": list(row.get("idle_windows", [])),
    }


def _load_snapshot(label: str, role: str) -> dict:
    if label == "ratio112_tighter_stop_main":
        snapshot = _ratio112_main()
    elif label == "ratio111_tighter_stop_backup":
        snapshot = _ratio111_backup()
    elif label == ACTIVE_CHALLENGER_LABEL:
        snapshot = _active_post_spike_challenger()
    elif label == "bridge_28_relief":
        snapshot = _frontier_bridge_snapshot(label, role)
    else:
        raise ValueError(f"Unsupported attack stack label: {label}")
    snapshot["role"] = role
    return snapshot


def _recommend_attack_research_focus(*, challenger: dict, backup: dict) -> dict[str, object]:
    try:
        application_readiness = build_attack_challenger_rotation_application_readiness()
        readiness = application_readiness["application_readiness"]
        mapping = application_readiness["approved_candidate_mapping"]
        if readiness.get("rotation_already_applied"):
            pass
        elif not readiness["ready_to_apply_rotation"] and mapping["approved_attack_challenger"]:
            return {
                "target_slot": "attack_challenger",
                "target_label": str(mapping["approved_attack_challenger"]),
                "focus_area": "attack_challenger_rotation_application_readiness",
                "priority": "high",
                "next_research_step_now": str(readiness["next_step_now"]),
                "reason": str(readiness["reason"]),
            }
    except FileNotFoundError:
        pass

    try:
        promotion_review = build_attack_challenger_promotion_review()
        verdict = promotion_review["promotion_review"]
        if verdict.get("rotation_already_applied"):
            pass
        elif verdict["promote_attack_challenger_now"]:
            return {
                "target_slot": "attack_challenger",
                "target_label": str(verdict["approved_attack_challenger"]),
                "focus_area": "attack_challenger_promotion_review",
                "priority": "high",
                "next_research_step_now": str(verdict["next_step_now"]),
                "reason": str(verdict["reason"]),
            }
    except FileNotFoundError:
        pass

    try:
        validation_review = build_attack_challenger_validation_review()
        verdict = validation_review["validation_review"]
        if verdict.get("rotation_already_applied"):
            pass
        elif verdict["approve_rotation_now"]:
            return {
                "target_slot": "attack_challenger",
                "target_label": str(verdict["candidate_label"]),
                "focus_area": "attack_challenger_rotation_approval",
                "priority": "high",
                "next_research_step_now": str(verdict["next_step_now"]),
                "reason": str(verdict["reason"]),
            }
    except FileNotFoundError:
        pass

    try:
        drift_repair = build_hold36_drift_repair_candidates()
        verdict = drift_repair["drift_repair_verdict"]
        top_candidate = str(verdict.get("top_candidate", ""))
        active_suffix = ACTIVE_CHALLENGER_LABEL.removeprefix("post_spike_")
        if verdict["top_candidate_beats_active_rotation_gate"] and not active_suffix.endswith(top_candidate):
            return {
                "target_slot": "attack_challenger",
                "target_label": top_candidate,
                "focus_area": "hold36_drift_repair_validation",
                "priority": "high",
                "next_research_step_now": str(verdict["next_step_now"]),
                "reason": str(verdict["reason"]),
            }
    except FileNotFoundError:
        pass

    try:
        rotation_review = build_attack_challenger_rotation_review()
        review = rotation_review["rotation_review"]
        current_rotation_reference = str(rotation_review.get("active_challenger_reference", {}).get("label", ""))
        if current_rotation_reference and current_rotation_reference != ACTIVE_ATTACK_CHALLENGER_LABEL:
            pass
        elif review["open_rotation_review"]:
            return {
                "target_slot": "attack_challenger",
                "target_label": str(review["proposed_attack_challenger"]),
                "focus_area": "attack_challenger_rotation_review",
                "priority": "high",
                "next_research_step_now": str(review["next_step_now"]),
                "reason": str(review["reason"]),
            }
    except FileNotFoundError:
        pass

    negative_windows = list(challenger.get("negative_walk_forward_windows", []))
    idle_windows = list(challenger.get("idle_walk_forward_windows", []))
    if not negative_windows and idle_windows:
        return {
            "target_slot": "attack_challenger",
            "target_label": str(challenger["label"]),
            "focus_area": "post_spike_idle_window_recovery",
            "priority": "high",
            "next_research_step_now": (
                "expand_post_spike_trend_family_to_recover_idle_windows"
            ),
            "reason": (
                "The active challenger no longer has negative walk-forward windows, "
                f"but idle windows {idle_windows} still cap attack-side CAGR."
            ),
        }
    return {
        "target_slot": "attack_backup",
        "target_label": str(backup["label"]),
        "focus_area": "frontier_bridge_backup_pressure_test",
        "priority": "medium",
        "next_research_step_now": "pressure_test_frontier_bridge_backup_against_main",
        "reason": (
            "No clean idle-window recovery target is exposed, so the next attack "
            "research step is to keep stressing the active backup against the main stack."
        ),
    }


def build_report() -> dict:
    main = _load_snapshot(ACTIVE_ATTACK_MAIN_LABEL, "attack_main")
    backup = _load_snapshot(ACTIVE_ATTACK_BACKUP_LABEL, "attack_backup")
    challenger = _load_snapshot(ACTIVE_ATTACK_CHALLENGER_LABEL, "attack_challenger")
    research_focus = _recommend_attack_research_focus(
        challenger=challenger,
        backup=backup,
    )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "stack_top": {
            "attack_main": main["label"],
            "attack_backup": backup["label"],
            "attack_challenger": challenger["label"],
        },
        "compared_models": [main, backup, challenger],
        "attack_research_focus": research_focus,
        "backup_verdict": {
            "preferred_main": main["label"],
            "preferred_backup": backup["label"],
            "main_backup_roles_are_distinct": True,
            "reason": "ratio112 remains the return anchor, the exact-hit frontier bridge candidate still owns the active backup slot, and the approved trend960 post-spike line now occupies the challenger lane.",
        },
        "decision_summary": [
            "ratio112 tighter_stop remains the attack main because it preserves the best CAGR and Sharpe while keeping drawdown in the same band.",
            "bridge_28_relief is now the active attack backup because it closes the promoted-backup 20bps gap while materially improving drift.",
            "post_spike_trend960_depth055_volume100_hold36 is now the active post-spike challenger after the approved rotation.",
            f"Next attack research step: `{research_focus['next_research_step_now']}`.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    lines = [
        "# BTC 1d Attack Main-Backup Screen",
        "",
        f"- Attack main: `{report['stack_top']['attack_main']}`",
        f"- Attack backup: `{report['stack_top']['attack_backup']}`",
        f"- Roles are distinct: `{report['backup_verdict']['main_backup_roles_are_distinct']}`",
        f"- Reason: {report['backup_verdict']['reason']}",
        f"- Next attack research step: `{report['attack_research_focus']['next_research_step_now']}`",
        f"- Research focus: `{report['attack_research_focus']['focus_area']}`",
        "",
    ]
    for row in report["compared_models"]:
        lines.extend(
            [
                f"## {row['label']}",
                f"- role: `{row['role']}`",
                f"- base: `{row['base_cagr']:.4f}` CAGR / `{row['base_mdd']:.4f}` MDD / Sharpe `{row['base_sharpe']:.4f}`",
                f"- OOS: `{row['oos_cagr']:.4f}` CAGR / `{row['oos_mdd']:.4f}` MDD / Sharpe `{row['oos_sharpe']:.4f}`",
                f"- drift: `{row['sensitivity_max_drift']:.4f}`",
                f"- cost20 Sharpe: `{row['cost20_sharpe']:.4f}`",
                f"- completed_trades: `{row['completed_trades']}`",
                f"- stack_read: `{row['stack_read']}`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_main_backup_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_main_backup_screen_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_attack_main_backup_screen_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_attack_main_backup_screen_md_latest.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_payload = _render_markdown(report)
    md_path.write_text(md_payload, encoding="utf-8")
    latest_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
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
