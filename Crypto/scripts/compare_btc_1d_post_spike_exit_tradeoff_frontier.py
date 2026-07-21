from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


ANALYSIS_DIR = Path("analysis_results")
TARGET_MAX_GAP = 0.08
TARGET_MAX_DRIFT = 0.20


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest(pattern: str) -> Path:
    matches = sorted(ANALYSIS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No analysis artifact matched pattern: {pattern}")
    return matches[0]


def _latest_optional(pattern: str) -> Path | None:
    matches = sorted(ANALYSIS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        return None
    return matches[0]


def _collect_rows() -> list[dict]:
    sources = [
        ("guardrail_repair", _latest("btc_1d_post_spike_consolidation_breakout_guardrail_repair_batch_*.json")),
        ("cost_robust_cagr", _latest("btc_1d_post_spike_consolidation_breakout_cost_robust_cagr_batch_*.json")),
        ("exit_defense", _latest("btc_1d_post_spike_consolidation_breakout_exit_defense_batch_*.json")),
        ("hold_stop_coupling", _latest("btc_1d_post_spike_consolidation_breakout_hold_stop_coupling_batch_*.json")),
    ]
    optional_source = _latest_optional("btc_1d_post_spike_consolidation_breakout_exit_sequencing_batch_*.json")
    if optional_source is not None:
        sources.append(("exit_sequencing", optional_source))
    optional_entry_shape = _latest_optional("btc_1d_post_spike_consolidation_breakout_entry_shape_batch_*.json")
    if optional_entry_shape is not None:
        sources.append(("entry_shape", optional_entry_shape))
    rows: list[dict] = []
    for source_name, path in sources:
        payload = _load_json(path)
        for row in payload.get("results", []):
            rows.append(
                {
                    "source": source_name,
                    "source_json": str(path),
                    "variant_label": row["variant_label"],
                    "base_cagr": float(row["base_cagr"]),
                    "base_sharpe": float(row["base_sharpe"]),
                    "base_max_drawdown": float(row["base_max_drawdown"]),
                    "sensitivity_max_drift": float(row["sensitivity_max_drift"]),
                    "cagr_gap_to_backup": float(row["cagr_gap_to_backup"]),
                    "negative_window_count": int(row["negative_window_count"]),
                    "idle_window_count": int(row["idle_window_count"]),
                    "rotation_gap_passed": bool(row["rotation_gap_passed"]),
                    "drift_guardrail_passed": bool(row["drift_guardrail_passed"]),
                    "parameters": dict(row["parameters"]),
                }
            )
    return rows


def _pareto_frontier(rows: list[dict]) -> list[dict]:
    frontier: list[dict] = []
    for candidate in rows:
        dominated = False
        for other in rows:
            if other is candidate:
                continue
            weakly_better = (
                other["negative_window_count"] <= candidate["negative_window_count"]
                and other["cagr_gap_to_backup"] <= candidate["cagr_gap_to_backup"]
                and other["sensitivity_max_drift"] <= candidate["sensitivity_max_drift"]
            )
            strictly_better = (
                other["negative_window_count"] < candidate["negative_window_count"]
                or other["cagr_gap_to_backup"] < candidate["cagr_gap_to_backup"]
                or other["sensitivity_max_drift"] < candidate["sensitivity_max_drift"]
            )
            if weakly_better and strictly_better:
                dominated = True
                break
        if not dominated:
            frontier.append(candidate)
    frontier.sort(
        key=lambda item: (
            item["negative_window_count"],
            item["cagr_gap_to_backup"],
            item["sensitivity_max_drift"],
            -item["base_sharpe"],
        )
    )
    return frontier


def build_report() -> dict:
    rows = _collect_rows()
    frontier = _pareto_frontier(rows)
    exact_hits = [
        row for row in frontier
        if row["negative_window_count"] == 0
        and row["cagr_gap_to_backup"] <= TARGET_MAX_GAP
        and row["sensitivity_max_drift"] <= TARGET_MAX_DRIFT
    ]
    best_gap_row = min(frontier, key=lambda item: item["cagr_gap_to_backup"])
    best_drift_row = min(frontier, key=lambda item: item["sensitivity_max_drift"])

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "targets": {
            "max_cagr_gap_to_backup": TARGET_MAX_GAP,
            "max_sensitivity_drift": TARGET_MAX_DRIFT,
            "max_negative_window_count": 0,
        },
        "frontier_summary": {
            "total_rows_scanned": len(rows),
            "frontier_count": len(frontier),
            "exact_hit_found": bool(exact_hits),
            "best_gap_variant": {
                "source": best_gap_row["source"],
                "variant_label": best_gap_row["variant_label"],
                "cagr_gap_to_backup": best_gap_row["cagr_gap_to_backup"],
                "sensitivity_max_drift": best_gap_row["sensitivity_max_drift"],
            },
            "best_drift_variant": {
                "source": best_drift_row["source"],
                "variant_label": best_drift_row["variant_label"],
                "cagr_gap_to_backup": best_drift_row["cagr_gap_to_backup"],
                "sensitivity_max_drift": best_drift_row["sensitivity_max_drift"],
            },
        },
        "pareto_frontier": frontier,
        "frontier_verdict": {
            "exact_hit_found": bool(exact_hits),
            "next_step_now": (
                "promote_exact_hit_into_rotation_review"
                if exact_hits
                else "open_new_exit_mechanism_axis"
            ),
            "reason": (
                "At least one variant now satisfies both the backup-gap and drift guardrails."
                if exact_hits
                else "No scanned variant satisfies both the 20bps gap target and the drift guardrail at the same time; a new exit mechanism axis is required."
            ),
        },
        "decision_summary": [
            (
                f"Best gap variant is `{best_gap_row['variant_label']}` from `{best_gap_row['source']}` "
                f"with gap `{best_gap_row['cagr_gap_to_backup']:.6f}` and drift `{best_gap_row['sensitivity_max_drift']:.6f}`."
            ),
            (
                f"Best drift variant is `{best_drift_row['variant_label']}` from `{best_drift_row['source']}` "
                f"with gap `{best_drift_row['cagr_gap_to_backup']:.6f}` and drift `{best_drift_row['sensitivity_max_drift']:.6f}`."
            ),
            (
                "No exact hit exists on the current frontier, so more tuning on the same exit knobs is unlikely to solve the rotation problem cleanly."
                if not exact_hits
                else "An exact frontier hit exists, so the next cycle can shift from search to promotion review."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    summary = report["frontier_summary"]
    verdict = report["frontier_verdict"]
    lines = [
        "# BTC 1d Post-Spike Exit Tradeoff Frontier",
        "",
        f"- Rows scanned: `{summary['total_rows_scanned']}`",
        f"- Frontier count: `{summary['frontier_count']}`",
        f"- Exact hit found: `{summary['exact_hit_found']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Frontier",
    ]
    for row in report["pareto_frontier"]:
        lines.append(
            f"- `{row['source']}::{row['variant_label']}` gap=`{row['cagr_gap_to_backup']}` drift=`{row['sensitivity_max_drift']}` negative_windows=`{row['negative_window_count']}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_exit_tradeoff_frontier_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_exit_tradeoff_frontier_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
