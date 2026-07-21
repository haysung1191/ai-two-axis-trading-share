from __future__ import annotations

from scripts.compare_btc_1d_attack_pivot_screen import build_report


def test_attack_pivot_screen_closes_primary_mutation_space() -> None:
    report = build_report()

    primary = report["primary_lane_status"]
    verdict = report["pivot_verdict"]

    assert primary["mutation_space_closed"] is True
    assert verdict["continue_primary_mutation_loop"] is False
    assert verdict["active_attack_anchor"] == "tighter_stop_mid_hold"


def test_attack_pivot_screen_defers_secondary_branch() -> None:
    report = build_report()

    secondary = report["secondary_lane_status"]
    verdict = report["pivot_verdict"]

    assert secondary["promotion_status"] == "secondary_upside_branch_only"
    assert secondary["promotion_ready"] is False
    assert verdict["promote_secondary_now"] is False
    assert verdict["next_model_development_lane"] == "secondary_friction_repair_or_new_family_search"
