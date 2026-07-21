from __future__ import annotations

from scripts.compare_btc_1d_dual_track_queue import build_report


def test_dual_track_queue_selects_distinct_cagr_and_mdd_tracks() -> None:
    report = build_report()

    constraints = report["constraints"]
    cagr_track = report["cagr_track"]
    mdd_track = report["mdd_track"]
    bridge = report["bridge_context"]

    assert report["queue_mode"] == "dual_track_autonomous"
    assert constraints["hold36_ceiling_confirmed"] is True
    assert constraints["hold36_next_step"] == "open_only_new_family_or_wider_frame_search"
    assert "structure" in constraints["do_not_restart_local_axes"]
    assert cagr_track["lane"] == "shallow_liquidity_void_refill_continuation_reference"
    assert cagr_track["next_step_now"] == "compare_with_new_family_search"
    assert mdd_track["primary_label"] == "trend_dip_reversal_breakout_tighter_stop_mid_hold"
    assert mdd_track["goal"] == "compress_drawdown_without_losing_attack_candidate_relevance"
    assert bridge["rotation_next_step"] == "hold_rotation_and_repair_failed_gate"


def test_dual_track_queue_exposes_runner_sequences() -> None:
    report = build_report()

    cagr_track = report["cagr_track"]
    mdd_track = report["mdd_track"]
    constraints = report["constraints"]

    assert any("validate_btc_1d_shallow_liquidity_void_refill_candidate.py" in runner for runner in cagr_track["runner_sequence"])
    assert any(
        "run_btc_1d_trend_dip_reversal_breakout_exit_compression_batch.py" in row["runner"]
        for row in mdd_track["mutation_axes"]
    )
    assert any(
        "validate_btc_1d_trend_dip_reversal_breakout_tsmh_candidate.py" in runner
        for runner in mdd_track["validation_sequence"]
    )
    assert "same_negative_profile" in constraints["rotation_blockers"]
