from __future__ import annotations

from scripts.compare_btc_1d_post_failed_breakout_new_family_queue import build_report


def test_post_failed_breakout_new_family_queue_holds_latest_seed() -> None:
    report = build_report()

    holding = set(report["post_failed_breakout_queue_summary"]["holding_families"])
    selected = report["selected_broad_search_seed"]["family"]

    assert "failed_breakout_continuation" in holding
    assert selected not in holding


def test_post_failed_breakout_new_family_queue_rotates_bucket() -> None:
    report = build_report()

    summary = report["post_failed_breakout_queue_summary"]
    verdict = report["queue_verdict"]
    seed = report["selected_broad_search_seed"]

    assert summary["queue_mode"] == "bucket_rotation_with_near_candidate_hold"
    assert seed["pattern_bucket"] != summary["prior_broad_seed_bucket"]
    assert verdict["next_step_now"] == "broad_family_seed_reopen"
