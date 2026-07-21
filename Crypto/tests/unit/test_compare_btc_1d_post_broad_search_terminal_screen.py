from __future__ import annotations

from scripts.compare_btc_1d_post_broad_search_terminal_screen import build_report


def test_post_broad_search_terminal_screen_closes_broad_search_framework() -> None:
    report = build_report()

    summary = report["broad_search_terminal_summary"]
    verdict = report["terminal_verdict"]

    assert summary["broad_search_exhausted"] is True
    assert summary["remaining_broad_candidates"] == 0
    assert summary["hold_refinement_promoted"] is False
    assert verdict["broad_search_framework_closed"] is True


def test_post_broad_search_terminal_screen_points_to_reframe_lane() -> None:
    report = build_report()

    verdict = report["terminal_verdict"]
    hold = report["hold_status"]

    assert verdict["next_model_development_lane"] == "reframe_failed_breakout_or_define_new_search_framework"
    assert verdict["next_step_now"] == "terminal_reframe_brief"
    assert hold["family"] == "failed_breakout_continuation"
