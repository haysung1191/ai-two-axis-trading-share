from __future__ import annotations

from scripts.compare_btc_1d_pullthrough_asymmetric_release_promotion_bridge import build_report


def test_pullthrough_asymmetric_release_promotion_bridge_marks_candidate_ready() -> None:
    report = build_report()

    verdict = report["promotion_bridge_verdict"]
    candidate = report["candidate_profile"]

    assert verdict["promotion_ready"] is True
    assert candidate["friction_final_decision"] == "continue"
    assert verdict["next_step_now"] == "candidate_promotion_bridge_entry"


def test_pullthrough_asymmetric_release_promotion_bridge_improves_on_defensive_hold() -> None:
    report = build_report()

    verdict = report["promotion_bridge_verdict"]

    assert verdict["beats_defensive_hold_on_cagr"] is True
    assert verdict["improves_on_defensive_hold_drift"] is True
    assert verdict["maintains_attack_band_drawdown"] is True
    assert verdict["role_assignment"] == "attack_challenger_candidate"
