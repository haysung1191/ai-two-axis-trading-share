from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ANALYSIS_DIR = Path("analysis_results")
POST_MICRO_QUEUE_PATH = ANALYSIS_DIR / "btc_1d_post_micro_undercut_new_family_queue_20260418T152128Z.json"
FAILED_BREAKOUT_HOLD_REFINEMENT_PATH = ANALYSIS_DIR / "btc_1d_failed_breakout_hold_refinement_screen_20260418T153541Z.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report() -> dict:
    post_micro = _load_json(POST_MICRO_QUEUE_PATH)
    hold_refinement = _load_json(FAILED_BREAKOUT_HOLD_REFINEMENT_PATH)

    exhausted = post_micro["post_micro_undercut_queue_summary"]["exhausted_families"]
    hold = post_micro["near_candidate_hold"]
    hold_best = hold_refinement["best_variant"]
    hold_promoted = bool(hold_refinement["hold_refinement_verdict"]["promoted_to_candidate_stage"])
    broad_candidates_left = len(post_micro["post_micro_undercut_queue_summary"]["remaining_broad_candidates"])

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "broad_search_terminal_summary": {
            "queue_mode": post_micro["post_micro_undercut_queue_summary"]["queue_mode"],
            "broad_search_exhausted": broad_candidates_left == 0,
            "remaining_broad_candidates": broad_candidates_left,
            "exhausted_family_count": len(exhausted),
            "final_exhausted_seed": post_micro["exhausted_seed_summary"]["family"],
            "hold_family": hold["family"],
            "hold_refinement_promoted": hold_promoted,
        },
        "hold_status": {
            "family": hold["family"],
            "best_variant_label": hold_best["variant_label"],
            "cagr": float(hold_best["cagr"]),
            "max_drawdown": float(hold_best["max_drawdown"]),
            "sharpe": float(hold_best["sharpe"]),
            "trades": int(hold_best["trades"]),
            "overfitting_flags": list(hold_best.get("overfitting_flags", [])),
            "sensitivity_max_drift": float(hold_best.get("sensitivity_max_drift", 0.0)),
            "promoted_to_candidate_stage": hold_promoted,
            "reason": hold_refinement["hold_refinement_verdict"]["reason"],
        },
        "terminal_verdict": {
            "broad_search_framework_closed": broad_candidates_left == 0 and not hold_promoted,
            "next_model_development_lane": "reframe_failed_breakout_or_define_new_search_framework",
            "reuse_existing_hold_without_reframe": False,
            "reason": (
                "Broad-search rotation is exhausted and the last near-candidate hold still failed to cross the candidate-stage bar after focused refinement."
            ),
            "next_step_now": "terminal_reframe_brief",
        },
        "decision_summary": [
            f"Treat the broad-search framework as closed because `{post_micro['exhausted_seed_summary']['family']}` exhausted the last low-alpha seed and no broad candidates remain.",
            f"Do not promote `{hold['family']}` as-is because hold refinement still topped out at `{float(hold_best['cagr']):.4f}` CAGR with candidate-stage promotion set to `{hold_promoted}`.",
            "Move the next cycle to a terminal reframe brief instead of reopening broad-search or repeating failed-breakout micro-tuning.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    summary = report["broad_search_terminal_summary"]
    hold = report["hold_status"]
    verdict = report["terminal_verdict"]
    return "\n".join(
        [
            "# BTC 1d Post-Broad-Search Terminal Screen",
            "",
            f"- Broad-search exhausted: `{summary['broad_search_exhausted']}`",
            f"- Remaining broad candidates: `{summary['remaining_broad_candidates']}`",
            f"- Final exhausted seed: `{summary['final_exhausted_seed']}`",
            f"- Hold family: `{summary['hold_family']}`",
            f"- Hold refinement promoted: `{summary['hold_refinement_promoted']}`",
            f"- Next model-development lane: `{verdict['next_model_development_lane']}`",
            f"- Next step now: `{verdict['next_step_now']}`",
            "",
            "## Hold Status",
            f"- Best variant: `{hold['best_variant_label']}`",
            f"- Base: `{hold['cagr']:.4f}` CAGR / `{hold['max_drawdown']:.4f}` MDD / Sharpe `{hold['sharpe']:.4f}`",
            f"- Trades: `{hold['trades']}`",
            f"- Overfitting flags: `{', '.join(hold['overfitting_flags']) if hold['overfitting_flags'] else 'none'}`",
            f"- Sensitivity drift: `{hold['sensitivity_max_drift']:.4f}`",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_broad_search_terminal_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_broad_search_terminal_screen_{stamp}.md"
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
