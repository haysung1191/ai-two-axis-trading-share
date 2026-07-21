from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_main_promoted_backup_review import (
    build_report as build_main_vs_backup_review,
)
from scripts.compare_btc_1d_post_spike_exact_hit_backup_replacement_review import (
    build_report as build_backup_replacement_review,
)
from scripts.attack_active_stack import (
    ACTIVE_ATTACK_BACKUP_LABEL,
    ACTIVE_ATTACK_CHALLENGER_LABEL,
    ACTIVE_ATTACK_MAIN_LABEL,
)


ANALYSIS_DIR = Path("analysis_results")


def build_report() -> dict:
    try:
        replacement = build_backup_replacement_review()
        main_vs_backup = build_main_vs_backup_review()
    except (FileNotFoundError, KeyError, ValueError) as exc:
        missing_artifact = str(exc)
        return {
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "bridge_monitor_reference": {
                "attack_main": ACTIVE_ATTACK_MAIN_LABEL,
                "bridge_backup": ACTIVE_ATTACK_BACKUP_LABEL,
                "previous_promoted_backup": "",
                "attack_challenger": ACTIVE_ATTACK_CHALLENGER_LABEL,
            },
            "main_replacement_watch": {
                "base_cagr_gap_to_main": None,
                "cost20_cagr_gap_to_main": None,
                "sharpe_edge_vs_main": None,
                "mdd_improvement_vs_main": None,
                "drift_improvement_vs_main": None,
                "quality_pressure_ready": False,
                "cost20_gap_open": False,
                "base_gap_open": False,
                "failed_gates": ["missing_required_analysis_artifact"],
                "negative_window_watch": True,
                "negative_walk_forward_windows": [5],
                "idle_walk_forward_windows": [],
                "blocking_reasons": ["missing_required_analysis_artifact"],
                "primary_blocker": "missing_required_analysis_artifact",
                "missing_artifact": missing_artifact,
            },
            "main_replacement_verdict": {
                "backup_replacement_ready": False,
                "open_attack_main_replacement_review": False,
                "keep_attack_main": True,
                "keep_bridge_backup": True,
                "next_step_now": "regenerate_missing_bridge_review_artifacts",
                "reason": (
                    "Main replacement review is blocked because a required upstream analysis artifact is missing. "
                    "Keep the active attack main and bridge backup unchanged."
                ),
            },
            "decision_summary": [
                f"`{ACTIVE_ATTACK_BACKUP_LABEL}` remains the active bridge backup, but main replacement review is blocked.",
                f"Missing upstream artifact: `{missing_artifact}`.",
                "Regenerate the missing bridge review artifacts before reopening attack-main replacement review.",
            ],
        }

    reference = dict(replacement["replacement_reference"])
    metrics = dict(main_vs_backup["main_vs_promoted_backup_metrics"])
    gate = dict(main_vs_backup["promotion_pressure_gate"])
    risk_watch = dict(main_vs_backup.get("promoted_backup_risk_watch", {}))

    base_gap = float(metrics["base_cagr_gap_to_main"])
    cost20_gap = float(metrics["cost20_cagr_gap_to_main"])
    sharpe_edge = float(metrics["sharpe_edge_vs_main"])
    mdd_improvement = float(metrics["mdd_improvement_vs_main"])
    drift_improvement = float(metrics["drift_improvement_vs_main"])
    negative_window_watch = bool(risk_watch.get("negative_window_watch", False))
    negative_walk_forward_windows = list(risk_watch.get("negative_walk_forward_windows", []))
    idle_walk_forward_windows = list(risk_watch.get("idle_walk_forward_windows", []))
    failed_gates = list(risk_watch.get("failed_gates", []))

    quality_pressure_ready = (
        sharpe_edge > float(gate["required_min_sharpe_edge"])
        and mdd_improvement > float(gate["required_min_mdd_improvement"])
        and drift_improvement > float(gate["required_min_drift_improvement"])
    )
    cost20_gap_open = cost20_gap <= float(gate["allowed_max_cost20_cagr_gap"])
    base_gap_open = base_gap <= float(gate["allowed_max_base_cagr_gap"])
    open_attack_main_replacement_review = bool(
        replacement["backup_replacement_verdict"]["backup_replacement_ready"]
        and quality_pressure_ready
        and cost20_gap_open
        and base_gap_open
        and not negative_window_watch
    )
    blocking_reasons: list[str] = []
    if negative_window_watch:
        blocking_reasons.append("negative_walk_forward_window")
    if not base_gap_open:
        blocking_reasons.append("base_cagr_gap")
    if not cost20_gap_open:
        blocking_reasons.append("cost20_cagr_gap")
    if not quality_pressure_ready:
        blocking_reasons.append("quality_pressure")
    primary_blocker = blocking_reasons[0] if blocking_reasons else "none"

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "bridge_monitor_reference": {
            "attack_main": reference["attack_main"],
            "bridge_backup": reference["new_attack_backup"],
            "previous_promoted_backup": reference["previous_promoted_backup"],
            "attack_challenger": reference["current_attack_challenger"],
        },
        "main_replacement_watch": {
            "base_cagr_gap_to_main": base_gap,
            "cost20_cagr_gap_to_main": cost20_gap,
            "sharpe_edge_vs_main": sharpe_edge,
            "mdd_improvement_vs_main": mdd_improvement,
            "drift_improvement_vs_main": drift_improvement,
            "quality_pressure_ready": quality_pressure_ready,
            "cost20_gap_open": cost20_gap_open,
            "base_gap_open": base_gap_open,
            "failed_gates": failed_gates,
            "negative_window_watch": negative_window_watch,
            "negative_walk_forward_windows": negative_walk_forward_windows,
            "idle_walk_forward_windows": idle_walk_forward_windows,
            "blocking_reasons": blocking_reasons,
            "primary_blocker": primary_blocker,
        },
        "main_replacement_verdict": {
            "backup_replacement_ready": bool(replacement["backup_replacement_verdict"]["backup_replacement_ready"]),
            "open_attack_main_replacement_review": open_attack_main_replacement_review,
            "keep_attack_main": True,
            "keep_bridge_backup": True,
            "next_step_now": (
                "open_attack_main_replacement_review"
                if open_attack_main_replacement_review
                else "monitor_bridge_backup_against_attack_main"
            ),
            "reason": (
                "The bridge backup now satisfies the quality-pressure and return-gap thresholds strongly enough to open attack-main replacement review."
                if open_attack_main_replacement_review
                else "The bridge backup is the correct active backup, but negative walk-forward window pressure keeps main replacement review closed until the repair signal is cleared."
                if negative_window_watch
                else "The bridge backup repair cleared the negative walk-forward window, but return gaps and quality-pressure checks still keep main replacement review closed."
                if not quality_pressure_ready or not cost20_gap_open
                else "The bridge backup is the correct active backup and already clears the quality-pressure plus cost20 gap checks, but the remaining base CAGR gap is still too large for main replacement."
            ),
        },
        "decision_summary": [
            f"`{reference['new_attack_backup']}` is the correct active backup and should stay on watch against `{reference['attack_main']}`.",
            f"Quality pressure is `{'ready' if quality_pressure_ready else 'not_ready'}`, and the cost20 gap is `{cost20_gap:.6f}` against an allowed max of `{float(gate['allowed_max_cost20_cagr_gap']):.6f}`.",
            (
                f"Blocking reasons are `{blocking_reasons}` with remaining base CAGR gap `{base_gap:.6f}`, so main replacement review stays closed."
                if not open_attack_main_replacement_review
                else "All gate conditions are open, so attack-main replacement review can now open."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    watch = report["main_replacement_watch"]
    verdict = report["main_replacement_verdict"]
    lines = [
        "# BTC 1d Bridge Backup Main Replacement Review",
        "",
        f"- Attack main: `{report['bridge_monitor_reference']['attack_main']}`",
        f"- Bridge backup: `{report['bridge_monitor_reference']['bridge_backup']}`",
        f"- Open attack main replacement review: `{verdict['open_attack_main_replacement_review']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Primary blocker: `{watch['primary_blocker']}`",
        "",
        "## Watch",
        f"- Base CAGR gap to main: `{watch['base_cagr_gap_to_main']}`",
        f"- Cost20 CAGR gap to main: `{watch['cost20_cagr_gap_to_main']}`",
        f"- Sharpe edge vs main: `{watch['sharpe_edge_vs_main']}`",
        f"- MDD improvement vs main: `{watch['mdd_improvement_vs_main']}`",
        f"- Drift improvement vs main: `{watch['drift_improvement_vs_main']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_bridge_backup_main_replacement_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_bridge_backup_main_replacement_review_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_bridge_backup_main_replacement_review_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_bridge_backup_main_replacement_review_latest.md"
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
