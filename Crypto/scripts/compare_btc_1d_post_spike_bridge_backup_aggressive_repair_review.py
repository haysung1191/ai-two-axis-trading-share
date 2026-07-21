from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest_batch_path() -> Path:
    matches = sorted(
        ANALYSIS_DIR.glob("btc_1d_post_spike_bridge_backup_aggressive_repair_batch_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not matches:
        raise FileNotFoundError(
            "No analysis artifact matched pattern: "
            "btc_1d_post_spike_bridge_backup_aggressive_repair_batch_*.json"
        )
    return matches[0]


def build_report() -> dict:
    batch_path = _latest_batch_path()
    payload = _load_json(batch_path)
    rows = list(payload.get("results", []) or [])
    best_variant = dict(payload.get("best_variant", {}) or {})
    replacement_open_variants = [
        dict(row) for row in rows if bool(row.get("replacement_open_passed", False))
    ]
    clean_variants = [dict(row) for row in rows if bool(row.get("negative_window_clean", False))]
    recovery_found = bool(replacement_open_variants)
    next_step = (
        "open_attack_main_replacement_review"
        if recovery_found
        else "close_aggressive_repair_axis_and_open_new_return_family"
        if rows
        else "collect_aggressive_repair_evidence"
    )
    reason = (
        "An aggressive repair seed cleared the main-replacement thresholds."
        if recovery_found
        else "Completed aggressive repair seeds still failed negative-window cleanliness and main-gap thresholds."
        if rows
        else "No completed aggressive repair variants were found yet."
    )
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "source_batch_json": str(batch_path),
        "aggressive_repair_reference": {
            "completed_variant_count": len(rows),
            "clean_variant_count": len(clean_variants),
            "main_base_cagr_reference": float(payload.get("main_base_cagr_reference", 0.0)),
            "main_cost20_cagr_reference": float(payload.get("main_cost20_cagr_reference", 0.0)),
        },
        "best_completed_variant": best_variant,
        "replacement_open_variants": replacement_open_variants,
        "completed_variants": rows,
        "aggressive_repair_verdict": {
            "main_gap_recovery_found": recovery_found,
            "completed_axis_failed": bool(rows) and not recovery_found,
            "next_step_now": next_step,
            "reason": reason,
        },
        "decision_summary": [
            f"Completed aggressive repair variants: `{len(rows)}`.",
            (
                f"Best completed variant is `{best_variant['variant_label']}` with base gap "
                f"`{float(best_variant['base_cagr_gap_to_main']):.6f}` and cost20 gap "
                f"`{float(best_variant['cost20_cagr_gap_to_main']):.6f}`."
                if best_variant
                else "No completed aggressive repair variant is available."
            ),
            reason,
        ],
    }


def _render_markdown(report: dict) -> str:
    verdict = report["aggressive_repair_verdict"]
    reference = report["aggressive_repair_reference"]
    lines = [
        "# BTC 1d Post-Spike Bridge Backup Aggressive-Repair Review",
        "",
        f"- Completed variants: `{reference['completed_variant_count']}`",
        f"- Clean variants: `{reference['clean_variant_count']}`",
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
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_bridge_backup_aggressive_repair_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_bridge_backup_aggressive_repair_review_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_post_spike_bridge_backup_aggressive_repair_review_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_post_spike_bridge_backup_aggressive_repair_review_latest.md"
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
