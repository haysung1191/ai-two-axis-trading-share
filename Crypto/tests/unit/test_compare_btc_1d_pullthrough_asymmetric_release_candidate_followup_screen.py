from __future__ import annotations

from scripts.compare_btc_1d_pullthrough_asymmetric_release_candidate_followup_screen import build_report


def test_pullthrough_asymmetric_release_candidate_followup_screen_marks_ready() -> None:
    report = build_report()

    candidate = report["candidate"]
    verdict = report["followup_verdict"]

    assert candidate["paper_validation_decision"] == "PASS"
    assert report["followup_status"]["friction_final_decision"] == "continue"
    assert verdict["candidate_stage_followup_ready"] is True


def test_pullthrough_asymmetric_release_candidate_followup_screen_points_to_bridge() -> None:
    report = build_report()

    verdict = report["followup_verdict"]

    assert verdict["next_step"] == "promotion_bridge_or_execution_contract_entry"
