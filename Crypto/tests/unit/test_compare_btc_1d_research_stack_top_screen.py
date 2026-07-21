from __future__ import annotations

from scripts.compare_btc_1d_research_stack_top_screen import build_report


def test_compare_btc_1d_research_stack_top_screen_keeps_expected_order() -> None:
    report = build_report()
    assert report["stack_top"]["attack_main"] == "ratio112_tighter_stop_main"
    assert report["stack_top"]["attack_backup"] == "bridge_28_relief"
    assert report["stack_top"]["defensive_hold"] == "volatility_expansion_pullthrough_shorter_hold"


def test_compare_btc_1d_research_stack_top_screen_marks_roles_distinct() -> None:
    report = build_report()
    assert report["stack_verdict"]["roles_are_distinct"] is True
    assert report["stack_verdict"]["top_attack_model"] == "ratio112_tighter_stop_main"
