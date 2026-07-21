from __future__ import annotations

from scripts.compare_btc_1d_attack_main_pressure_escalation_review import build_report


def test_attack_main_pressure_escalation_review_identifies_base_gap_as_primary_blocker() -> None:
    report = build_report()
    status = report["watch_status"]

    assert status["escalation_ready"] is False
    assert status["primary_blocker"] == "base_cagr_gap"
    assert "base_cagr_gap" in status["open_bottlenecks"]
    assert "cost20_cagr_gap" not in status["open_bottlenecks"]
    assert status["next_step_now"] == "continue_pressure_watch"


def test_attack_main_pressure_escalation_review_quality_checks_are_already_green() -> None:
    report = build_report()
    checks = report["escalation_checks"]

    assert checks["quality_edge_sharpe_ready"] is True
    assert checks["quality_edge_mdd_ready"] is True
    assert checks["quality_edge_drift_ready"] is True
    assert checks["lane_reconciliation_ready"] is True
    assert checks["base_cagr_gap_ready"] is False
    assert checks["cost20_cagr_gap_ready"] is True
