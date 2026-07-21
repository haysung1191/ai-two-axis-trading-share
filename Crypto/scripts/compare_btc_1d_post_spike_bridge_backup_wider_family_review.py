from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_post_spike_bridge_backup_main_gap_recovery_batch import (
    MAIN_BASE_CAGR_REFERENCE,
    MAIN_BASE_MDD_REFERENCE,
    MAIN_BASE_SHARPE_REFERENCE,
    MAIN_COST20_CAGR_REFERENCE,
    MAIN_DRIFT_REFERENCE,
)
from app.domains.experiments.btc_1d_post_spike_bridge_backup_wider_family_batch import (
    WIDER_FAMILY_VARIANTS,
)


ANALYSIS_DIR = Path("analysis_results")
BRIDGE_PREFIX = "post_spike_bridge_backup::"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _diagnostic_snapshot(path: Path) -> tuple[str, str, dict] | None:
    payload = _load_json(path)
    config = dict(payload.get("config", {}) or {})
    candidate_label = str(config.get("candidate_label", ""))
    if not candidate_label.startswith(BRIDGE_PREFIX):
        return None
    parts = candidate_label.split("::")
    if len(parts) != 3:
        return None
    variant_label = parts[1]
    lane = parts[2]
    allowed_labels = {str(variant["label"]) for variant in WIDER_FAMILY_VARIANTS}
    if variant_label not in allowed_labels or lane not in {"base", "cost20"}:
        return None

    walk_forward = list((payload.get("overfitting", {}) or {}).get("walk_forward", []) or [])
    negative_windows = [
        int(window.get("window", 0))
        for window in walk_forward
        if float((window.get("metrics", {}) or {}).get("sharpe", 0.0)) < 0.0
        or float((window.get("metrics", {}) or {}).get("cagr", 0.0)) < 0.0
    ]
    idle_windows = [
        int(window.get("window", 0))
        for window in walk_forward
        if int((window.get("metrics", {}) or {}).get("trades", 0)) == 0
    ]
    return (
        variant_label,
        lane,
        {
            "analysis_result_json": str(path),
            "cagr": float(payload["base_metrics"]["cagr"]),
            "sharpe": float(payload["base_metrics"]["sharpe"]),
            "max_drawdown": float(payload["base_metrics"]["max_drawdown"]),
            "sensitivity_max_drift": float(payload["overfitting"]["sensitivity_max_drift"]),
            "negative_windows": negative_windows,
            "idle_windows": idle_windows,
            "negative_window_count": len(negative_windows),
            "idle_window_count": len(idle_windows),
            "last_write_time_utc": datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat(),
        },
    )


def _collect_variant_snapshots() -> tuple[list[dict], list[dict]]:
    grouped: dict[str, dict[str, dict]] = {}
    for path in sorted(ANALYSIS_DIR.glob("btc_1d_walk_forward_diagnostic_*.json"), key=lambda p: p.stat().st_mtime):
        snapshot = _diagnostic_snapshot(path)
        if not snapshot:
            continue
        variant_label, lane, row = snapshot
        grouped.setdefault(variant_label, {})[lane] = row

    completed: list[dict] = []
    pending: list[dict] = []
    for variant in WIDER_FAMILY_VARIANTS:
        variant_label = str(variant["label"])
        lanes = grouped.get(variant_label, {})
        missing_lanes = [lane for lane in ("base", "cost20") if lane not in lanes]
        if missing_lanes:
            pending.append(
                {
                    "variant_label": variant_label,
                    "available_lanes": sorted(lanes),
                    "missing_lanes": missing_lanes,
                }
            )
            continue

        base = lanes["base"]
        cost20 = lanes["cost20"]
        base_cagr = float(base["cagr"])
        cost20_cagr = float(cost20["cagr"])
        base_mdd = float(base["max_drawdown"])
        base_sharpe = float(base["sharpe"])
        max_drift = max(float(base["sensitivity_max_drift"]), float(cost20["sensitivity_max_drift"]))
        base_gap = MAIN_BASE_CAGR_REFERENCE - base_cagr
        cost20_gap = MAIN_COST20_CAGR_REFERENCE - cost20_cagr
        negative_window_count = int(base["negative_window_count"]) + int(cost20["negative_window_count"])
        completed.append(
            {
                "variant_label": variant_label,
                "base_cagr": base_cagr,
                "base_sharpe": base_sharpe,
                "base_max_drawdown": base_mdd,
                "base_negative_windows": list(base["negative_windows"]),
                "base_idle_windows": list(base["idle_windows"]),
                "base_negative_window_count": int(base["negative_window_count"]),
                "cost20_cagr": cost20_cagr,
                "cost20_sharpe": float(cost20["sharpe"]),
                "cost20_max_drawdown": float(cost20["max_drawdown"]),
                "cost20_negative_windows": list(cost20["negative_windows"]),
                "cost20_idle_windows": list(cost20["idle_windows"]),
                "cost20_negative_window_count": int(cost20["negative_window_count"]),
                "max_sensitivity_drift": max_drift,
                "base_cagr_gap_to_main": base_gap,
                "cost20_cagr_gap_to_main": cost20_gap,
                "sharpe_edge_vs_main": base_sharpe - MAIN_BASE_SHARPE_REFERENCE,
                "mdd_improvement_vs_main": MAIN_BASE_MDD_REFERENCE - base_mdd,
                "drift_improvement_vs_main": MAIN_DRIFT_REFERENCE - max_drift,
                "negative_window_clean": negative_window_count == 0,
                "replacement_open_passed": (
                    negative_window_count == 0
                    and base_gap <= 0.04
                    and cost20_gap <= 0.06
                    and base_sharpe >= MAIN_BASE_SHARPE_REFERENCE + 0.15
                    and base_mdd <= MAIN_BASE_MDD_REFERENCE - 0.05
                    and max_drift <= 0.15
                ),
                "source_pair": {
                    "base": str(base["analysis_result_json"]),
                    "cost20": str(cost20["analysis_result_json"]),
                },
            }
        )

    completed.sort(
        key=lambda item: (
            not bool(item["negative_window_clean"]),
            not bool(item["replacement_open_passed"]),
            float(item["base_cagr_gap_to_main"]),
            float(item["cost20_cagr_gap_to_main"]),
            float(item["max_sensitivity_drift"]),
            -float(item["base_sharpe"]),
        )
    )
    return completed, pending


