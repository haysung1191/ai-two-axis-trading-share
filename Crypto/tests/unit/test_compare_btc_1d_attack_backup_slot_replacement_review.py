from __future__ import annotations

from scripts.compare_btc_1d_attack_backup_slot_replacement_review import build_report


def test_attack_backup_slot_replacement_review_promotes_post_spike_into_backup_slot() -> None:
    report = build_report()
    verdict = report["replacement_review"]

    assert verdict["promote_post_spike_into_backup_slot"] is True
    assert verdict["proposed_attack_backup"] == "post_spike_trend92_depth058_volume105_hold36"
    assert verdict["proposed_attack_challenger"] == "post_spike_walk_forward_repair::trend84_depth055_volume104_hold34"
    assert verdict["next_step_now"] == "promote_reopen_seed_into_attack_backup_slot"


def test_attack_backup_slot_replacement_review_keeps_main_fixed() -> None:
    report = build_report()

    assert report["current_stack"]["attack_main"] == "ratio112_tighter_stop_main"
    assert report["replacement_review"]["keep_attack_main_unchanged"] is True
    assert report["supporting_metrics"]["cagr_gap_to_backup"] < 0.0
