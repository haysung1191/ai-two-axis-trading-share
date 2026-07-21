from __future__ import annotations

from scripts.compare_btc_1d_new_family_search_queue import build_report


def test_new_family_search_queue_selects_void_refill_lane() -> None:
    report = build_report()

    summary = report["search_queue_summary"]
    verdict = report["queue_verdict"]
    transition = report["transition_context"]
    validation = report["current_validation_snapshot"]
    plateau = report["plateau_assessment"]

    assert summary["next_family_lane"] == "shallow_liquidity_void_refill_continuation_reference"
    assert summary["post_pivot_seed_status"] == "held_out_as_seed_source"
    assert summary["queue_mode"] == "plateau_review"
    assert verdict["next_step_now"] == "compare_with_new_family_search"
    assert transition["primary_lane_status"] == "exhausted_for_now"
    assert transition["deferred_seed_label"] == "volatility_expansion_pullthrough_shorter_hold"
    assert transition["post_pivot_artifact_path"].endswith(
        "btc_1d_attack_post_pivot_next_family_brief_latest.json"
    ) or transition["post_pivot_artifact_path"] == "in_memory_build"
    assert transition["practical_adjacent_artifact_path"].endswith(
        "btc_1d_defensive_practical_adjacent_screen_latest.json"
    ) or "btc_1d_defensive_practical_adjacent_screen_" in transition["practical_adjacent_artifact_path"]
    assert validation["decision"] == "FAIL"
    assert "overfitting_sensitivity" in validation["failed_gates"]
    assert plateau["plateaued"] is True
    assert plateau["repair_best_variant"] == "stronger_confirmation_anchor"


def test_new_family_search_queue_excludes_exhausted_lanes() -> None:
    report = build_report()

    exhausted = set(report["search_queue_summary"]["exhausted_lanes"])
    lane = report["next_family_lane"]["label"]
    transition = report["transition_context"]
    queue = report["repair_queue"]
    plateau = report["plateau_assessment"]

    assert "volatility_expansion_pullthrough_shorter_hold" in exhausted
    assert "volatility_spike_reversal_continuation_slower_trend" in exhausted
    assert lane not in exhausted
    assert transition["primary_lane_best_stage1_candidate"] == "volume_lookback_16_seeded"
    assert "btc_1d_shallow_liquidity_void_refill_friction_" in queue["friction_artifact_path"]
    assert "btc_1d_shallow_liquidity_void_refill_repair_screen_" in queue["repair_screen_artifact_path"]
    assert plateau["micro_best_variant"] == "cleaner_impulse_stronger_confirmation"
