from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest_exit_batch_path() -> Path:
    matches = sorted(
        ANALYSIS_DIR.glob("btc_1d_trend_dip_reversal_breakout_exit_compression_batch_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not matches:
        raise FileNotFoundError("No trend dip exit compression batch artifact found.")
    return matches[0]


def _latest_validation_path(artifact_label: str) -> Path | None:
    matches = sorted(
        ANALYSIS_DIR.glob(f"btc_1d_trend_dip_reversal_breakout_*_{artifact_label}_paper_validation_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def build_report() -> dict:
    batch_path = _latest_exit_batch_path()
    batch = _load_json(batch_path)
    survivors = [row for row in batch.get("results", []) if str(row.get("decision")) == "KEEP"]

    reviewed_rows: list[dict] = []
    for row in survivors:
        artifact_label = str(row["variant_label"])
        validation_path = _latest_validation_path(artifact_label)
        if validation_path is None:
            reviewed_rows.append(
                {
                    "artifact_label": artifact_label,
                    "strategy_name": str(row["strategy_name"]),
                    "validation_available": False,
                }
            )
            continue
        validation = _load_json(validation_path)
        decision = dict(validation.get("decision_record", {}) or {})
        metrics = dict(decision.get("key_metrics", {}) or {})
        reviewed_rows.append(
            {
                "artifact_label": artifact_label,
                "strategy_name": str(row["strategy_name"]),
                "validation_available": True,
                "decision": str(decision.get("decision", "")),
                "failed_gates": list(decision.get("failed_gates", []) or []),
                "cagr": float(metrics.get("cagr", 0.0)),
                "max_drawdown": float(metrics.get("max_drawdown", 0.0)),
                "sharpe": float(metrics.get("sharpe", 0.0)),
                "analysis_result_json": str(validation_path),
            }
        )

    available_rows = [row for row in reviewed_rows if bool(row.get("validation_available"))]
    passing_rows = [row for row in available_rows if str(row.get("decision")) == "PASS"]
    available_rows.sort(
        key=lambda row: (
            str(row.get("decision")) != "PASS",
            float(row.get("max_drawdown", 9.0)),
            -float(row.get("cagr", 0.0)),
            -float(row.get("sharpe", 0.0)),
        )
    )
    best_reviewed = available_rows[0] if available_rows else {}

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "validation_reference": {
            "exit_compression_batch_json": str(batch_path),
            "survivor_count": len(survivors),
            "validation_count": len(available_rows),
        },
        "best_reviewed_candidate": best_reviewed,
        "reviewed_candidates": reviewed_rows,
        "validation_review_verdict": {
            "has_passing_candidate": bool(passing_rows),
            "all_reviewed_candidates_failed": bool(available_rows) and not bool(passing_rows),
            "next_step_now": (
                "candidate_validation_passed_open_walk_forward"
                if passing_rows
                else "run_exit_symmetry_batch"
                if available_rows
                else "collect_candidate_validation_results"
            ),
            "reason": (
                "At least one exit-compression survivor passed candidate validation, so the trend-dip lane can advance to walk-forward."
                if passing_rows
                else "All reviewed exit-compression survivors failed candidate validation, so the primary lane should stay in mutation space and run exit symmetry next."
                if available_rows
                else "Candidate validation results are not available yet for the latest exit-compression survivors."
            ),
        },
        "decision_summary": [
            (
                f"Reviewed `{len(available_rows)}` candidate validations from the latest exit-compression survivor set."
                if available_rows
                else "No candidate validation artifacts were available to review yet."
            ),
            (
                f"Best reviewed candidate is `{best_reviewed['artifact_label']}` with decision `{best_reviewed['decision']}` and failed gates `{best_reviewed['failed_gates']}`."
                if best_reviewed
                else "No reviewed candidate is available yet."
            ),
            (
                "All reviewed compression survivors failed, so the next primary step should be exit symmetry."
                if available_rows and not passing_rows
                else "A reviewed candidate passed, so the next primary step should be walk-forward."
                if passing_rows
                else "Collect the candidate validation results before moving the queue."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    verdict = report["validation_review_verdict"]
    lines = [
        "# BTC 1d Trend Dip Candidate Validation Review",
        "",
        f"- Survivor count: `{report['validation_reference']['survivor_count']}`",
        f"- Validation count: `{report['validation_reference']['validation_count']}`",
        f"- Has passing candidate: `{verdict['has_passing_candidate']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Reviewed Candidates",
    ]
    for row in report["reviewed_candidates"]:
        if not row.get("validation_available"):
            lines.append(f"- `{row['artifact_label']}` | validation_available=`False`")
            continue
        lines.append(
            f"- `{row['artifact_label']}` | decision=`{row['decision']}` | failed_gates=`{row['failed_gates']}` "
            f"| cagr=`{row['cagr']}` | mdd=`{row['max_drawdown']}` | sharpe=`{row['sharpe']}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_trend_dip_candidate_validation_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_trend_dip_candidate_validation_review_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_trend_dip_candidate_validation_review_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_trend_dip_candidate_validation_review_latest.md"
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
