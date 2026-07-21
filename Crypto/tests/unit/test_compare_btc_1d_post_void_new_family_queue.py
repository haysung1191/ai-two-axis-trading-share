from __future__ import annotations

from scripts.compare_btc_1d_post_void_new_family_queue import build_report


def test_post_void_new_family_queue_avoids_exhausted_families() -> None:
    report = build_report()

    exhausted = set(report["post_void_queue_summary"]["exhausted_families"])
    selected = report["selected_broad_search_seed"]["family"]

    assert "volatility_expansion_pullthrough" in exhausted
    assert "shallow_liquidity_void_refill_continuation" in exhausted
    assert selected not in exhausted


def test_post_void_new_family_queue_selects_broad_search_seed() -> None:
    report = build_report()

    summary = report["post_void_queue_summary"]
    verdict = report["queue_verdict"]
    seed = report["selected_broad_search_seed"]

    assert summary["queue_mode"] == "plateau_compare_to_fresh_seed_restart"
    assert summary["void_lane_verdict"] == "compare_with_new_family_search"
    assert verdict["next_step_now"] == "reopen_batch"
    assert seed["family"] == "post_spike_consolidation_breakout"
