from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_post_spike_reopen_kickoff_review import (
    build_report as build_reopen_kickoff_review,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest_json(prefix: str) -> Path:
    matches = sorted(ANALYSIS_DIR.glob(f"{prefix}*.json"))
    if not matches:
        raise FileNotFoundError(f"No analysis result found for prefix: {prefix}")
    return matches[-1]


def _load_frontier() -> tuple[dict, Path]:
    path = _latest_json("btc_1d_post_spike_exit_tradeoff_frontier_")
    return _load_json(path), path


def _pick_exact_hit(frontier_payload: dict, preferred_label: str) -> dict:
    frontier_rows = list(frontier_payload.get("pareto_frontier", []) or [])
    exact_hits = [
        row
        for row in frontier_rows
        if bool(row.get("rotation_gap_passed", False))
        and bool(row.get("drift_guardrail_passed", False))
        and int(row.get("negative_window_count", 0)) == 0
    ]
    preferred = next(
        (row for row in exact_hits if str(row.get("variant_label")) == preferred_label),
        None,
    )
    if preferred is not None:
        return preferred
    if exact_hits:
        return exact_hits[0]
    raise ValueError("No exact-hit candidate found in frontier payload.")


def _load_cost20_confirmation(preferred_label: str) -> tuple[dict | None, Path | None]:
    matches = sorted(ANALYSIS_DIR.glob("btc_1d_walk_forward_diagnostic_*.json"), reverse=True)
    for path in matches:
        payload = _load_json(path)
        config = dict(payload.get("config", {}) or {})
        candidate_label = str(config.get("candidate_label", ""))
        if preferred_label not in candidate_label:
            continue
        if float(config.get("fee_bps", 0.0)) < 20.0 or float(config.get("slippage_bps", 0.0)) < 20.0:
            continue
        return payload, path
    return None, None


def _extract_cost20_sensitivity(payload: dict) -> tuple[float | None, list[int], list[int]]:
    if "walk_forward_sensitivity" in payload:
        sensitivity = dict(payload.get("walk_forward_sensitivity", {}) or {})
        return (
            float(sensitivity.get("sensitivity_max_drift", 0.0)),
            list(sensitivity.get("negative_windows", []) or []),
            list(sensitivity.get("idle_windows", []) or []),
        )

    overfitting = dict(payload.get("overfitting", {}) or {})
    walk_forward = list(overfitting.get("walk_forward", []) or [])
    negative_windows = []
    idle_windows = []
    for row in walk_forward:
        metrics = dict(row.get("metrics", {}) or {})
        window = int(row.get("window", 0))
        if int(metrics.get("trades", 0)) == 0:
            idle_windows.append(window)
        if float(metrics.get("cagr", 0.0)) < 0.0:
            negative_windows.append(window)
    sensitivity_max_drift = overfitting.get("sensitivity_max_drift")
    return (
        float(sensitivity_max_drift) if sensitivity_max_drift is not None else None,
        negative_windows,
        idle_windows,
    )


def build_report() -> dict:
    kickoff = build_reopen_kickoff_review()
    preferred = dict(kickoff["preferred_seed_metrics"])
    backup = dict(kickoff["backup_seed_metrics"])
    kickoff_meta = dict(kickoff["reopen_kickoff"])
    frontier_payload, frontier_path = _load_frontier()
    exact_hit = _pick_exact_hit(frontier_payload, str(preferred["candidate_label"]))
    cost20_payload, cost20_path = _load_cost20_confirmation(str(preferred["candidate_label"]))

    frontier_targets = dict(frontier_payload.get("targets", {}) or {})
    max_drift = float(frontier_targets.get("max_sensitivity_drift", 0.2))
    max_negative_windows = int(frontier_targets.get("max_negative_window_count", 0))
    frontier_exact_hit_confirmed = (
        bool(exact_hit.get("rotation_gap_passed", False))
        and bool(exact_hit.get("drift_guardrail_passed", False))
        and int(exact_hit.get("negative_window_count", 0)) <= max_negative_windows
    )

    cost20_confirmation_available = cost20_payload is not None
    cost20_negative_windows = []
    cost20_idle_windows = []
    cost20_sensitivity_max_drift = None
    cost20_base_cagr = None
    cost20_base_sharpe = None
    cost20_base_max_drawdown = None
    if cost20_payload is not None:
        base_metrics = dict(cost20_payload.get("base_metrics", {}) or {})
        (
            cost20_sensitivity_max_drift,
            cost20_negative_windows,
            cost20_idle_windows,
        ) = _extract_cost20_sensitivity(cost20_payload)
        cost20_base_cagr = float(base_metrics.get("cagr", 0.0))
        cost20_base_sharpe = float(base_metrics.get("sharpe", 0.0))
        cost20_base_max_drawdown = float(base_metrics.get("max_drawdown", 0.0))

    cost20_guardrail_passed = (
        cost20_confirmation_available
        and cost20_sensitivity_max_drift is not None
        and cost20_sensitivity_max_drift <= max_drift
        and len(cost20_negative_windows) <= max_negative_windows
    )
    rotation_review_ready = (
        str(kickoff_meta.get("next_step_now")) == "launch_exact_hit_rotation_review"
        and frontier_exact_hit_confirmed
        and cost20_guardrail_passed
    )
    preferred_label = str(preferred["candidate_label"])
    backup_label = str(backup["candidate_label"])

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "rotation_review_reference": {
            "attack_main": kickoff["kickoff_reference"]["attack_main"],
            "promoted_backup": kickoff["kickoff_reference"]["promoted_backup"],
            "monitoring_candidate": kickoff["kickoff_reference"]["monitoring_candidate"],
            "preferred_exact_hit_candidate": preferred_label,
            "backup_seed_candidate": backup_label,
            "kickoff_next_step_now": kickoff_meta["next_step_now"],
            "kickoff_execution_order": list(kickoff_meta.get("execution_order", []) or []),
        },
        "frontier_exact_hit_review": {
            "frontier_json": str(frontier_path),
            "preferred_exact_hit_source": str(exact_hit["source"]),
            "preferred_exact_hit_variant_label": str(exact_hit["variant_label"]),
            "base_cagr": float(exact_hit["base_cagr"]),
            "base_sharpe": float(exact_hit["base_sharpe"]),
            "base_max_drawdown": float(exact_hit["base_max_drawdown"]),
            "sensitivity_max_drift": float(exact_hit["sensitivity_max_drift"]),
            "cagr_gap_to_backup": float(exact_hit["cagr_gap_to_backup"]),
            "negative_window_count": int(exact_hit["negative_window_count"]),
            "idle_window_count": int(exact_hit.get("idle_window_count", 0)),
            "rotation_gap_passed": bool(exact_hit["rotation_gap_passed"]),
            "drift_guardrail_passed": bool(exact_hit["drift_guardrail_passed"]),
            "parameters": dict(exact_hit.get("parameters", {}) or {}),
        },
        "cost20_confirmation_review": {
            "cost20_confirmation_available": cost20_confirmation_available,
            "diagnostic_json": str(cost20_path) if cost20_path is not None else None,
            "base_cagr": cost20_base_cagr,
            "base_sharpe": cost20_base_sharpe,
            "base_max_drawdown": cost20_base_max_drawdown,
            "sensitivity_max_drift": cost20_sensitivity_max_drift,
            "negative_windows": cost20_negative_windows,
            "idle_windows": cost20_idle_windows,
            "cost20_guardrail_passed": cost20_guardrail_passed,
        },
        "backup_seed_comparison": {
            "backup_seed_candidate": backup_label,
            "backup_seed_source": kickoff_meta["backup_seed_source"],
            "backup_seed_class": kickoff_meta["backup_seed_class"],
            "backup_base_cagr": float(backup["base_cagr"]),
            "backup_base_sharpe": float(backup["base_sharpe"]),
            "backup_base_max_drawdown": float(backup["base_max_drawdown"]),
            "backup_sensitivity_max_drift": float(backup["sensitivity_max_drift"]),
            "backup_negative_window_count": int(backup["negative_window_count"]),
            "preferred_cagr_edge_vs_backup": float(preferred["base_cagr"]) - float(backup["base_cagr"]),
            "preferred_sharpe_edge_vs_backup": float(preferred["base_sharpe"]) - float(backup["base_sharpe"]),
            "preferred_mdd_improvement_vs_backup": float(backup["base_max_drawdown"]) - float(preferred["base_max_drawdown"]),
            "preferred_drift_improvement_vs_backup": float(backup["sensitivity_max_drift"]) - float(preferred["sensitivity_max_drift"]),
        },
        "rotation_gate": {
            "max_cagr_gap_to_backup": float(frontier_targets.get("max_cagr_gap_to_backup", 0.0)),
            "max_sensitivity_drift": max_drift,
            "max_negative_window_count": max_negative_windows,
            "frontier_exact_hit_confirmed": frontier_exact_hit_confirmed,
            "cost20_confirmation_available": cost20_confirmation_available,
            "cost20_guardrail_passed": cost20_guardrail_passed,
            "rotation_review_ready": rotation_review_ready,
            "promote_exact_hit_now": rotation_review_ready,
            "next_step_now": (
                "compare_exact_hit_against_attack_main_and_promoted_backup"
                if rotation_review_ready
                else "repair_exact_hit_rotation_review_inputs"
            ),
            "reason": (
                "Preferred exact-hit seed clears frontier guardrails and its 20bps confirmation still stays inside the drift and negative-window limits."
                if rotation_review_ready
                else "Preferred exact-hit seed is identified, but the review is not yet promotable until frontier and 20bps confirmation remain aligned."
            ),
        },
        "decision_summary": [
            f"Preferred exact-hit candidate is `{preferred_label}` and kickoff already routes it into rotation review.",
            (
                f"20bps confirmation remains viable with CAGR `{cost20_base_cagr:.6f}`, Sharpe `{cost20_base_sharpe:.6f}`, MDD `{cost20_base_max_drawdown:.6f}`, and drift `{cost20_sensitivity_max_drift:.6f}`."
                if cost20_confirmation_available
                else "A matching 20bps confirmation artifact was not found for the preferred exact-hit candidate."
            ),
            f"Backup comparison stays anchored on `{backup_label}` so the next attack-model comparison can measure exact-hit promotion quality against the current reopen fallback.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    review = report["frontier_exact_hit_review"]
    cost20 = report["cost20_confirmation_review"]
    backup = report["backup_seed_comparison"]
    gate = report["rotation_gate"]
    lines = [
        "# BTC 1d Post-Spike Exact-Hit Rotation Review",
        "",
        f"- Attack main: `{report['rotation_review_reference']['attack_main']}`",
        f"- Promoted backup: `{report['rotation_review_reference']['promoted_backup']}`",
        f"- Preferred exact-hit candidate: `{report['rotation_review_reference']['preferred_exact_hit_candidate']}`",
        f"- Backup seed candidate: `{report['rotation_review_reference']['backup_seed_candidate']}`",
        f"- Rotation review ready: `{gate['rotation_review_ready']}`",
        f"- Promote exact hit now: `{gate['promote_exact_hit_now']}`",
        f"- Next step now: `{gate['next_step_now']}`",
        "",
        "## Frontier Review",
        f"- Source: `{review['preferred_exact_hit_source']}`",
        f"- CAGR=`{review['base_cagr']}` Sharpe=`{review['base_sharpe']}` MDD=`{review['base_max_drawdown']}` drift=`{review['sensitivity_max_drift']}` gap_to_backup=`{review['cagr_gap_to_backup']}`",
        "",
        "## Cost20 Confirmation",
        f"- Available: `{cost20['cost20_confirmation_available']}`",
        f"- Guardrail passed: `{cost20['cost20_guardrail_passed']}`",
        f"- CAGR=`{cost20['base_cagr']}` Sharpe=`{cost20['base_sharpe']}` MDD=`{cost20['base_max_drawdown']}` drift=`{cost20['sensitivity_max_drift']}`",
        "",
        "## Backup Comparison",
        f"- Preferred CAGR edge vs backup: `{backup['preferred_cagr_edge_vs_backup']}`",
        f"- Preferred Sharpe edge vs backup: `{backup['preferred_sharpe_edge_vs_backup']}`",
        f"- Preferred MDD improvement vs backup: `{backup['preferred_mdd_improvement_vs_backup']}`",
        f"- Preferred drift improvement vs backup: `{backup['preferred_drift_improvement_vs_backup']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_exact_hit_rotation_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_exact_hit_rotation_review_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "report": report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
