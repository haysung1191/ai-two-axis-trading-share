from __future__ import annotations

from scripts.compare_btc_1d_pullthrough_asymmetric_release_operator_stack_handoff import (
    build_report,
)


def test_pullthrough_operator_stack_handoff_marks_ready() -> None:
    report = build_report()

    requirements = report["operator_stack_handoff_requirements"]
    verdict = report["operator_stack_handoff_verdict"]

    assert requirements["execution_contract_entry_ready"] is True
    assert requirements["operating_index_contract_entry_ready"] is True
    assert requirements["operating_brief_contract_entry_ready"] is True
    assert requirements["dashboard_contract_entry_ready"] is True
    assert requirements["queue_lane_mirrored"] is True
    assert verdict["operator_stack_handoff_ready"] is True


def test_pullthrough_operator_stack_handoff_points_to_runbook_entry() -> None:
    report = build_report()

    verdict = report["operator_stack_handoff_verdict"]
    context = report["stack_context"]

    assert context["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert verdict["operator_stack_handoff_lane"] == "operator_stack_handoff_queue"
    assert verdict["next_step_now"] == "operator_runbook_candidate_entry"
