from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


ANALYSIS_DIR = Path("analysis_results")
COMMON_RULES_LATEST = Path("analysis_results/btc_1d_attack_common_rules_latest.json")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _collect_latest_family_rows() -> list[dict]:
    latest_by_family: dict[str, tuple[float, dict]] = {}
    for path in sorted(ANALYSIS_DIR.glob("btc_1d_attack_return_family_scout_batch_*.json")):
        payload = _load_json(path)
        mtime = path.stat().st_mtime
        for row in list(payload.get("results", []) or []):
            family = str(row.get("family", ""))
            if not family:
                continue
            existing = latest_by_family.get(family)
            if existing is None or mtime >= existing[0]:
                enriched = dict(row)
                enriched["source_batch_json"] = str(path)
                latest_by_family[family] = (mtime, enriched)
    rows = [row for _, row in latest_by_family.values()]
    rows.sort(
        key=lambda item: (
            not bool(item.get("negative_window_clean", False)),
            not bool(item.get("replacement_open_passed", False)),
            float(item.get("base_cagr_gap_to_main", 999.0)),
            float(item.get("cost20_cagr_gap_to_main", 999.0)),
            float(item.get("max_sensitivity_drift", 999.0)),
            -float(item.get("base_sharpe", 0.0)),
        )
    )
    return rows


def _common_rule_leader_families() -> list[str]:
    if not COMMON_RULES_LATEST.exists():
        return []
    payload = _load_json(COMMON_RULES_LATEST)
    families = [
        str(row.get("family", ""))
        for row in list(payload.get("leaders", []) or [])
        if str(row.get("family", ""))
    ]
    return sorted(set(families))


def build_report() -> dict:
    rows = _collect_latest_family_rows()
    best = rows[0] if rows else {}
    replacement_open = [row for row in rows if bool(row.get("replacement_open_passed", False))]
    closed = [row for row in rows if not bool(row.get("replacement_open_passed", False))]
    common_rule_leaders = _common_rule_leader_families()
    completed_families = sorted({str(row.get("family", "")) for row in rows if str(row.get("family", ""))})
    unchecked_common_rule_leaders = [
        family for family in common_rule_leaders if family not in set(completed_families)
    ]
    next_step = (
        "open_attack_main_replacement_review"
        if replacement_open
        else "expand_return_family_scout_with_unchecked_leaders"
        if unchecked_common_rule_leaders
        else "close_common_rule_return_family_scout_and_open_new_return_family_axis"
        if rows and common_rule_leaders
        else "expand_return_family_scout_with_unchecked_leaders"
        if rows
        else "run_return_family_scout_batch"
    )
    reason = (
        "At least one return-family scout cleared replacement-open thresholds."
        if replacement_open
        else "All common-rule leader families were scouted, and none cleared replacement-open thresholds."
        if rows and common_rule_leaders and not unchecked_common_rule_leaders
        else "Some common-rule leader families have not been scouted yet."
        if unchecked_common_rule_leaders
        else "Completed return-family scouts did not clear negative-window, quality, and main-gap thresholds."
        if rows
        else "No completed return-family scout rows were found."
    )
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "return_family_scout_reference": {
            "completed_family_count": len(rows),
            "closed_family_count": len(closed),
            "replacement_open_count": len(replacement_open),
            "common_rule_leader_count": len(common_rule_leaders),
            "unchecked_common_rule_leader_count": len(unchecked_common_rule_leaders),
        },
        "completed_family_names": completed_families,
        "unchecked_common_rule_leaders": unchecked_common_rule_leaders,
        "best_completed_family": best,
        "replacement_open_families": replacement_open,
        "completed_families": rows,
        "return_family_scout_verdict": {
            "main_gap_recovery_found": bool(replacement_open),
            "next_step_now": next_step,
            "reason": reason,
        },
        "decision_summary": [
            f"Completed return-family scouts: `{len(rows)}`.",
            (
                f"Best completed family is `{best['family']}` / `{best['variant_label']}` with base gap "
                f"`{float(best['base_cagr_gap_to_main']):.6f}` and cost20 gap "
                f"`{float(best['cost20_cagr_gap_to_main']):.6f}`."
                if best
                else "No completed return-family scout is available."
            ),
            reason,
        ],
    }


def _render_markdown(report: dict) -> str:
    verdict = report["return_family_scout_verdict"]
    reference = report["return_family_scout_reference"]
    lines = [
        "# BTC 1d Attack Return-Family Scout Review",
        "",
        f"- Completed families: `{reference['completed_family_count']}`",
        f"- Common-rule leader families: `{reference['common_rule_leader_count']}`",
        f"- Unchecked common-rule leaders: `{reference['unchecked_common_rule_leader_count']}`",
        f"- Replacement-open count: `{reference['replacement_open_count']}`",
        f"- Main-gap recovery found: `{verdict['main_gap_recovery_found']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Completed Families",
    ]
    for row in report["completed_families"]:
        lines.append(
            f"- `{row['family']}` / `{row['variant_label']}` | replacement_open=`{row['replacement_open_passed']}` "
            f"| clean=`{row['negative_window_clean']}` "
            f"| base_gap=`{float(row['base_cagr_gap_to_main']):.6f}` "
            f"| cost20_gap=`{float(row['cost20_cagr_gap_to_main']):.6f}` "
            f"| mdd_improvement=`{float(row['mdd_improvement_vs_main']):.6f}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_return_family_scout_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_return_family_scout_review_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_attack_return_family_scout_review_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_attack_return_family_scout_review_latest.md"
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
