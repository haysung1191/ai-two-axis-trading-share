from __future__ import annotations

from scripts.compare_btc_1d_spike_reversal_secondary_promotion_screen import build_report


def test_spike_reversal_secondary_promotion_screen_keeps_branch_secondary() -> None:
    report = build_report()

    secondary = report["secondary_branch_candidate"]
    verdict = report["secondary_branch_verdict"]

    assert secondary["best_batch_variant_label"] == "slower_trend"
    assert verdict["promotion_status"] == "secondary_upside_branch_only"
    assert verdict["promotion_ready"] is False
    assert verdict["outranks_primary_attack_retest"] is False


def test_spike_reversal_secondary_promotion_screen_surfaces_friction_gate() -> None:
    report = build_report()

    friction = report["friction_summary"]
    validation = report["validation_snapshot"]
    verdict = report["secondary_branch_verdict"]

    assert friction["final_decision"] == "pause"
    assert friction["all_levels_failed"] is True
    assert validation["decision"] == "FAIL"
    assert verdict["next_required_gate"] == "friction_pass_and_candidate_stage_promotion"
