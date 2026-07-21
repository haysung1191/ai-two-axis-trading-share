from __future__ import annotations

from scripts.compare_btc_1d_pullthrough_asymmetric_release_execution_contract_entry_check import (
    build_report,
)


def test_pullthrough_execution_contract_entry_check_marks_ready() -> None:
    report = build_report()

    requirements = report["execution_contract_entry_requirements"]
    verdict = report["execution_contract_entry_verdict"]

    assert requirements["bridge_entry_ready"] is True
    assert requirements["execution_contract_aligned"] is True
    assert requirements["meta_contract_aligned"] is True
    assert requirements["execution_contract_entry_scope_included"] is True
    assert verdict["execution_contract_entry_ready"] is True


def test_pullthrough_execution_contract_entry_check_points_to_handoff() -> None:
    report = build_report()

    verdict = report["execution_contract_entry_verdict"]
    context = report["stack_context"]

    assert context["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert verdict["execution_contract_queue_lane"] == "challenger_execution_contract_queue"
    assert verdict["next_step_now"] == "candidate_operator_stack_handoff"
