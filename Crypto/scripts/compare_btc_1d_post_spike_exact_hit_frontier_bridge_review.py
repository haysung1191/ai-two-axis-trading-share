from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_post_spike_exact_hit_cost_repair_review import (
    build_report as build_cost_repair_review,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest_json(prefix: str) -> Path:
    matches = sorted(ANALYSIS_DIR.glob(f"{prefix}*.json"))
    if not matches:
        raise FileNotFoundError(f"No analysis result found for prefix: {prefix}")
    return matches[-1]


def build_report() -> dict:
    try:
        cost_review = build_cost_repair_review()
    except ValueError as exc:
        if "No exact-hit candidate found" not in str(exc):
            raise
        return {
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "frontier_bridge_reference": {
                "previous_next_step_now": "frontier_exact_hit_missing",
                "batch_json": None,
                "promoted_backup_cost20_cagr_reference": None,
            },
            "frontier_bridge_best_variant": {
                "variant_label": "",
                "base_cagr": 0.0,
                "base_sharpe": 0.0,
                "base_max_drawdown": 0.0,
                "sensitivity_max_drift": 0.0,
                "cost20_cagr_edge_vs_promoted_backup": 0.0,
                "negative_window_count": 0,
            },
            "frontier_bridge_verdict": {
                "frontier_bridge_found_backup_replacement": False,
                "next_step_now": "open_new_exit_mechanism_axis",
                "reason": (
                    "No exact-hit candidate exists in the current exit tradeoff frontier, "
                    "so frontier-bridge replacement review is blocked before a bridge batch can be valid."
                ),
            },
            "decision_summary": [
                "No exact-hit candidate exists in the current exit tradeoff frontier.",
                "Do not open frontier-bridge backup replacement review from this artifact set.",
                "The next step is to open a new exit mechanism axis rather than retry the same frontier bridge path.",
            ],
        }
    batch_path = _latest_json("btc_1d_post_spike_exact_hit_frontier_bridge_batch_")
    batch = _load_json(batch_path)
    best_variant = dict(batch.get("best_variant", {}) or {})

    gap_closed = float(best_variant.get("cost20_cagr_edge_vs_promoted_backup", -1.0)) >= 0.0
    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "frontier_bridge_reference": {
            "previous_next_step_now": cost_review["cost_repair_verdict"]["next_step_now"],
            "batch_json": str(batch_path),
            "promoted_backup_cost20_cagr_reference": float(batch["promoted_backup_cost20_cagr_reference"]),
        },
        "frontier_bridge_best_variant": {
            "variant_label": str(best_variant.get("variant_label", "")),
            "base_cagr": float(best_variant.get("base_cagr", 0.0)),
            "base_sharpe": float(best_variant.get("base_sharpe", 0.0)),
            "base_max_drawdown": float(best_variant.get("base_max_drawdown", 0.0)),
            "sensitivity_max_drift": float(best_variant.get("sensitivity_max_drift", 0.0)),
            "cost20_cagr_edge_vs_promoted_backup": float(best_variant.get("cost20_cagr_edge_vs_promoted_backup", 0.0)),
            "negative_window_count": int(best_variant.get("negative_window_count", 0)),
        },
        "frontier_bridge_verdict": {
            "frontier_bridge_found_backup_replacement": gap_closed,
            "next_step_now": (
                "open_exact_hit_backup_replacement_review"
                if gap_closed
                else "expand_to_new_post_spike_family_outside_frontier_bridge"
            ),
            "reason": (
                "A bridge variant closed the promoted-backup 20bps gap while staying inside the guardrails."
                if gap_closed
                else "The frontier bridge family still did not close the promoted-backup 20bps gap, so the next search should leave this bridge neighborhood entirely."
            ),
        },
        "decision_summary": [
            f"Best frontier-bridge variant is `{best_variant.get('variant_label', '')}`.",
            (
                f"It closes the promoted-backup 20bps gap with edge `{float(best_variant.get('cost20_cagr_edge_vs_promoted_backup', 0.0)):.6f}`."
                if gap_closed
                else f"It still trails the promoted backup on 20bps CAGR by `{abs(float(best_variant.get('cost20_cagr_edge_vs_promoted_backup', 0.0))):.6f}`."
            ),
            (
                "The next step can reopen backup replacement review."
                if gap_closed
                else "The next step should open a new post-spike family outside the current exact-hit frontier bridge."
            ),
        ],
    }
    return report


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_exact_hit_frontier_bridge_review_{stamp}.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
