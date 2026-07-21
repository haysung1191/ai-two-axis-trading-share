from __future__ import annotations

import scripts.compare_btc_1d_attack_main_promoted_backup_watchlist as mod
import pytest


def _patch_current_baseline_hold(monkeypatch) -> None:
    monkeypatch.setattr(
        mod,
        "build_main_vs_backup_review",
        lambda: {
            "active_stack_reference": {
                "attack_main": "ratio112_tighter_stop_main",
                "promoted_attack_backup": "bridge_28_relief",
                "monitoring_candidate": "bridge_28_relief::negative_window_repair",
            },
            "main_vs_promoted_backup_metrics": {
                "base_cagr_gap_to_main": 0.10884736,
                "cost20_cagr_gap_to_main": 0.09820287,
                "sharpe_edge_vs_main": 0.24742542,
                "mdd_improvement_vs_main": 0.07016508,
                "drift_improvement_vs_main": -0.15420068,
            },
            "promotion_pressure_gate": {
                "allowed_max_base_cagr_gap": 0.04,
                "allowed_max_cost20_cagr_gap": 0.06,
            },
            "promotion_pressure_verdict": {
                "replace_attack_main_now": False,
                "promoted_backup_has_main_pressure": False,
                "next_step_now": "monitor_promoted_backup_against_active_main",
            },
        },
    )
    monkeypatch.setattr(
        mod,
        "build_reopen_seed_pressure_reconciliation",
        lambda: {
            "verdict": {
                "lane_status": "not_applicable",
                "next_step_now": "monitor_promoted_backup_against_active_main",
                "reason": "No reopen-seed lane applies to bridge repair monitoring.",
            },
            "lane_alignment": {
                "framing_conflict": False,
            },
        },
    )


def test_attack_main_promoted_backup_watchlist_marks_baseline_hold(monkeypatch) -> None:
    _patch_current_baseline_hold(monkeypatch)

    report = mod.build_report()
    snapshot = report["pressure_watch_snapshot"]

    assert snapshot["status_band"] == "baseline_hold"
    assert snapshot["promoted_backup_has_main_pressure"] is False
    assert snapshot["replace_attack_main_now"] is False
    assert snapshot["next_step_now"] == "monitor_promoted_backup_against_active_main"
    assert snapshot["lane_reconciliation_status"] == "not_applicable"
    assert snapshot["lane_framing_conflict"] is False


def test_attack_main_promoted_backup_watchlist_records_remaining_gap_to_open(monkeypatch) -> None:
    _patch_current_baseline_hold(monkeypatch)

    report = mod.build_report()
    snapshot = report["pressure_watch_snapshot"]

    assert snapshot["remaining_base_cagr_gap_to_open"] == pytest.approx(0.06884736)
    assert snapshot["remaining_cost20_cagr_gap_to_open"] == pytest.approx(0.03820287)
