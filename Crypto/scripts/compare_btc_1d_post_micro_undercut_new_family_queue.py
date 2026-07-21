from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ANALYSIS_DIR = Path("analysis_results")
POST_SHALLOW_BREAKOUT_QUEUE_PATH = ANALYSIS_DIR / "btc_1d_post_shallow_breakout_new_family_queue_20260418T144934Z.json"
MICRO_UNDERCUT_REOPEN_PATH = ANALYSIS_DIR / "btc_1d_micro_undercut_reclaim_continuation_reopen_screen_20260418T152023Z.json"
RECENT_FAMILY_COMPARATIVE_PATH = ANALYSIS_DIR / "btc_1d_recent_family_comparative_screen_20260415T205917Z.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _remaining_candidates(rows: list[dict], excluded_families: set[str], blocked_bucket: str) -> list[dict]:
    candidates = [
        row
        for row in rows
        if row["family"] not in excluded_families
        and row["screen_label"] == "low_alpha_kill"
        and row["completed_trades"] >= 5
        and float(row["max_drawdown"]) <= 0.16
        and row["pattern_bucket"] != blocked_bucket
    ]
    candidates.sort(
        key=lambda row: (
            float(row["max_drawdown"]),
            -float(row["cagr"]),
            -float(row["sharpe"]),
        )
    )
    return candidates


def build_report() -> dict:
    post_shallow = _load_json(POST_SHALLOW_BREAKOUT_QUEUE_PATH)
    micro_reopen = _load_json(MICRO_UNDERCUT_REOPEN_PATH)
    comparative = _load_json(RECENT_FAMILY_COMPARATIVE_PATH)

    exhausted_families = set(post_shallow["post_shallow_breakout_queue_summary"]["exhausted_families"])
    exhausted_families.add(post_shallow["selected_broad_search_seed"]["family"])
    holding_families = set(post_shallow["post_shallow_breakout_queue_summary"]["holding_families"])
    blocked_bucket = post_shallow["selected_broad_search_seed"]["pattern_bucket"]

    remaining = _remaining_candidates(comparative["rows"], exhausted_families | holding_families, blocked_bucket)
    hold = post_shallow["near_candidate_hold"]
    best = micro_reopen["best_variant"]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "post_micro_undercut_queue_summary": {
            "prior_broad_seed": post_shallow["selected_broad_search_seed"]["family"],
            "prior_broad_seed_bucket": blocked_bucket,
            "prior_broad_seed_verdict": micro_reopen["reopen_verdict"]["next_step"],
            "exhausted_families": sorted(exhausted_families),
            "holding_families": sorted(holding_families),
            "remaining_broad_candidates": [
                {
                    "family": row["family"],
                    "variant_label": row["variant_label"],
                    "pattern_bucket": row["pattern_bucket"],
                    "base_cagr": float(row["cagr"]),
                    "base_mdd": float(row["max_drawdown"]),
                    "completed_trades": int(row["completed_trades"]),
                }
                for row in remaining
            ],
            "queue_mode": "hold_only_broad_search_exhausted",
        },
        "exhausted_seed_summary": {
            "family": post_shallow["selected_broad_search_seed"]["family"],
            "best_variant_label": best["variant_label"],
            "stage": best["stage"],
            "decision": best["decision"],
            "cagr": float(best["cagr"]),
            "max_drawdown": float(best["max_drawdown"]),
            "trades": int(best["trades"]),
            "overfitting_flags": list(best.get("overfitting_flags", [])),
            "sensitivity_max_drift": float(best.get("sensitivity_max_drift", 0.0)),
            "reason": micro_reopen["reopen_verdict"]["reason"],
        },
        "near_candidate_hold": hold,
        "broad_search_queue": {
            "selection_logic": [
                "treat micro-undercut as exhausted because it still missed candidate-stage after reopen",
                "keep failed-breakout as the only near-candidate hold because it progressed closest to candidate-stage",
                "recompute the low-alpha broad-search pool after excluding exhausted families, the hold lane, and the last reclaim-grab bucket",
                "stop rotating broad-search seeds when no eligible low-drawdown candidate remains",
            ],
            "next_step_now": "near_candidate_hold_revisit_or_new_search_framework",
            "working_hypothesis": "the broad-search pool is exhausted and the only lane worth keeping alive is the failed-breakout near-candidate hold",
            "success_gate": {
                "remaining_broad_candidates_must_exist": False,
                "hold_lane_is_closest_to_candidate_stage": True,
                "must_avoid_reopening_exhausted_seed": True,
            },
        },
        "queue_verdict": {
            "selected_family": None,
            "selected_reason": "The micro-undercut reopen still failed clean candidate-stage promotion, and no other eligible low-alpha broad-search seed remains after exclusions.",
            "next_step_now": "near_candidate_hold_revisit_or_new_search_framework",
            "advance_condition": "either tighten the failed-breakout hold into candidate-stage evidence or define a fresh research framework instead of rotating the exhausted broad-search pool.",
        },
        "decision_summary": [
            f"Mark `{post_shallow['selected_broad_search_seed']['family']}` as exhausted because reopen still ended at `{best['decision']}` with sensitivity drift `{float(best['sensitivity_max_drift']):.4f}`.",
            f"Keep `{hold['family']}` as the only near-candidate hold because it remains the closest lane to candidate-stage with `{float(hold['cagr']):.4f}` CAGR and `{float(hold['max_drawdown']):.4f}` MDD.",
            "Stop broad-search rotation here because no eligible low-alpha seed remains after excluding exhausted families, the hold lane, and the last reclaim-grab bucket.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    hold = report["near_candidate_hold"]
    exhausted = report["exhausted_seed_summary"]
    lines = [
        "# BTC 1d Post-Micro-Undercut New Family Queue",
        "",
        f"- Queue mode: `{report['post_micro_undercut_queue_summary']['queue_mode']}`",
        f"- Prior broad seed: `{exhausted['family']}`",
        f"- Prior verdict: `{report['post_micro_undercut_queue_summary']['prior_broad_seed_verdict']}`",
        f"- Remaining broad candidates: `{len(report['post_micro_undercut_queue_summary']['remaining_broad_candidates'])}`",
        f"- Near-candidate hold: `{hold['family']}` via `{hold['best_variant_label']}`",
        f"- Hold profile: `{hold['cagr']:.4f}` CAGR / `{hold['max_drawdown']:.4f}` MDD / `{hold['trades']}` trades",
        f"- Next step now: `{report['broad_search_queue']['next_step_now']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_micro_undercut_new_family_queue_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_micro_undercut_new_family_queue_{stamp}.md"
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
