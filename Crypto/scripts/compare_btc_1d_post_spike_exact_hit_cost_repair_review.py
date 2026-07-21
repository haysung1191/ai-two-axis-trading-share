from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_post_spike_exact_hit_attack_stack_review import (
    build_report as build_attack_stack_review,
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
    stack_review = build_attack_stack_review()
    batch_path = _latest_json("btc_1d_post_spike_exact_hit_cost_repair_batch_")
    batch = _load_json(batch_path)
    rows = list(batch.get("results", []) or [])
    best_variant = dict(batch.get("best_variant", {}) or {})
    anchor = next((row for row in rows if str(row.get("variant_label")) == "exact_hit_anchor"), best_variant)

    best_label = str(best_variant.get("variant_label", ""))
    anchor_label = str(anchor.get("variant_label", "exact_hit_anchor"))
    gap_closed = float(best_variant.get("cost20_cagr_edge_vs_promoted_backup", -1.0)) >= 0.0
    anchor_kept = best_label == anchor_label

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "cost_repair_reference": {
            "exact_hit_candidate": batch["exact_hit_candidate_label"],
            "promoted_backup_cost20_cagr_reference": float(batch["promoted_backup_cost20_cagr_reference"]),
            "batch_json": str(batch_path),
            "attack_stack_next_step_before_repair": stack_review["exact_hit_stack_verdict"]["next_step_now"],
        },
        "cost_repair_best_variant": {
            "variant_label": best_label,
            "base_cagr": float(best_variant.get("base_cagr", 0.0)),
            "base_sharpe": float(best_variant.get("base_sharpe", 0.0)),
            "base_max_drawdown": float(best_variant.get("base_max_drawdown", 0.0)),
            "sensitivity_max_drift": float(best_variant.get("sensitivity_max_drift", 0.0)),
            "cost20_cagr_edge_vs_promoted_backup": float(best_variant.get("cost20_cagr_edge_vs_promoted_backup", 0.0)),
            "negative_window_count": int(best_variant.get("negative_window_count", 0)),
        },
        "cost_repair_anchor_comparison": {
            "anchor_variant_label": anchor_label,
            "anchor_cost20_cagr_edge_vs_promoted_backup": float(anchor.get("cost20_cagr_edge_vs_promoted_backup", 0.0)),
            "best_minus_anchor_cost20_cagr_edge": float(best_variant.get("cost20_cagr_edge_vs_promoted_backup", 0.0))
            - float(anchor.get("cost20_cagr_edge_vs_promoted_backup", 0.0)),
            "anchor_kept_best_slot": anchor_kept,
            "gap_closed_against_promoted_backup": gap_closed,
        },
        "cost_repair_verdict": {
            "cost_repair_axis_closed": anchor_kept and not gap_closed,
            "promote_exact_hit_to_backup_now": bool(gap_closed),
            "keep_exact_hit_as_monitoring_candidate": not bool(gap_closed),
            "next_step_now": (
                "open_exact_hit_backup_replacement_review"
                if gap_closed
                else "search_new_exact_hit_family_or_non_cost_axes"
            ),
            "reason": (
                "A cost-repair variant closed the 20bps gap, so the exact-hit candidate can reopen backup replacement review."
                if gap_closed
                else "The targeted cost-repair variants did not beat the exact-hit anchor or close the promoted-backup 20bps gap, so this local repair axis is now closed."
            ),
        },
        "decision_summary": [
            (
                f"Best cost-repair variant is `{best_label}`, and it {'does' if gap_closed else 'does not'} close the 20bps gap versus the promoted backup."
            ),
            (
                f"The anchor stayed best with cost20 edge `{float(anchor.get('cost20_cagr_edge_vs_promoted_backup', 0.0)):.6f}`, so stop/hold/volume micro-repairs did not improve the promoted-backup comparison."
                if anchor_kept
                else f"A non-anchor repair variant `{best_label}` improved the local cost-retention ranking."
            ),
            (
                "The next search should leave this local cost-repair neighborhood and open a new family or non-cost axis."
                if not gap_closed
                else "The next step can return to backup replacement review because the cost-retention blocker is cleared."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    best = report["cost_repair_best_variant"]
    verdict = report["cost_repair_verdict"]
    lines = [
        "# BTC 1d Post-Spike Exact-Hit Cost Repair Review",
        "",
        f"- Exact-hit candidate: `{report['cost_repair_reference']['exact_hit_candidate']}`",
        f"- Best variant: `{best['variant_label']}`",
        f"- Cost repair axis closed: `{verdict['cost_repair_axis_closed']}`",
        f"- Promote exact hit to backup now: `{verdict['promote_exact_hit_to_backup_now']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        "",
        "## Best Variant",
        f"- CAGR=`{best['base_cagr']}` Sharpe=`{best['base_sharpe']}` MDD=`{best['base_max_drawdown']}` drift=`{best['sensitivity_max_drift']}`",
        f"- Cost20 CAGR edge vs promoted backup: `{best['cost20_cagr_edge_vs_promoted_backup']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_exact_hit_cost_repair_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_exact_hit_cost_repair_review_{stamp}.md"
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