def build_report() -> dict:
    completed, pending = _collect_variant_snapshots()
    best_variant = completed[0] if completed else {}
    replacement_open_variants = [
        dict(row) for row in completed if bool(row.get("replacement_open_passed", False))
    ]
    expected_count = len(WIDER_FAMILY_VARIANTS)
    complete = len(completed) == expected_count
    recovery_found = bool(replacement_open_variants)
    next_step = (
        "open_attack_main_replacement_review"
        if recovery_found
        else "keep_wider_family_batch_running"
        if not complete
        else "close_wider_bridge_family_and_open_new_axis"
    )
    reason = (
        "A completed wider-family variant cleared the main-replacement thresholds."
        if recovery_found
        else "The wider-family batch is still in progress; keep collecting base/cost20 pairs."
        if not complete
        else "Completed wider-family variants still did not clear the main-replacement thresholds."
    )
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "wider_family_reference": {
            "expected_variant_count": expected_count,
            "completed_variant_count": len(completed),
            "pending_variant_count": len(pending),
            "active_bridge_backup": "bridge_28_relief",
        },
        "best_completed_variant": best_variant,
        "replacement_open_variants": replacement_open_variants,
        "completed_variants": completed,
        "pending_variants": pending,
        "wider_family_verdict": {
            "wider_family_complete": complete,
            "main_gap_recovery_found": recovery_found,
            "next_step_now": next_step,
            "reason": reason,
        },
        "decision_summary": [
            f"Completed wider-family variants: `{len(completed)}/{expected_count}`.",
            (
                f"Best completed variant is `{best_variant['variant_label']}` with base gap "
                f"`{float(best_variant['base_cagr_gap_to_main']):.6f}` and cost20 gap "
                f"`{float(best_variant['cost20_cagr_gap_to_main']):.6f}`."
                if best_variant
                else "No completed wider-family base/cost20 pair is available yet."
            ),
            reason,
        ],
    }


def _render_markdown(report: dict) -> str:
    verdict = report["wider_family_verdict"]
    reference = report["wider_family_reference"]
    lines = [
        "# BTC 1d Post-Spike Bridge Backup Wider-Family Review",
        "",
        f"- Completed variants: `{reference['completed_variant_count']}/{reference['expected_variant_count']}`",
        f"- Pending variants: `{reference['pending_variant_count']}`",
        f"- Wider-family complete: `{verdict['wider_family_complete']}`",
        f"- Main-gap recovery found: `{verdict['main_gap_recovery_found']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Completed Variants",
    ]
    for row in report["completed_variants"]:
        lines.append(
            f"- `{row['variant_label']}` | replacement_open=`{row['replacement_open_passed']}` "
            f"| clean=`{row['negative_window_clean']}` "
            f"| base_gap=`{float(row['base_cagr_gap_to_main']):.6f}` "
            f"| cost20_gap=`{float(row['cost20_cagr_gap_to_main']):.6f}` "
            f"| drift=`{float(row['max_sensitivity_drift']):.6f}`"
        )
    lines.append("")
    lines.append("## Pending Variants")
    for row in report["pending_variants"]:
        lines.append(
            f"- `{row['variant_label']}` | available=`{row['available_lanes']}` "
            f"| missing=`{row['missing_lanes']}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_bridge_backup_wider_family_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_bridge_backup_wider_family_review_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_post_spike_bridge_backup_wider_family_review_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_post_spike_bridge_backup_wider_family_review_latest.md"
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
