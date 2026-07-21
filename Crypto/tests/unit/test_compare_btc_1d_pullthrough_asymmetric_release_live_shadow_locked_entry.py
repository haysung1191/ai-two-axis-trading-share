from __future__ import annotations

from scripts.compare_btc_1d_pullthrough_asymmetric_release_live_shadow_locked_entry import (
    build_report,
)


def test_pullthrough_live_shadow_locked_entry_marks_ready() -> None:
    report = build_report()

    requirements = report["challenger_live_shadow_locked_entry_requirements"]
    verdict = report["challenger_live_shadow_locked_entry_verdict"]

    assert requirements["challenger_live_shadow_candidate_governance_lock_ready"] is True
    assert requirements["operating_index_live_shadow_candidate_governance_lock_ready"] is True
    assert requirements["operating_brief_live_shadow_candidate_governance_lock_ready"] is True
    assert requirements["dashboard_live_shadow_candidate_governance_lock_ready"] is True
    assert requirements["queue_lane_mirrored"] is True
    assert verdict["challenger_live_shadow_locked_entry_ready"] is True


def test_pullthrough_live_shadow_locked_entry_points_to_locked_candidate_review() -> None:
    report = build_report()

    verdict = report["challenger_live_shadow_locked_entry_verdict"]
    context = report["stack_context"]

    assert (
        context["attack_challenger_candidate"]
        == "pullthrough_asymmetric_release_tighter_exit"
    )
    assert (
        verdict["challenger_live_shadow_locked_entry_lane"]
        == "challenger_live_shadow_locked_queue"
    )
    assert verdict["next_step_now"] == "challenger_live_shadow_locked_candidate_review"
