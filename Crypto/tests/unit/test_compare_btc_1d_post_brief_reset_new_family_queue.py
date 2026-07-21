from __future__ import annotations

from scripts.compare_btc_1d_post_brief_reset_new_family_queue import build_report


def test_post_brief_reset_new_family_queue_exhausts_brief_reset_seed() -> None:
    report = build_report()

    exhausted = set(report["post_brief_reset_queue_summary"]["exhausted_families"])
    holding = set(report["post_brief_reset_queue_summary"]["holding_families"])
    selected = report["selected_broad_search_seed"]["family"]

    assert "brief_close_above_reset_continuation" in exhausted
    assert "failed_breakout_continuation" in holding
    assert selected not in exhausted
    assert selected not in holding


def test_post_brief_reset_new_family_queue_rotates_bucket() -> None:
    report = build_report()

    summary = report["post_brief_reset_queue_summary"]
    verdict = report["queue_verdict"]
    seed = report["selected_broad_search_seed"]

    assert summary["queue_mode"] == "hold_and_bucket_rotation_broad_search"
    assert seed["pattern_bucket"] != summary["prior_broad_seed_bucket"]
    assert verdict["next_step_now"] == "broad_family_seed_reopen"
