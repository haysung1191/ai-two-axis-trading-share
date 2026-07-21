from __future__ import annotations

from scripts.compare_btc_1d_void_refill_vs_new_family_transition_brief import build_report


def test_void_refill_transition_brief_opens_pullthrough_seed_now() -> None:
    report = build_report()

    summary = report["transition_summary"]
    verdict = report["transition_verdict"]

    assert summary["plateau_lane_label"] == "shallow_liquidity_void_refill_continuation_reference"
    assert summary["deferred_seed_label"] == "volatility_expansion_pullthrough_shorter_hold"
    assert summary["transition_mode"] == "hold_plateau_lane_open_distinct_seed_search"
    assert verdict["open_now"] == "volatility_expansion_pullthrough_shorter_hold"
    assert verdict["hold_in_reserve"] == "shallow_liquidity_void_refill_continuation_reference"
    assert verdict["next_step_now"] == "derive_distinct_attack_family_from_pullthrough_seed"


def test_void_refill_transition_brief_records_plateau_evidence() -> None:
    report = build_report()

    plateau_lane = report["plateau_lane"]
    seed = report["deferred_seed"]

    assert plateau_lane["latest_repair_variant"] == "stronger_confirmation_anchor"
    assert abs(plateau_lane["latest_repair_drift"] - 0.24245351) < 1e-6
    assert plateau_lane["latest_validation_decision"] == "FAIL"
    assert seed["base_cagr"] > plateau_lane["base_cagr"]
    assert seed["base_mdd"] < plateau_lane["base_mdd"]
