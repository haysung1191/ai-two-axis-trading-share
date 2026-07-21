from __future__ import annotations

from scripts.compare_btc_1d_attack_next_experiment_brief import build_report


def test_attack_next_experiment_brief_keeps_primary_priority_on_trend_dip() -> None:
    report = build_report()

    primary = report["next_experiment_brief"]["primary_attack_experiment"]
    assert primary["label"] == "trend_dip_reversal_breakout_tighter_stop_mid_hold"
    assert primary["family"] == "trend_dip_reversal_breakout"
    assert primary["candidate_stage_status"] == "validated_fail_hold"
    assert primary["success_gate"]["target_role"] == "attack_reopen_candidate"
    assert "outside_bridge_backup_local_repair_neighborhood" in primary["mutation_focus"]
    assert report["attack_post_pivot_context"]["selected_seed_label"] == "volatility_expansion_pullthrough_shorter_hold"


def test_attack_next_experiment_brief_keeps_spike_reversal_as_secondary() -> None:
    report = build_report()

    secondary = report["next_experiment_brief"]["secondary_attack_experiment"]
    assert secondary["label"] == "volatility_spike_reversal_continuation_slower_trend"
    assert secondary["family"] == "volatility_spike_reversal_continuation"
    assert secondary["conversion_context"]["family_verdict"] == "attack_near_miss_hold"
    assert report["experiment_verdict"]["next_attack_reopen_candidate"] is None
    assert report["experiment_verdict"]["next_attack_new_family_seed"] == "volatility_expansion_pullthrough_shorter_hold"
    assert report["experiment_verdict"]["attack_backup_local_repair_next_step"] == "close_local_bridge_window_repairs_and_open_new_axis"
    assert report["experiment_verdict"]["attack_backup_repair_watch_active"] is True
    assert report["experiment_verdict"]["attack_backup_local_repair_closed"] is True
