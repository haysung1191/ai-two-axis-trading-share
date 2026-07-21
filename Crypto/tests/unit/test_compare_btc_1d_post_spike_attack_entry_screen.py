from __future__ import annotations

from scripts.compare_btc_1d_post_spike_attack_entry_screen import build_report


def test_post_spike_attack_entry_screen_marks_candidate_ready() -> None:
    report = build_report()
    verdict = report["post_spike_attack_entry_verdict"]
    assert verdict["attack_entry_ready"] is True
    assert verdict["queue_lane"] == "attack_comparison_entry_queue"
    assert verdict["next_step_now"] == "run_attack_main_comparison_with_post_spike_candidate"


def test_post_spike_attack_entry_screen_keeps_attack_stack_reference() -> None:
    report = build_report()
    assert report["attack_stack_reference"]["attack_main"] == "ratio112_tighter_stop_main"
    assert report["attack_stack_reference"]["attack_backup"] == "ratio111_tighter_stop_backup"
