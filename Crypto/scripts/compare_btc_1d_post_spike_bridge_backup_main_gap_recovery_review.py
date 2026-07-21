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
        ANALYSIS_DIR.glob("btc_1d_post_spike_bridge_backup_main_gap_recovery_batch_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not matches:
        raise FileNotFoundError(
            "No analysis artifact matched pattern: "
            "btc_1d_post_spike_bridge_backup_main_gap_recovery_batch_*.json"
        )
    return matches[0]


def build_report() -> dict:
    batch_path = _latest_batch_path()
    payload = _load_json(batch_path)
    rows = list(payload.get("results", []) or [])
    best_variant = dict(payload.get("best_variant", {}) or {})
    completed_variant_count = len(rows)
    replacement_open_variants = [
        dict(row) for row in rows if bool(row.get("replacement_open_passed", False))
    ]
    clean_variants = [dict(row) for row in rows if bool(row.get("negative_window_clean", False))]
    anchor = next(
        (dict(row) for row in rows if str(row.get("variant_label", "")) == "bridge_28_relief"),
        None,
    )

    main_gap_recovery_found = bool(replacement_open_variants)
    local_axis_completed_failed = completed_variant_count > 0 and not main_gap_recovery_found
    next_step = (
        "open_attack_main_replacement_review"
        if main_gap_recovery_found
        else "open_wider_bridge_family_or_new_axis"
        if completed_variant_count > 0
        else "collect_bridge_main_gap_recovery_evidence"
    )
    reason = (
        "At least one completed bridge variant cleared the negative-window and main-gap replacement thresholds."
        if main_gap_recovery_found
        else "Completed local bridge variants did not reduce the base/cost20 CAGR gaps enough to open main replacement."
        if completed_variant_count > 0
        else "No completed main-gap recovery batch rows were found yet."
    )

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "source_batch_json": str(batch_path),
        "main_gap_recovery_reference": {
            "active_bridge_backup": str(payload.get("active_bridge_backup_label", "bridge_28_relief")),
            "main_base_cagr_reference": float(payload.get("main_base_cagr_reference", 0.0)),
            "main_cost20_cagr_reference": float(payload.get("main_cost20_cagr_reference", 0.0)),
            "completed_variant_count": completed_variant_count,
            "clean_variant_count": len(clean_variants),
        },
        "best_completed_variant": best_variant,
        "anchor_status": anchor,
        "replacement_open_variants": replacement_open_variants,
        "completed_variants": rows,
        "main_gap_recovery_verdict": {
            "main_gap_recovery_found": main_gap_recovery_found,
            "completed_local_gap_axes_failed": local_axis_completed_failed,
            "next_step_now": next_step,
            "reason": reason,
        },
        "decision_summary": [
            (
                f"Completed local bridge main-gap variants: `{completed_variant_count}`."
                if completed_variant_count > 0
                else "No completed local bridge main-gap variants were available to review."
            ),
            (
                f"Best completed variant is `{best_variant['variant_label']}` with base gap "
                f"`{float(best_variant['base_cagr_gap_to_main']):.6f}` and cost20 gap "
                f"`{float(best_variant['cost20_cagr_gap_to_main']):.6f}`."
                if best_variant
                else "Main-gap ranking is unavailable until at least one variant finishes."
            ),
            reason,
        ],
    }


def _render_markdown(report: dict) -> str:
    verdict = report["main_gap_recovery_verdict"]
    reference = report["main_gap_recovery_reference"]
    lines = [
        "# BTC 1d Post-Spike Bridge Backup Main-Gap Recovery Review",
        "",
        f"- Active bridge backup: `{reference['active_bridge_backup']}`",
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
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_bridge_backup_main_gap_recovery_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_bridge_backup_main_gap_recovery_review_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_post_spike_bridge_backup_main_gap_recovery_review_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_post_spike_bridge_backup_main_gap_recovery_review_latest.md"
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
