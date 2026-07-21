from __future__ import annotations

from scripts.compare_btc_1d_near_miss_priority_screen import build_report


def test_near_miss_priority_screen_keeps_expected_priority() -> None:
    report = build_report()
    assert report["priority_verdict"]["highest_priority_near_miss"] == "trend_dip_reversal_breakout_tighter_stop_mid_hold"
    assert report["priority_verdict"]["highest_raw_upside_near_miss"] == "volatility_spike_reversal_continuation_slower_trend"


def test_near_miss_priority_screen_keeps_frontier_fixed() -> None:
    report = build_report()
    assert report["attack_frontier"] == "ratio112_tighter_stop_main"
