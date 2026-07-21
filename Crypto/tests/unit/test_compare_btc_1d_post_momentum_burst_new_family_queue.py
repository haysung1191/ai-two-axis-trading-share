from __future__ import annotations

from scripts.compare_btc_1d_post_momentum_burst_new_family_queue import build_report


def test_post_momentum_burst_new_family_queue_excludes_failed_seed() -> None:
    report = build_report()

    exhausted = set(report["post_momentum_burst_queue_summary"]["exhausted_families"])
    selected = report["selected_broad_search_seed"]["family"]

    assert "momentum_burst_shallow_reclaim_base" in exhausted
    assert selected not in exhausted


def test_post_momentum_burst_new_family_queue_rotates_bucket() -> None:
    report = build_report()

    summary = report["post_momentum_burst_queue_summary"]
    verdict = report["queue_verdict"]
    seed = report["selected_broad_search_seed"]

    assert summary["queue_mode"] == "bucket_rotation_broad_search"
    assert seed["pattern_bucket"] != summary["prior_broad_seed_bucket"]
    assert verdict["next_step_now"] == "broad_family_seed_reopen"
