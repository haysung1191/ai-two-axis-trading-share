from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.attack_active_stack import ACTIVE_ATTACK_BACKUP_LABEL


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest(pattern: str) -> Path:
    matches = sorted(ANALYSIS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No analysis artifact matched pattern: {pattern}")
    return matches[0]


def _find_seed_result(cycle_payload: dict, seed_label: str) -> dict | None:
    for row in cycle_payload.get("seed_results", []):
        if str(row.get("seed_label")) == seed_label:
            return dict(row)
    return None


def build_report() -> dict:
    cycle_path = _latest("btc_1d_post_spike_reopen_seed_cycle_*.json")
    recovery_path = _latest("btc_1d_post_spike_reopen_seed_main_pressure_recovery_batch_*.json")
    cycle_payload = _load_json(cycle_path)
    recovery_payload = _load_json(recovery_path)

    active_seed_result = _find_seed_result(cycle_payload, ACTIVE_ATTACK_BACKUP_LABEL)
    recovery_seed_label = str(recovery_payload.get("seed_label", ""))
    best_variant = dict(recovery_payload.get("best_variant", {}) or {})

    same_seed_across_lanes = bool(active_seed_result) and recovery_seed_label == ACTIVE_ATTACK_BACKUP_LABEL
    seed_cycle_passed = bool(
        active_seed_result
        and active_seed_result.get("paper_validation_passed")
        and active_seed_result.get("walk_forward_passed")
    )
    quality_pressure_passed = bool(best_variant.get("quality_pressure_passed", False))
    framing_conflict = same_seed_across_lanes and seed_cycle_passed and not quality_pressure_passed

    seed_base_cagr = float(active_seed_result["base_cagr"]) if active_seed_result else None
    seed_sharpe = float(active_seed_result["base_sharpe"]) if active_seed_result else None
    seed_mdd = float(active_seed_result["base_max_drawdown"]) if active_seed_result else None
    seed_drift = float(active_seed_result["sensitivity_max_drift"]) if active_seed_result else None

    recovery_base_cagr = float(best_variant["base_cagr"]) if best_variant else None
    recovery_sharpe = float(best_variant["base_sharpe"]) if best_variant else None
    recovery_mdd = float(best_variant["base_max_drawdown"]) if best_variant else None
    recovery_drift = float(best_variant["sensitivity_max_drift"]) if best_variant else None

    if framing_conflict:
        lane_status = "revalidation_hold"
        next_step_now = "freeze_main_pressure_escalation_and_revalidate_reopen_seed"
        reason = (
            "The active reopen seed passed seed-cycle validation, but it fails the stricter "
            "main-pressure quality gate under the 20bps recovery frame."
        )
    elif same_seed_across_lanes and quality_pressure_passed:
        lane_status = "pressure_watch_eligible"
        next_step_now = "continue_main_pressure_monitoring"
        reason = "The active reopen seed is consistent across the seed-cycle and main-pressure lanes."
    elif not active_seed_result:
        lane_status = "not_applicable"
        next_step_now = "continue_main_pressure_monitoring"
        reason = "The active backup is no longer the reopen seed, so reopen-seed lane reconciliation no longer governs the pressure watch."
    else:
        lane_status = "lane_mismatch_hold"
        next_step_now = "repair_reopen_seed_lane_alignment"
        reason = "The active backup could not be aligned cleanly across the seed-cycle and main-pressure lanes."

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "active_backup_label": ACTIVE_ATTACK_BACKUP_LABEL,
        "artifact_reference": {
            "seed_cycle_json": str(cycle_path),
            "main_pressure_recovery_json": str(recovery_path),
        },
        "lane_alignment": {
            "same_seed_across_lanes": same_seed_across_lanes,
            "seed_cycle_passed": seed_cycle_passed,
            "main_pressure_quality_passed": quality_pressure_passed,
            "framing_conflict": framing_conflict,
        },
        "seed_cycle_metrics": (
            {
                "base_cagr": seed_base_cagr,
                "base_sharpe": seed_sharpe,
                "base_max_drawdown": seed_mdd,
                "sensitivity_max_drift": seed_drift,
            }
            if active_seed_result
            else None
        ),
        "main_pressure_metrics": (
            {
                "variant_label": str(best_variant.get("variant_label")),
                "base_cagr": recovery_base_cagr,
                "base_sharpe": recovery_sharpe,
                "base_max_drawdown": recovery_mdd,
                "sensitivity_max_drift": recovery_drift,
                "base_cagr_gap_to_main": float(best_variant["base_cagr_gap_to_main"]),
                "cost20_cagr_gap_to_main": float(best_variant["cost20_cagr_gap_to_main"]),
            }
            if best_variant
            else None
        ),
        "lane_delta": (
            {
                "base_cagr_delta": recovery_base_cagr - seed_base_cagr,
                "base_sharpe_delta": recovery_sharpe - seed_sharpe,
                "base_max_drawdown_delta": recovery_mdd - seed_mdd,
                "sensitivity_max_drift_delta": recovery_drift - seed_drift,
            }
            if active_seed_result and best_variant
            else None
        ),
        "verdict": {
            "lane_status": lane_status,
            "keep_active_backup_slot": True,
            "allow_pressure_watch": lane_status == "pressure_watch_eligible",
            "next_step_now": next_step_now,
            "reason": reason,
        },
        "decision_summary": [
            f"Active backup under review is `{ACTIVE_ATTACK_BACKUP_LABEL}`.",
            (
                "Seed-cycle validation and main-pressure evaluation are in conflict, so the backup should be treated as `revalidation_hold` rather than a live pressure-watch candidate."
                if framing_conflict
                else "Seed-cycle and main-pressure lanes are aligned closely enough to keep standard monitoring."
                if lane_status == "pressure_watch_eligible"
                else "Lane alignment is incomplete, so the backup should stay on hold until reconciliation is repaired."
            ),
            f"Current next step is `{next_step_now}`.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    lane = report["lane_alignment"]
    verdict = report["verdict"]
    lines = [
        "# BTC 1d Post-Spike Reopen Seed Pressure Reconciliation",
        "",
        f"- Active backup: `{report['active_backup_label']}`",
        f"- Same seed across lanes: `{lane['same_seed_across_lanes']}`",
        f"- Seed cycle passed: `{lane['seed_cycle_passed']}`",
        f"- Main pressure quality passed: `{lane['main_pressure_quality_passed']}`",
        f"- Framing conflict: `{lane['framing_conflict']}`",
        f"- Lane status: `{verdict['lane_status']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_reopen_seed_pressure_reconciliation_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_reopen_seed_pressure_reconciliation_{stamp}.md"
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
