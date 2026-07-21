from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_post_spike_bridge_backup_negative_window_repair_batch import (
    ACTIVE_BACKUP_BASE_CAGR_REFERENCE,
    ACTIVE_BACKUP_COST20_CAGR_REFERENCE,
)


ANALYSIS_DIR = Path("analysis_results")
BRIDGE_PREFIX = "post_spike_bridge_backup::"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _collect_latest_variant_snapshots() -> list[dict]:
    grouped: dict[str, dict[str, dict]] = {}
    for path in sorted(ANALYSIS_DIR.glob("btc_1d_walk_forward_diagnostic_*.json"), key=lambda p: p.stat().st_mtime):
        payload = _load_json(path)
        config = dict(payload.get("config", {}) or {})
        candidate_label = str(config.get("candidate_label", ""))
        if not candidate_label.startswith(BRIDGE_PREFIX):
            continue
        parts = candidate_label.split("::")
        if len(parts) != 3:
            continue
        variant_label = parts[1]
        lane = parts[2]
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
        grouped.setdefault(variant_label, {})[lane] = {
            "analysis_result_json": str(path),
            "cagr": float(payload["base_metrics"]["cagr"]),
            "sharpe": float(payload["base_metrics"]["sharpe"]),
            "max_drawdown": float(payload["base_metrics"]["max_drawdown"]),
            "sensitivity_max_drift": float(payload["overfitting"]["sensitivity_max_drift"]),
            "negative_windows": negative_windows,
            "idle_windows": idle_windows,
            "negative_window_count": len(negative_windows),
            "idle_window_count": len(idle_windows),
        }

    rows: list[dict] = []
    for variant_label, lanes in grouped.items():
        if "base" not in lanes or "cost20" not in lanes:
            continue
        base = lanes["base"]
        cost20 = lanes["cost20"]
        rows.append(
            {
                "variant_label": variant_label,
                "base_cagr": float(base["cagr"]),
                "base_sharpe": float(base["sharpe"]),
                "base_max_drawdown": float(base["max_drawdown"]),
                "base_negative_windows": list(base["negative_windows"]),
                "base_idle_windows": list(base["idle_windows"]),
                "base_negative_window_count": int(base["negative_window_count"]),
                "cost20_cagr": float(cost20["cagr"]),
                "cost20_sharpe": float(cost20["sharpe"]),
                "cost20_max_drawdown": float(cost20["max_drawdown"]),
                "cost20_negative_windows": list(cost20["negative_windows"]),
                "cost20_idle_windows": list(cost20["idle_windows"]),
                "cost20_negative_window_count": int(cost20["negative_window_count"]),
                "max_sensitivity_drift": max(
                    float(base["sensitivity_max_drift"]),
                    float(cost20["sensitivity_max_drift"]),
                ),
                "base_cagr_gap_to_active_backup": ACTIVE_BACKUP_BASE_CAGR_REFERENCE - float(base["cagr"]),
                "cost20_cagr_gap_to_active_backup": ACTIVE_BACKUP_COST20_CAGR_REFERENCE - float(cost20["cagr"]),
                "negative_window_repair_passed": int(base["negative_window_count"]) == 0
                and int(cost20["negative_window_count"]) == 0,
                "source_pair": {
                    "base": str(base["analysis_result_json"]),
                    "cost20": str(cost20["analysis_result_json"]),
                },
            }
        )

    rows.sort(
        key=lambda item: (
            not bool(item["negative_window_repair_passed"]),
            int(item["base_negative_window_count"]) + int(item["cost20_negative_window_count"]),
            abs(float(item["cost20_cagr_gap_to_active_backup"])),
            abs(float(item["base_cagr_gap_to_active_backup"])),
            float(item["max_sensitivity_drift"]),
        )
    )
    return rows


def build_report() -> dict:
    rows = _collect_latest_variant_snapshots()
    best_variant = rows[0] if rows else {}
    completed_variant_count = len(rows)
    completed_repairs = [row for row in rows if bool(row["negative_window_repair_passed"])]
    anchor = next((row for row in rows if str(row["variant_label"]) == "bridge_28_relief"), None)

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "repair_review_reference": {
            "active_bridge_backup": "bridge_28_relief",
            "active_bridge_backup_base_cagr_reference": ACTIVE_BACKUP_BASE_CAGR_REFERENCE,
            "active_bridge_backup_cost20_cagr_reference": ACTIVE_BACKUP_COST20_CAGR_REFERENCE,
            "completed_variant_count": completed_variant_count,
        },
        "best_completed_variant": best_variant,
        "anchor_status": anchor,
        "completed_variants": rows,
        "repair_review_verdict": {
            "negative_window_repair_found": bool(completed_repairs),
            "completed_local_repair_axes_failed": not bool(completed_repairs) and completed_variant_count > 0,
            "next_step_now": (
                "promote_repaired_bridge_backup_candidate"
                if completed_repairs
                else "close_local_bridge_window_repairs_and_open_new_axis"
                if completed_variant_count > 0
                else "collect_bridge_backup_repair_evidence"
            ),
            "reason": (
                "A completed local repair cleared the negative walk-forward window in both base and cost20 validation."
                if completed_repairs
                else "Completed local bridge repairs kept the same negative walk-forward window while degrading return, so this local repair neighborhood should be closed."
                if completed_variant_count > 0
                else "No completed dual-validation repair pairs were found yet."
            ),
        },
        "decision_summary": [
            (
                f"Completed local bridge repair variants: `{completed_variant_count}`."
                if completed_variant_count > 0
                else "No completed local bridge repair variants were available to review."
            ),
            (
                f"Best completed variant is `{best_variant['variant_label']}`, but repair_passed=`{best_variant['negative_window_repair_passed']}` and cost20 gap to active backup is `{best_variant['cost20_cagr_gap_to_active_backup']:.6f}`."
                if best_variant
                else "Repair ranking is unavailable until at least one variant finishes both base and cost20 validation."
            ),
            (
                "Completed hold/buffer/depth/volume/spike-lookback repairs all preserved negative window 5, so the next search should leave this local bridge-repair neighborhood."
                if completed_variant_count > 0 and not completed_repairs
                else "A completed repair cleared the negative window, so the next step is promotion review."
                if completed_repairs
                else "Keep collecting completed repair evidence."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    verdict = report["repair_review_verdict"]
    lines = [
        "# BTC 1d Post-Spike Bridge Backup Negative-Window Repair Review",
        "",
        f"- Active bridge backup: `{report['repair_review_reference']['active_bridge_backup']}`",
        f"- Completed variants: `{report['repair_review_reference']['completed_variant_count']}`",
        f"- Negative-window repair found: `{verdict['negative_window_repair_found']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Completed Variants",
    ]
    for row in report["completed_variants"]:
        lines.append(
            f"- `{row['variant_label']}` | repair_passed=`{row['negative_window_repair_passed']}` "
            f"| base_neg=`{row['base_negative_windows']}` | cost20_neg=`{row['cost20_negative_windows']}` "
            f"| base_gap=`{row['base_cagr_gap_to_active_backup']:.6f}` | cost20_gap=`{row['cost20_cagr_gap_to_active_backup']:.6f}` "
            f"| drift=`{row['max_sensitivity_drift']:.6f}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_bridge_backup_negative_window_repair_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_bridge_backup_negative_window_repair_review_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_post_spike_bridge_backup_negative_window_repair_review_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_post_spike_bridge_backup_negative_window_repair_review_latest.md"
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
