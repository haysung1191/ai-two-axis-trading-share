from __future__ import annotations

from scripts.compare_btc_1d_post_shallow_breakout_new_family_queue import build_report


def test_post_shallow_breakout_new_family_queue_exhausts_shallow_breakout_seed() -> None:
    report = build_report()

    exhausted = set(report["post_shallow_breakout_queue_summary"]["exhausted_families"])
    holding = set(report["post_shallow_breakout_queue_summary"]["holding_families"])
    selected = report["selected_broad_search_seed"]["family"]

    assert "shallow_breakout_shelf_continuation" in exhausted
    assert "failed_breakout_continuation" in holding
    assert selected not in exhausted
    assert selected not in holding


def test_post_shallow_breakout_new_family_queue_rotates_bucket() -> None:
    report = build_report()

    summary = report["post_shallow_breakout_queue_summary"]
    verdict = report["queue_verdict"]
    seed = report["selected_broad_search_seed"]

    assert summary["queue_mode"] == "single_hold_last_candidate_rotation"
    assert seed["pattern_bucket"] != summary["prior_broad_seed_bucket"]
    assert verdict["next_step_now"] == "broad_family_seed_reopen"
