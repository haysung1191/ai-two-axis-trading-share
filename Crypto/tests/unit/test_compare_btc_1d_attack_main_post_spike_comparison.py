from __future__ import annotations

from scripts.compare_btc_1d_attack_main_post_spike_comparison import build_report


def test_attack_main_post_spike_comparison_keeps_attack_main() -> None:
    report = build_report()
    verdict = report["comparison_verdict"]
    assert verdict["keep_attack_main"] is True
    assert report["stack_reference"]["attack_main"] == "ratio112_tighter_stop_main"


def test_attack_main_post_spike_comparison_adds_post_spike_as_challenger() -> None:
    report = build_report()
    verdict = report["comparison_verdict"]
    assert verdict["add_post_spike_challenger"] is True
    assert verdict["next_step_now"] == "promote_post_spike_into_attack_experiment_board"
