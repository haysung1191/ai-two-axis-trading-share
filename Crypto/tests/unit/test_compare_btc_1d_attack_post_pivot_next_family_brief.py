from __future__ import annotations

from scripts.compare_btc_1d_attack_post_pivot_next_family_brief import build_report


def test_attack_post_pivot_next_family_brief_selects_defensive_hold_as_seed() -> None:
    report = build_report()

    brief = report["next_family_brief"]
    current = report["current_stack"]
    handoff = report["trend_dip_handoff"]

    assert current["primary_mutation_space_closed"] is True
    assert current["primary_lane_handoff_status"] == "exhausted_for_now"
    assert brief["selected_seed_label"] == "volatility_expansion_pullthrough_shorter_hold"
    assert brief["selected_seed_role"] == "defensive_research_hold"
    assert handoff["best_stage1_candidate"] == "volume_lookback_16_seeded"


def test_attack_post_pivot_next_family_brief_excludes_exhausted_lanes() -> None:
    report = build_report()

    brief = report["next_family_brief"]

    assert "ratio112_tighter_stop_main" in brief["do_not_restart"]
    assert "bridge_28_relief" in brief["do_not_restart"]
    assert "volatility_spike_reversal_continuation_slower_trend" in brief["do_not_restart"]
