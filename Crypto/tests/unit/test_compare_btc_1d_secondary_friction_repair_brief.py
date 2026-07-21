from __future__ import annotations

from scripts.compare_btc_1d_secondary_friction_repair_brief import build_report


def test_secondary_friction_repair_brief_targets_pause_flip() -> None:
    report = build_report()

    blocker = report["current_friction_blocker"]
    gate = report["repair_brief"]["success_gate"]

    assert blocker["final_decision"] == "pause"
    assert gate["must_flip_final_decision_from"] == "pause"
    assert gate["must_clear_failed_gate"] == "backtest_max_drawdown"


def test_secondary_friction_repair_brief_keeps_secondary_behind_primary_until_ready() -> None:
    report = build_report()

    brief = report["repair_brief"]
    candidate = report["secondary_candidate"]

    assert candidate["best_batch_variant_label"] == "slower_trend"
    assert brief["pivot_source"] == "secondary_friction_repair_or_new_family_search"
    assert brief["success_gate"]["do_not_overtake_primary_anchor_until"] == "promotion_ready=true"
