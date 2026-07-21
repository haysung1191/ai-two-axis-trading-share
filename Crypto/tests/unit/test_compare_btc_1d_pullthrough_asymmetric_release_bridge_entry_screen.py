from __future__ import annotations

from scripts.compare_btc_1d_pullthrough_asymmetric_release_bridge_entry_screen import (
    build_report,
)


def test_pullthrough_asymmetric_release_bridge_entry_screen_marks_ready() -> None:
    report = build_report()

    requirements = report["bridge_entry_requirements"]
    verdict = report["bridge_entry_verdict"]

    assert requirements["promotion_ready"] is True
    assert requirements["contract_health_aligned"] is True
    assert requirements["execution_contract_aligned"] is True
    assert verdict["bridge_entry_ready"] is True
    assert verdict["execution_contract_entry_check_ready"] is True


def test_pullthrough_asymmetric_release_bridge_entry_screen_points_to_execution_contract_check() -> None:
    report = build_report()

    verdict = report["bridge_entry_verdict"]
    context = report["stack_context"]

    assert context["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert verdict["bridge_queue_lane"] == "attack_challenger_queue"
    assert verdict["next_step_now"] == "execution_contract_entry_check"
