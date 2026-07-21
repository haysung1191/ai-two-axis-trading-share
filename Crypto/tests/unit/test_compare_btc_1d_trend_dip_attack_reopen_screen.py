from __future__ import annotations

from scripts.compare_btc_1d_trend_dip_attack_reopen_screen import build_report


def test_trend_dip_attack_reopen_screen_prefers_symmetry_family() -> None:
    report = build_report()

    verdict = report["reopen_verdict"]
    assert verdict["preferred_mutation_family"] == "exit_symmetry"
    assert verdict["preferred_variant_label"] == "tighter_stop_mid_hold"
    assert verdict["keep_current_candidate_as_drawdown_anchor"] is True


def test_trend_dip_attack_reopen_screen_keeps_friction_pause_visible() -> None:
    report = build_report()

    assert report["friction_summary"]["final_decision"] == "pause"
    assert report["current_candidate"]["label"] == "tighter_stop_mid_hold"
    assert report["best_exit_compression_variant"]["variant_label"] == "tighter_stop_shorter_hold"
