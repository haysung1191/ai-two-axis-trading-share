from __future__ import annotations

from scripts.compare_btc_1d_pullthrough_asymmetric_release_operator_runbook_execution_entry import (
    build_report,
)


def test_pullthrough_operator_runbook_execution_entry_marks_ready() -> None:
    report = build_report()

    requirements = report["operator_runbook_execution_entry_requirements"]
    verdict = report["operator_runbook_execution_entry_verdict"]

    assert requirements["operator_runbook_candidate_entry_ready"] is True
    assert requirements["operating_index_runbook_candidate_entry_ready"] is True
    assert requirements["operating_brief_runbook_candidate_entry_ready"] is True
    assert requirements["dashboard_runbook_candidate_entry_ready"] is True
    assert requirements["queue_lane_mirrored"] is True
    assert verdict["operator_runbook_execution_entry_ready"] is True


def test_pullthrough_operator_runbook_execution_entry_points_to_shadow_monitoring() -> None:
    report = build_report()

    verdict = report["operator_runbook_execution_entry_verdict"]
    context = report["stack_context"]

    assert context["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert verdict["operator_runbook_execution_entry_lane"] == "operator_runbook_execution_queue"
    assert verdict["next_step_now"] == "challenger_shadow_monitoring_entry"
