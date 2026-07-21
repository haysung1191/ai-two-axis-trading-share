from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ANALYSIS_DIR = Path("analysis_results")
POST_ONE_BAR_QUEUE_PATH = ANALYSIS_DIR / "btc_1d_post_one_bar_new_family_queue_20260418T141344Z.json"
MOMENTUM_BURST_REOPEN_PATH = ANALYSIS_DIR / "btc_1d_momentum_burst_shallow_reclaim_reopen_screen_20260418T142326Z.json"
RECENT_FAMILY_COMPARATIVE_PATH = ANALYSIS_DIR / "btc_1d_recent_family_comparative_screen_20260415T205917Z.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _choose_seed(rows: list[dict], exhausted_families: set[str], blocked_bucket: str) -> dict:
    candidates = [
        row
        for row in rows
        if row["family"] not in exhausted_families
        and row["screen_label"] == "low_alpha_kill"
        and row["completed_trades"] >= 5
        and float(row["max_drawdown"]) <= 0.16
        and row["pattern_bucket"] != blocked_bucket
    ]
    if not candidates:
        raise ValueError("No post-momentum-burst broad-search seed candidates remain after excluding exhausted families and blocked bucket.")
    candidates.sort(
        key=lambda row: (
            float(row["max_drawdown"]),
            -float(row["cagr"]),
            -float(row["sharpe"]),
        )
    )
    return candidates[0]


def build_report() -> dict:
    post_one_bar = _load_json(POST_ONE_BAR_QUEUE_PATH)
    momentum_burst = _load_json(MOMENTUM_BURST_REOPEN_PATH)
    comparative = _load_json(RECENT_FAMILY_COMPARATIVE_PATH)

    exhausted_families = set(post_one_bar["post_one_bar_queue_summary"]["exhausted_families"])
    exhausted_families.add(post_one_bar["selected_broad_search_seed"]["family"])
    blocked_bucket = post_one_bar["selected_broad_search_seed"]["pattern_bucket"]

    next_seed = _choose_seed(comparative["rows"], exhausted_families, blocked_bucket)

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "post_momentum_burst_queue_summary": {
            "prior_broad_seed": post_one_bar["selected_broad_search_seed"]["family"],
            "prior_broad_seed_bucket": blocked_bucket,
            "prior_broad_seed_verdict": momentum_burst["reopen_verdict"]["next_step"],
            "exhausted_families": sorted(exhausted_families),
            "queue_mode": "bucket_rotation_broad_search",
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
        "broad_search_queue": {
            "selection_logic": [
                "exclude exhausted attack lanes, practical-adjacent lanes, and failed broad-search seeds",
                "rotate away from the failed reclaim_grab bucket before broadening search inside it again",
                "prefer low-drawdown low-alpha candidates with enough completed trades to support a reopen batch",
            ],
            "next_step_now": "broad_family_seed_reopen",
            "working_hypothesis": "search a fresh breakout-continuation style attack family after the reclaim-grab seed could not reopen into candidate-stage evidence",
            "success_gate": {
                "target_bucket": next_seed["pattern_bucket"],
                "must_preserve_drawdown_below": 0.16,
                "must_lift_cagr_above": 0.20,
                "must_reach_candidate_stage_evidence": True,
            },
        },
        "queue_verdict": {
            "selected_family": next_seed["family"],
            "selected_reason": "The reclaim-grab seed could not reopen cleanly, so broad search rotates into the cleanest remaining low-drawdown bucket with enough trade density.",
            "next_step_now": "broad_family_seed_reopen",
            "advance_condition": "derive a new attack-capable mutation family from the selected broad-search seed and bring it to candidate-stage evidence.",
        },
        "decision_summary": [
            f"Do not reopen `{post_one_bar['selected_broad_search_seed']['family']}` again because its reopen verdict is `{momentum_burst['reopen_verdict']['next_step']}`.",
            f"Rotate out of `{blocked_bucket}` and open the next broad family search from `{next_seed['family']}`.",
            "Use bucket rotation now because repeated reopen attempts across the latest broad-search buckets did not produce a candidate-stage family.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    seed = report["selected_broad_search_seed"]
    lines = [
        "# BTC 1d Post-Momentum-Burst New Family Queue",
        "",
        f"- Selected family: `{seed['family']}`",
        f"- Variant: `{seed['variant_label']}`",
        f"- Pattern bucket: `{seed['pattern_bucket']}`",
        f"- Base: `{seed['base_cagr']:.4f}` CAGR / `{seed['base_mdd']:.4f}` MDD / Sharpe `{seed['base_sharpe']:.4f}`",
        f"- Completed trades: `{seed['completed_trades']}`",
        f"- Queue mode: `{report['post_momentum_burst_queue_summary']['queue_mode']}`",
        f"- Next step now: `{report['broad_search_queue']['next_step_now']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_momentum_burst_new_family_queue_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_momentum_burst_new_family_queue_{stamp}.md"
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
