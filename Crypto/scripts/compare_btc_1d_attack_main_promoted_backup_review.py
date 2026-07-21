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
    ACTIVE_ATTACK_MAIN_LABEL,
)
from scripts.compare_btc_1d_attack_main_backup_screen import (
    build_report as build_attack_stack_screen,
)
from scripts.compare_btc_1d_post_spike_bridge_backup_negative_window_repair_review import (
    build_report as build_bridge_backup_negative_window_repair_review,
)


ANALYSIS_DIR = Path("analysis_results")
LEGACY_POST_SPIKE_BACKUP_LABEL = "post_spike_trend92_depth058_volume105_hold34"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest(pattern: str) -> Path:
    matches = sorted(ANALYSIS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No analysis artifact matched pattern: {pattern}")
    return matches[0]


def _load_recovery_candidate() -> dict | None:
    try:
        payload = _load_json(_latest("btc_1d_post_spike_consolidation_breakout_main_pressure_recovery_batch_*.json"))
    except FileNotFoundError:
        return None
    best_variant = dict(payload.get("best_variant", {}) or {})
    if not best_variant:
        return None
    if int(best_variant.get("negative_window_count", 0)) > 0:
        return None
    if not bool(best_variant.get("quality_pressure_passed", False)):
        return None
    return best_variant


def _load_bridge_negative_window_repair_candidate() -> dict | None:
    try:
        repair_review = build_bridge_backup_negative_window_repair_review()
    except FileNotFoundError:
        return None
    verdict = dict(repair_review.get("repair_review_verdict", {}) or {})
    if not bool(verdict.get("negative_window_repair_found", False)):
        return None
    best_variant = dict(repair_review.get("best_completed_variant", {}) or {})
    if not best_variant:
        return None
    if str(best_variant.get("variant_label", "")) != ACTIVE_ATTACK_BACKUP_LABEL:
        return None
    return best_variant


def build_report() -> dict:
    screen = build_attack_stack_screen()
    snapshots = {row["label"]: row for row in screen["compared_models"]}
    main = snapshots[ACTIVE_ATTACK_MAIN_LABEL]
    promoted_backup = snapshots[ACTIVE_ATTACK_BACKUP_LABEL]
    recovery_candidate = _load_recovery_candidate()
    bridge_repair_candidate = _load_bridge_negative_window_repair_candidate()

    monitoring_candidate_label = ACTIVE_ATTACK_BACKUP_LABEL
    monitoring_base_cagr = float(promoted_backup["base_cagr"])
    monitoring_cost20_cagr = float(promoted_backup["cost20_cagr"])
    monitoring_sharpe = float(promoted_backup["base_sharpe"])
    monitoring_max_drawdown = float(promoted_backup["base_mdd"])
    monitoring_drift = float(promoted_backup["sensitivity_max_drift"])
    monitoring_failed_gates = list(promoted_backup.get("failed_gates", []))
    monitoring_negative_walk_forward_windows = list(promoted_backup.get("negative_walk_forward_windows", []))
    monitoring_idle_walk_forward_windows = list(promoted_backup.get("idle_walk_forward_windows", []))
    if (
        ACTIVE_ATTACK_BACKUP_LABEL == LEGACY_POST_SPIKE_BACKUP_LABEL
        and recovery_candidate
        and float(recovery_candidate["base_cagr_gap_to_main"]) < float(main["base_cagr"]) - float(promoted_backup["base_cagr"])
    ):
        monitoring_candidate_label = f"{ACTIVE_ATTACK_BACKUP_LABEL}::{recovery_candidate['variant_label']}"
        monitoring_base_cagr = float(recovery_candidate["base_cagr"])
        monitoring_cost20_cagr = float(recovery_candidate["base_cagr"])
        monitoring_sharpe = float(recovery_candidate["base_sharpe"])
        monitoring_max_drawdown = float(recovery_candidate["base_max_drawdown"])
        monitoring_drift = float(recovery_candidate["sensitivity_max_drift"])
        monitoring_failed_gates = []
        monitoring_negative_walk_forward_windows = []
        monitoring_idle_walk_forward_windows = list(recovery_candidate.get("idle_windows", []))
    elif ACTIVE_ATTACK_BACKUP_LABEL == "bridge_28_relief" and bridge_repair_candidate:
        monitoring_candidate_label = f"{ACTIVE_ATTACK_BACKUP_LABEL}::negative_window_repair"
        monitoring_base_cagr = float(bridge_repair_candidate["base_cagr"])
        monitoring_cost20_cagr = float(bridge_repair_candidate["cost20_cagr"])
        monitoring_sharpe = float(bridge_repair_candidate["base_sharpe"])
        monitoring_max_drawdown = float(bridge_repair_candidate["base_max_drawdown"])
        monitoring_drift = float(bridge_repair_candidate["max_sensitivity_drift"])
        monitoring_failed_gates = []
        monitoring_negative_walk_forward_windows = list(bridge_repair_candidate.get("cost20_negative_windows", []))
        monitoring_idle_walk_forward_windows = list(bridge_repair_candidate.get("cost20_idle_windows", []))

    cagr_gap_to_main = float(main["base_cagr"]) - monitoring_base_cagr
    cost20_cagr_gap_to_main = float(main["cost20_cagr"]) - monitoring_cost20_cagr
    sharpe_edge_vs_main = monitoring_sharpe - float(main["base_sharpe"])
    mdd_improvement_vs_main = abs(float(main["base_mdd"])) - abs(monitoring_max_drawdown)
    drift_improvement_vs_main = float(main["sensitivity_max_drift"]) - monitoring_drift
    failed_gates = monitoring_failed_gates
    negative_walk_forward_windows = monitoring_negative_walk_forward_windows
    idle_walk_forward_windows = monitoring_idle_walk_forward_windows
    negative_window_watch = (
        "negative_walk_forward_window" in failed_gates or bool(negative_walk_forward_windows)
    )

    pressure_ready = (
        sharpe_edge_vs_main > 0.15
        and mdd_improvement_vs_main > 0.05
        and drift_improvement_vs_main > 0.15
    )
    clean_monitoring_ready = pressure_ready and not negative_window_watch
    replace_main_now = (
        clean_monitoring_ready
        and cagr_gap_to_main <= 0.04
        and cost20_cagr_gap_to_main <= 0.06
    )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "active_stack_reference": {
            "attack_main": ACTIVE_ATTACK_MAIN_LABEL,
            "promoted_attack_backup": ACTIVE_ATTACK_BACKUP_LABEL,
            "monitoring_candidate": monitoring_candidate_label,
        },
        "main_vs_promoted_backup_metrics": {
            "attack_main_base_cagr": float(main["base_cagr"]),
            "promoted_backup_base_cagr": monitoring_base_cagr,
            "base_cagr_gap_to_main": cagr_gap_to_main,
            "attack_main_cost20_cagr": float(main["cost20_cagr"]),
            "promoted_backup_cost20_cagr": monitoring_cost20_cagr,
            "cost20_cagr_gap_to_main": cost20_cagr_gap_to_main,
            "sharpe_edge_vs_main": sharpe_edge_vs_main,
            "mdd_improvement_vs_main": mdd_improvement_vs_main,
            "drift_improvement_vs_main": drift_improvement_vs_main,
        },
        "recovery_candidate_review": (
            {
                "recovery_variant_label": str(recovery_candidate["variant_label"]),
                "is_active_monitoring_candidate": monitoring_candidate_label.endswith(str(recovery_candidate["variant_label"])),
                "base_cagr_gap_to_main": float(recovery_candidate["base_cagr_gap_to_main"]),
                "cost20_cagr_gap_to_main": float(recovery_candidate["cost20_cagr_gap_to_main"]),
                "quality_pressure_passed": bool(recovery_candidate["quality_pressure_passed"]),
                "negative_window_count": int(recovery_candidate["negative_window_count"]),
            }
            if recovery_candidate and ACTIVE_ATTACK_BACKUP_LABEL == LEGACY_POST_SPIKE_BACKUP_LABEL
            else None
        ),
        "bridge_negative_window_repair_review": (
            {
                "repaired_variant_label": str(bridge_repair_candidate["variant_label"]),
                "is_active_monitoring_candidate": monitoring_candidate_label.endswith("negative_window_repair"),
                "base_cagr_gap_to_main": cagr_gap_to_main,
                "cost20_cagr_gap_to_main": cost20_cagr_gap_to_main,
                "negative_window_repair_passed": bool(bridge_repair_candidate["negative_window_repair_passed"]),
                "base_negative_window_count": int(bridge_repair_candidate["base_negative_window_count"]),
                "cost20_negative_window_count": int(bridge_repair_candidate["cost20_negative_window_count"]),
            }
            if bridge_repair_candidate and ACTIVE_ATTACK_BACKUP_LABEL == "bridge_28_relief"
            else None
        ),
        "promoted_backup_risk_watch": {
            "failed_gates": failed_gates,
            "negative_window_watch": negative_window_watch,
            "negative_walk_forward_windows": negative_walk_forward_windows,
            "idle_walk_forward_windows": idle_walk_forward_windows,
            "clean_monitoring_ready": clean_monitoring_ready,
        },
        "promotion_pressure_gate": {
            "required_min_sharpe_edge": 0.15,
            "required_min_mdd_improvement": 0.05,
            "required_min_drift_improvement": 0.15,
            "allowed_max_base_cagr_gap": 0.04,
            "allowed_max_cost20_cagr_gap": 0.06,
        },
        "promotion_pressure_verdict": {
            "promoted_backup_has_main_pressure": pressure_ready,
            "promoted_backup_clean_monitoring_ready": clean_monitoring_ready,
            "replace_attack_main_now": replace_main_now,
            "keep_attack_main": True,
            "keep_promoted_backup": True,
            "next_step_now": (
                "open_attack_main_replacement_review"
                if replace_main_now
                else "repair_negative_walk_forward_window"
                if negative_window_watch
                else "monitor_promoted_backup_against_active_main"
            ),
            "reason": (
                "The promoted backup now matches the main closely enough on return while retaining a large quality edge, so main replacement review can open."
                if replace_main_now
                else "The promoted backup still has a real quality edge over the main, but it is carrying a negative walk-forward window signal, so it stays active only under repair watch rather than clean replacement monitoring."
                if negative_window_watch
                else "The monitored backup repair clears the negative walk-forward window, but return gaps and quality-pressure checks are not strong enough for main replacement."
                if not pressure_ready
                else "The promoted backup has a real quality edge over the main, but the CAGR gap is still too large for main replacement, so it should be monitored rather than promoted again."
            ),
        },
        "decision_summary": [
            f"Keep `{ACTIVE_ATTACK_MAIN_LABEL}` as the active attack main for now.",
            (
                f"Keep `{ACTIVE_ATTACK_BACKUP_LABEL}` as the promoted backup, but monitor the repaired bridge variant because it clears the negative walk-forward window."
                if bridge_repair_candidate
                else f"Keep `{ACTIVE_ATTACK_BACKUP_LABEL}` as the promoted backup because it materially improves Sharpe, drawdown, and drift against the main."
            ),
            (
                f"Monitor recovery candidate `{monitoring_candidate_label}` because it improves the current main-gap profile without losing the quality-pressure gate."
                if monitoring_candidate_label != ACTIVE_ATTACK_BACKUP_LABEL
                else "Current promoted backup remains the best monitoring candidate against the main."
            ),
            (
                f"Current gaps are base CAGR `{cagr_gap_to_main:.6f}` and cost20 CAGR `{cost20_cagr_gap_to_main:.6f}`, but negative walk-forward windows `{negative_walk_forward_windows}` keep the backup on repair watch before any main-replacement escalation."
                if negative_window_watch
                else f"Current gaps are base CAGR `{cagr_gap_to_main:.6f}` and cost20 CAGR `{cost20_cagr_gap_to_main:.6f}`, so the correct next step is monitoring rather than immediate main replacement."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    metrics = report["main_vs_promoted_backup_metrics"]
    verdict = report["promotion_pressure_verdict"]
    gate = report["promotion_pressure_gate"]
    risk_watch = report["promoted_backup_risk_watch"]
    lines = [
        "# BTC 1d Attack Main vs Promoted Backup Review",
        "",
        f"- Attack main: `{report['active_stack_reference']['attack_main']}`",
        f"- Promoted backup: `{report['active_stack_reference']['promoted_attack_backup']}`",
        f"- Monitoring candidate: `{report['active_stack_reference']['monitoring_candidate']}`",
        f"- Promoted backup has main pressure: `{verdict['promoted_backup_has_main_pressure']}`",
        f"- Promoted backup clean monitoring ready: `{verdict['promoted_backup_clean_monitoring_ready']}`",
        f"- Replace attack main now: `{verdict['replace_attack_main_now']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Metrics",
        f"- Base CAGR gap to main: `{metrics['base_cagr_gap_to_main']}`",
        f"- Cost20 CAGR gap to main: `{metrics['cost20_cagr_gap_to_main']}`",
        f"- Sharpe edge vs main: `{metrics['sharpe_edge_vs_main']}`",
        f"- MDD improvement vs main: `{metrics['mdd_improvement_vs_main']}`",
        f"- Drift improvement vs main: `{metrics['drift_improvement_vs_main']}`",
        "",
        "## Risk Watch",
        f"- failed_gates: `{risk_watch['failed_gates']}`",
        f"- negative_window_watch: `{risk_watch['negative_window_watch']}`",
        f"- negative_walk_forward_windows: `{risk_watch['negative_walk_forward_windows']}`",
        f"- idle_walk_forward_windows: `{risk_watch['idle_walk_forward_windows']}`",
        "",
        "## Gate",
        f"- required_min_sharpe_edge: `{gate['required_min_sharpe_edge']}`",
        f"- required_min_mdd_improvement: `{gate['required_min_mdd_improvement']}`",
        f"- required_min_drift_improvement: `{gate['required_min_drift_improvement']}`",
        f"- allowed_max_base_cagr_gap: `{gate['allowed_max_base_cagr_gap']}`",
        f"- allowed_max_cost20_cagr_gap: `{gate['allowed_max_cost20_cagr_gap']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_main_promoted_backup_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_main_promoted_backup_review_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_attack_main_promoted_backup_review_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_attack_main_promoted_backup_review_latest.md"
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
