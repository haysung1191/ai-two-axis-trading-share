from __future__ import annotations

from scripts.compare_btc_1d_pullthrough_asymmetric_release_shadow_monitoring_entry import (
    build_report,
)


def test_pullthrough_shadow_monitoring_entry_marks_ready() -> None:
    report = build_report()

    requirements = report["challenger_shadow_monitoring_entry_requirements"]
    verdict = report["challenger_shadow_monitoring_entry_verdict"]

    assert requirements["operator_runbook_execution_entry_ready"] is True
    assert requirements["operating_index_runbook_execution_entry_ready"] is True
    assert requirements["operating_brief_runbook_execution_entry_ready"] is True
    assert requirements["dashboard_runbook_execution_entry_ready"] is True
    assert requirements["queue_lane_mirrored"] is True
    assert verdict["challenger_shadow_monitoring_entry_ready"] is True


def test_pullthrough_shadow_monitoring_entry_points_to_live_readiness() -> None:
    report = build_report()

    verdict = report["challenger_shadow_monitoring_entry_verdict"]
    context = report["stack_context"]

    assert context["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert verdict["challenger_shadow_monitoring_entry_lane"] == "challenger_shadow_monitoring_queue"
    assert verdict["next_step_now"] == "challenger_candidate_live_readiness_review"
