from __future__ import annotations

from scripts.compare_btc_1d_pullthrough_exit_to_fresh_seed_brief import build_report


def test_pullthrough_exit_brief_marks_pullthrough_exhausted() -> None:
    report = build_report()

    summary = report["pullthrough_exit_summary"]
    board = report["adjacent_board_status"]
    verdict = report["fresh_seed_verdict"]

    assert summary["candidate_label"] == "volatility_expansion_pullthrough_softer_setup_hold31"
    assert summary["exhausted_for_now"] is True
    assert board["pullthrough_status"] == "exhausted_for_now"
    assert board["adjacent_board_exhausted"] is True
    assert verdict["next_step_now"] == "derive_fresh_non_adjacent_attack_seed"


def test_pullthrough_exit_brief_keeps_void_refill_closed_too() -> None:
    report = build_report()

    board = report["adjacent_board_status"]
    verdict = report["fresh_seed_verdict"]

    assert board["void_refill_label"] == "shallow_liquidity_void_refill_continuation_reference"
    assert board["void_refill_status"] == "plateaued_candidate_hold"
    assert board["void_refill_latest_validation_decision"] == "FAIL"
    assert "volatility_expansion_pullthrough_softer_setup_hold31" in verdict["do_not_reopen_now"]
    assert "shallow_liquidity_void_refill_continuation_reference" in verdict["do_not_reopen_now"]
