from __future__ import annotations

from scripts.compare_btc_1d_attack_execution_queue import build_report


def test_attack_execution_queue_runs_primary_compression_first() -> None:
    report = build_report()

    summary = report["queue_summary"]
    first = report["execution_queue"][0]
    second = report["execution_queue"][1]

    assert summary["next_step_now"] == "hold_primary_anchor"
    assert summary["trend_dip_validation_next_step"] == "run_exit_symmetry_batch"
    assert summary["next_runner_now"] == "hold_current_anchor_no_further_primary_mutation"
    assert summary["attack_backup_label"] == "bridge_28_relief"
    assert summary["attack_backup_negative_window_watch"] is True
    assert summary["attack_backup_local_repair_next_step"] == "close_local_bridge_window_repairs_and_open_new_axis"
    assert summary["attack_seed_available"] is True
    assert summary["attack_seed_params"]["trend_ema_window"] == 96.0
    assert first["status"] == "completed_fail_validation"
    assert second["status"] == "completed_hold_anchor"


def test_attack_execution_queue_blocks_secondary_branch_until_friction_gate() -> None:
    report = build_report()

    summary = report["queue_summary"]
    verdict = report["queue_verdict"]
    secondary = report["execution_queue"][-1]

    assert summary["secondary_branch_status"] == "secondary_upside_branch_only"
    assert summary["secondary_branch_blocked"] is True
    assert verdict["block_secondary_until"] == "friction_pass_and_candidate_stage_promotion"
    assert secondary["status"] == "blocked"
    assert "hold the current anchor" in verdict["reason"]
