from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ANALYSIS_DIR = Path("analysis_results")
POST_BRIEF_RESET_QUEUE_PATH = ANALYSIS_DIR / "btc_1d_post_brief_reset_new_family_queue_20260418T143715Z.json"
RECLAIM_SHELF_REOPEN_PATH = ANALYSIS_DIR / "btc_1d_reclaim_shelf_acceleration_reopen_screen_20260418T144305Z.json"
RECENT_FAMILY_COMPARATIVE_PATH = ANALYSIS_DIR / "btc_1d_recent_family_comparative_screen_20260415T205917Z.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _choose_seed(rows: list[dict], exhausted_families: set[str], holding_families: set[str], blocked_bucket: str) -> dict:
    candidates = [
        row
        for row in rows
        if row["family"] not in exhausted_families
        and row["family"] not in holding_families
        and row["screen_label"] == "low_alpha_kill"
        and row["completed_trades"] >= 5
        and float(row["max_drawdown"]) <= 0.16
        and row["pattern_bucket"] != blocked_bucket
    ]
    if not candidates:
        raise ValueError("No post-reclaim-shelf broad-search seed candidates remain after exclusions and bucket rotation.")
    candidates.sort(
        key=lambda row: (
            float(row["max_drawdown"]),
            -float(row["cagr"]),
            -float(row["sharpe"]),
        )
    )
    return candidates[0]


def build_report() -> dict:
    post_brief_reset = _load_json(POST_BRIEF_RESET_QUEUE_PATH)
    reclaim_shelf = _load_json(RECLAIM_SHELF_REOPEN_PATH)
    comparative = _load_json(RECENT_FAMILY_COMPARATIVE_PATH)

    exhausted_families = set(post_brief_reset["post_brief_reset_queue_summary"]["exhausted_families"])
    exhausted_families.add(post_brief_reset["selected_broad_search_seed"]["family"])
    holding_families = set(post_brief_reset["post_brief_reset_queue_summary"]["holding_families"])
    blocked_bucket = post_brief_reset["selected_broad_search_seed"]["pattern_bucket"]

    next_seed = _choose_seed(comparative["rows"], exhausted_families, holding_families, blocked_bucket)

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "post_reclaim_shelf_queue_summary": {
            "prior_broad_seed": post_brief_reset["selected_broad_search_seed"]["family"],
            "prior_broad_seed_bucket": blocked_bucket,
            "prior_broad_seed_verdict": reclaim_shelf["reopen_verdict"]["next_step"],
            "exhausted_families": sorted(exhausted_families),
            "holding_families": sorted(holding_families),
            "queue_mode": "single_hold_bucket_rotation_broad_search",
        },
        "selected_broad_search_seed": {
            "family": next_seed["family"],
            "variant_label": next_seed["variant_label"],
            "pattern_bucket": next_seed["pattern_bucket"],
            "screen_label": next_seed["screen_label"],
            "base_cagr": float(next_seed["cagr"]),
            "base_mdd": float(next_seed["max_drawdown"]),
            "base_sharpe": float(next_seed["sharpe"]),
            "completed_trades": int(next_seed["completed_trades"]),
            "artifact_path": next_seed["artifact_path"],
        },
        "near_candidate_hold": post_brief_reset["near_candidate_hold"],
        "broad_search_queue": {
            "selection_logic": [
                "exclude fully exhausted attack lanes and practical-adjacent lanes",
                "keep failed-breakout as the only near-candidate hold",
                "mark reclaim-shelf as exhausted because all reopen variants stayed unstable in stage2",
                "rotate away from the latest reclaim_grab bucket before opening another broad-search seed",
                "prefer low-drawdown low-alpha candidates with enough completed trades to support a reopen batch",
            ],
            "next_step_now": "broad_family_seed_reopen",
            "working_hypothesis": "search a compression-reset style family while failed-breakout stays as the only reserve lane close to candidate-stage",
            "success_gate": {
                "target_bucket": next_seed["pattern_bucket"],
                "must_preserve_drawdown_below": 0.16,
                "must_lift_cagr_above": 0.20,
                "must_reach_candidate_stage_evidence": True,
            },
        },
        "queue_verdict": {
            "selected_family": next_seed["family"],
            "selected_reason": "The reclaim-shelf seed did not survive stage2 cleanly, so broad search continues from the last clean remaining bucket while failed-breakout stays on hold.",
            "next_step_now": "broad_family_seed_reopen",
            "advance_condition": "derive a new attack-capable mutation family from the selected broad-search seed and bring it to candidate-stage evidence.",
        },
        "decision_summary": [
            f"Do not reopen `{post_brief_reset['selected_broad_search_seed']['family']}` again because its reopen verdict is `{reclaim_shelf['reopen_verdict']['next_step']}` and its stage2 variants remained unstable.",
            f"Keep `{post_brief_reset['near_candidate_hold']['family']}` as the only near-candidate hold and open the next broad family search from `{next_seed['family']}`.",
            "Use single-hold rotation now because only one lane remains close to candidate-stage while the rest of the broad-search seeds are exhausted.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    seed = report["selected_broad_search_seed"]
    hold = report["near_candidate_hold"]
    lines = [
        "# BTC 1d Post-Reclaim-Shelf New Family Queue",
        "",
        f"- Selected family: `{seed['family']}`",
        f"- Variant: `{seed['variant_label']}`",
        f"- Pattern bucket: `{seed['pattern_bucket']}`",
        f"- Base: `{seed['base_cagr']:.4f}` CAGR / `{seed['base_mdd']:.4f}` MDD / Sharpe `{seed['base_sharpe']:.4f}`",
        f"- Completed trades: `{seed['completed_trades']}`",
        f"- Near-candidate hold: `{hold['family']}` via `{hold['best_variant_label']}`",
        f"- Queue mode: `{report['post_reclaim_shelf_queue_summary']['queue_mode']}`",
        f"- Next step now: `{report['broad_search_queue']['next_step_now']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_reclaim_shelf_new_family_queue_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_reclaim_shelf_new_family_queue_{stamp}.md"
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
