from __future__ import annotations

from scripts.compare_btc_1d_attack_main_promoted_backup_review import build_report


def test_attack_main_promoted_backup_review_keeps_main_when_cagr_gap_is_still_large() -> None:
    report = build_report()
    verdict = report["promotion_pressure_verdict"]
    risk_watch = report["promoted_backup_risk_watch"]

    assert verdict["promoted_backup_has_main_pressure"] is False
    assert verdict["promoted_backup_clean_monitoring_ready"] is False
    assert verdict["replace_attack_main_now"] is False
    assert verdict["keep_attack_main"] is True
    assert verdict["next_step_now"] == "monitor_promoted_backup_against_active_main"
    assert risk_watch["negative_window_watch"] is False
    assert risk_watch["negative_walk_forward_windows"] == []


def test_attack_main_promoted_backup_review_records_quality_edge_vs_main() -> None:
    report = build_report()
    metrics = report["main_vs_promoted_backup_metrics"]

    assert metrics["sharpe_edge_vs_main"] > 0.0
    assert metrics["mdd_improvement_vs_main"] > 0.0
    assert metrics["drift_improvement_vs_main"] < 0.0
    assert metrics["base_cagr_gap_to_main"] > report["promotion_pressure_gate"]["allowed_max_base_cagr_gap"]
    assert metrics["cost20_cagr_gap_to_main"] > report["promotion_pressure_gate"]["allowed_max_cost20_cagr_gap"]


def test_attack_main_promoted_backup_review_monitors_current_reopen_seed_backup() -> None:
    report = build_report()

    assert (
        report["active_stack_reference"]["monitoring_candidate"]
        == "bridge_28_relief::negative_window_repair"
    )
    assert report["recovery_candidate_review"] is None
    assert report["bridge_negative_window_repair_review"]["negative_window_repair_passed"] is True
    assert report["promoted_backup_risk_watch"]["failed_gates"] == []
