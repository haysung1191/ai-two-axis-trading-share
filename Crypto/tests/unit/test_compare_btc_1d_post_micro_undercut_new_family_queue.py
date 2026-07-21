from __future__ import annotations

from scripts.compare_btc_1d_post_micro_undercut_new_family_queue import build_report


def test_post_micro_undercut_queue_exhausts_broad_search_pool() -> None:
    report = build_report()

    summary = report["post_micro_undercut_queue_summary"]
    exhausted = set(summary["exhausted_families"])
    holding = set(summary["holding_families"])

    assert "micro_undercut_reclaim_continuation" in exhausted
    assert holding == {"failed_breakout_continuation"}
    assert summary["remaining_broad_candidates"] == []
    assert report["queue_verdict"]["selected_family"] is None


def test_post_micro_undercut_queue_switches_to_hold_only_mode() -> None:
    report = build_report()

    summary = report["post_micro_undercut_queue_summary"]
    verdict = report["queue_verdict"]

    assert summary["queue_mode"] == "hold_only_broad_search_exhausted"
    assert verdict["next_step_now"] == "near_candidate_hold_revisit_or_new_search_framework"
    assert report["near_candidate_hold"]["family"] == "failed_breakout_continuation"
