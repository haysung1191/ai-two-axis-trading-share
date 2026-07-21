from __future__ import annotations

from scripts.compare_btc_1d_research_stack_gap_screen import build_report


def test_research_stack_gap_screen_keeps_attack_frontier_fixed() -> None:
    report = build_report()
    assert report["gap_summary"]["preferred_attack_frontier"] == "ratio112_tighter_stop_main"
    assert report["stack_top"]["attack_main"] == "ratio112_tighter_stop_main"


def test_research_stack_gap_screen_includes_recent_attack_near_miss_holds() -> None:
    report = build_report()
    labels = {item["label"] for item in report["recent_attack_near_miss_holds"]}
    assert "trend_dip_reversal_breakout_tighter_stop_mid_hold" in labels
    assert "volatility_spike_reversal_continuation_slower_trend" in labels
