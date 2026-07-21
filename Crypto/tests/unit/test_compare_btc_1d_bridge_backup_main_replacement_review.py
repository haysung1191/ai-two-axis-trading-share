from __future__ import annotations

import scripts.compare_btc_1d_bridge_backup_main_replacement_review as mod


def test_bridge_backup_main_replacement_review_keeps_main_when_base_gap_is_still_large(monkeypatch) -> None:
    monkeypatch.setattr(
        mod,
        "build_backup_replacement_review",
        lambda: {
            "replacement_reference": {
                "attack_main": "ratio112_tighter_stop_main",
                "new_attack_backup": "bridge_28_relief",
                "previous_promoted_backup": "post_spike_trend92_depth058_volume105_hold36",
                "current_attack_challenger": "post_spike_walk_forward_repair::trend84_depth055_volume104_hold34",
            },
            "backup_replacement_verdict": {
                "backup_replacement_ready": True,
            },
        },
    )
    monkeypatch.setattr(
        mod,
        "build_main_vs_backup_review",
        lambda: {
            "main_vs_promoted_backup_metrics": {
                "base_cagr_gap_to_main": 0.07788175,
                "cost20_cagr_gap_to_main": 0.05723624,
                "sharpe_edge_vs_main": 0.25185224,
                "mdd_improvement_vs_main": 0.06568218,
                "drift_improvement_vs_main": 0.29712846,
            },
            "promoted_backup_risk_watch": {
                "failed_gates": ["negative_walk_forward_window"],
                "negative_window_watch": True,
                "negative_walk_forward_windows": [5],
                "idle_walk_forward_windows": [2],
            },
            "promotion_pressure_gate": {
                "required_min_sharpe_edge": 0.15,
                "required_min_mdd_improvement": 0.05,
                "required_min_drift_improvement": 0.15,
                "allowed_max_base_cagr_gap": 0.04,
                "allowed_max_cost20_cagr_gap": 0.06,
            },
        },
    )

    report = mod.build_report()

    assert report["main_replacement_watch"]["quality_pressure_ready"] is True
    assert report["main_replacement_watch"]["cost20_gap_open"] is True
    assert report["main_replacement_watch"]["base_gap_open"] is False
    assert report["main_replacement_watch"]["negative_window_watch"] is True
    assert report["main_replacement_watch"]["negative_walk_forward_windows"] == [5]
    assert report["main_replacement_watch"]["blocking_reasons"] == [
        "negative_walk_forward_window",
        "base_cagr_gap",
    ]
    assert report["main_replacement_watch"]["primary_blocker"] == "negative_walk_forward_window"
    assert report["main_replacement_verdict"]["open_attack_main_replacement_review"] is False
    assert report["main_replacement_verdict"]["next_step_now"] == "monitor_bridge_backup_against_attack_main"


def test_bridge_backup_main_replacement_review_reports_missing_artifact_blocker(monkeypatch) -> None:
    monkeypatch.setattr(
        mod,
        "build_backup_replacement_review",
        lambda: (_ for _ in ()).throw(
            FileNotFoundError("No analysis artifact matched pattern: btc_1d_post_spike_reopen_seed_cycle_*.json")
        ),
    )

    report = mod.build_report()

    assert report["bridge_monitor_reference"]["bridge_backup"] == "bridge_28_relief"
    assert report["main_replacement_watch"]["primary_blocker"] == "missing_required_analysis_artifact"
    assert report["main_replacement_watch"]["negative_window_watch"] is True
    assert report["main_replacement_verdict"]["open_attack_main_replacement_review"] is False
    assert report["main_replacement_verdict"]["keep_attack_main"] is True
    assert report["main_replacement_verdict"]["next_step_now"] == "regenerate_missing_bridge_review_artifacts"


def test_bridge_backup_main_replacement_review_reports_missing_snapshot_blocker(monkeypatch) -> None:
    monkeypatch.setattr(
        mod,
        "build_backup_replacement_review",
        lambda: (_ for _ in ()).throw(KeyError("post_spike_walk_forward_repair::trend84_depth055_volume104_hold34")),
    )

    report = mod.build_report()

    assert report["main_replacement_watch"]["primary_blocker"] == "missing_required_analysis_artifact"
    assert "trend84_depth055_volume104_hold34" in report["main_replacement_watch"]["missing_artifact"]
    assert report["main_replacement_verdict"]["open_attack_main_replacement_review"] is False
