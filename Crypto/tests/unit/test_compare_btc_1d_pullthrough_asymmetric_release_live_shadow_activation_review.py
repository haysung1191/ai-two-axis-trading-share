from __future__ import annotations

from scripts.compare_btc_1d_pullthrough_asymmetric_release_live_shadow_activation_review import (
    build_report,
)


def test_pullthrough_live_shadow_activation_review_marks_ready() -> None:
    report = build_report()

    requirements = report["challenger_live_shadow_activation_review_requirements"]
    verdict = report["challenger_live_shadow_activation_review_verdict"]

    assert requirements["challenger_candidate_live_readiness_review_ready"] is True
    assert requirements["operating_index_live_readiness_review_ready"] is True
    assert requirements["operating_brief_live_readiness_review_ready"] is True
    assert requirements["dashboard_live_readiness_review_ready"] is True
    assert requirements["queue_lane_mirrored"] is True
    assert verdict["challenger_live_shadow_activation_review_ready"] is True


def test_pullthrough_live_shadow_activation_review_points_to_live_candidate_entry() -> None:
    report = build_report()

    verdict = report["challenger_live_shadow_activation_review_verdict"]
    context = report["stack_context"]

    assert (
        context["attack_challenger_candidate"]
        == "pullthrough_asymmetric_release_tighter_exit"
    )
    assert (
        verdict["challenger_live_shadow_activation_review_lane"]
        == "challenger_live_shadow_activation_queue"
    )
    assert verdict["next_step_now"] == "challenger_live_candidate_entry"
