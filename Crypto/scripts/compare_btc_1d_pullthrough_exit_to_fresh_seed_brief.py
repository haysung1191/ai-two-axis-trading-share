from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_pullthrough_candidate_stage_review import build_report as build_pullthrough_stage_review
from scripts.compare_btc_1d_void_refill_vs_new_family_transition_brief import (
    build_report as build_void_refill_transition_brief,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest_required_artifact(pattern: str) -> tuple[Path, dict]:
    matches = sorted(ANALYSIS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No artifact found for pattern: {pattern}")
    path = matches[0]
    return path, _load_json(path)


def build_report() -> dict:
    pullthrough_stage = build_pullthrough_stage_review()
    void_transition = build_void_refill_transition_brief()
    structural_path, structural = _latest_required_artifact("btc_1d_pullthrough_candidate_structural_repair_batch_*.json")
    refine_path, refine = _latest_required_artifact("btc_1d_pullthrough_candidate_refine_batch_*.json")
    confirmation_path, confirmation = _latest_required_artifact("btc_1d_pullthrough_confirmation_repair_batch_*.json")

    pullthrough_candidate = pullthrough_stage["candidate_profile"]
    structural_best = structural["best_variant"]
    refine_best = refine["best_variant"]
    confirmation_best = confirmation["best_variant"]
    plateau_lane = void_transition["plateau_lane"]

    pullthrough_exhausted = (
        pullthrough_stage["pullthrough_candidate_stage_review_verdict"]["candidate_stage_ready"] is False
        and int(structural_best["negative_window_count"]) >= 1
        and str(refine_best["variant_label"]) == "baseline_hold31"
        and int(confirmation_best["negative_window_count"]) >= 1
    )
    adjacent_board_exhausted = pullthrough_exhausted and plateau_lane["latest_validation_decision"] == "FAIL"

    next_step_now = (
        "derive_fresh_non_adjacent_attack_seed"
        if adjacent_board_exhausted
        else "continue_adjacent_family_search"
    )
    queue_lane = (
        "fresh_seed_search_required"
        if adjacent_board_exhausted
        else "adjacent_family_search_still_open"
    )

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "pullthrough_exit_summary": {
            "candidate_label": pullthrough_candidate["label"],
            "candidate_stage_ready": pullthrough_stage["pullthrough_candidate_stage_review_verdict"]["candidate_stage_ready"],
            "negative_walk_forward_windows": list(pullthrough_candidate["negative_walk_forward_windows"]),
            "idle_walk_forward_windows": list(pullthrough_candidate["idle_walk_forward_windows"]),
            "baseline_drift": float(pullthrough_candidate["walk_forward_sensitivity_max_drift"]),
            "structural_best_variant": str(structural_best["variant_label"]),
            "structural_best_worst_window_sharpe": float(structural_best["worst_window_sharpe"]),
            "refine_best_variant": str(refine_best["variant_label"]),
            "confirmation_best_variant": str(confirmation_best["variant_label"]),
            "confirmation_best_base_cagr": float(confirmation_best["base_cagr"]),
            "exhausted_for_now": pullthrough_exhausted,
        },
        "adjacent_board_status": {
            "pullthrough_status": "exhausted_for_now" if pullthrough_exhausted else "still_open",
            "void_refill_status": "plateaued_candidate_hold",
            "void_refill_label": plateau_lane["label"],
            "void_refill_latest_validation_decision": plateau_lane["latest_validation_decision"],
            "void_refill_latest_failed_gates": list(plateau_lane["latest_failed_gates"]),
            "adjacent_board_exhausted": adjacent_board_exhausted,
        },
        "artifact_paths": {
            "pullthrough_stage_review_json": str(ANALYSIS_DIR / "btc_1d_pullthrough_candidate_stage_review_latest.json")
            if (ANALYSIS_DIR / "btc_1d_pullthrough_candidate_stage_review_latest.json").exists()
            else "",
            "structural_repair_json": str(structural_path),
            "refine_repair_json": str(refine_path),
            "confirmation_repair_json": str(confirmation_path),
        },
        "fresh_seed_verdict": {
            "queue_lane": queue_lane,
            "next_step_now": next_step_now,
            "reason": (
                "Pullthrough failed to clear its negative walk-forward window after threshold, structural, refine, and confirmation repair passes, while the void-refill lane remains a plateaued hold. The next attack cycle should therefore leave the current practical-adjacent board and open a fresh seed search."
                if adjacent_board_exhausted
                else "At least one practical-adjacent lane still has enough unexplored headroom to justify another adjacent-family pass."
            ),
            "do_not_reopen_now": [
                pullthrough_candidate["label"],
                plateau_lane["label"],
            ],
        },
        "decision_summary": [
            f"Freeze `{pullthrough_candidate['label']}` because its walk-forward blocker survived every repair axis tried in this thread.",
            f"Keep `{plateau_lane['label']}` as a plateaued hold, not as the next active repair lane.",
            (
                "Spend the next attack-search cycle on a fresh non-adjacent seed because the current practical-adjacent board is exhausted."
                if adjacent_board_exhausted
                else "Stay on the practical-adjacent board because at least one adjacent lane still warrants another pass."
            ),
        ],
    }


def _render_markdown(report: dict) -> str:
    summary = report["pullthrough_exit_summary"]
    board = report["adjacent_board_status"]
    verdict = report["fresh_seed_verdict"]
    paths = report["artifact_paths"]
    return "\n".join(
        [
            "# BTC 1d Pullthrough Exit To Fresh Seed Brief",
            "",
            f"- Pullthrough candidate: `{summary['candidate_label']}`",
            f"- Pullthrough exhausted: `{summary['exhausted_for_now']}`",
            f"- Baseline drift: `{summary['baseline_drift']:.4f}`",
            f"- Structural best: `{summary['structural_best_variant']}` | worst window sharpe `{summary['structural_best_worst_window_sharpe']:.4f}`",
            f"- Refine best: `{summary['refine_best_variant']}`",
            f"- Confirmation best: `{summary['confirmation_best_variant']}` | base CAGR `{summary['confirmation_best_base_cagr']:.4f}`",
            f"- Adjacent board exhausted: `{board['adjacent_board_exhausted']}`",
            f"- Void-refill status: `{board['void_refill_status']}`",
            f"- Next step now: `{verdict['next_step_now']}`",
            f"- Reason: {verdict['reason']}",
            "",
            "## Do Not Reopen Now",
            *(f"- `{label}`" for label in verdict["do_not_reopen_now"]),
            "",
            "## Artifacts",
            f"- structural repair: `{paths['structural_repair_json']}`",
            f"- refine repair: `{paths['refine_repair_json']}`",
            f"- confirmation repair: `{paths['confirmation_repair_json']}`",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_pullthrough_exit_to_fresh_seed_brief_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_pullthrough_exit_to_fresh_seed_brief_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_pullthrough_exit_to_fresh_seed_brief_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_pullthrough_exit_to_fresh_seed_brief_md_latest.md"
    json_payload = json.dumps(report, indent=2)
    md_payload = _render_markdown(report)
    json_path.write_text(json_payload, encoding="utf-8")
    md_path.write_text(md_payload, encoding="utf-8")
    latest_json.write_text(json_payload, encoding="utf-8")
    latest_md.write_text(md_payload, encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
