from __future__ import annotations

from scripts.compare_btc_1d_terminal_reframe_brief import build_report


def test_terminal_reframe_brief_uses_defensive_hold_seed() -> None:
    report = build_report()

    brief = report["reframe_brief"]
    terminal = report["terminal_state"]

    assert terminal["broad_search_framework_closed"] is True
    assert brief["selected_seed_label"] == "volatility_expansion_pullthrough_shorter_hold"
    assert brief["selected_seed_role"] == "defensive_research_hold"


def test_terminal_reframe_brief_blocks_failed_hold_restart() -> None:
    report = build_report()

    brief = report["reframe_brief"]

    assert "failed_breakout_continuation" in brief["do_not_restart"]
    assert brief["success_gate"]["must_not_reuse_failed_hold_without_reframe"] is True
    assert brief["success_gate"]["candidate_stage_floor_cagr"] == 0.20
