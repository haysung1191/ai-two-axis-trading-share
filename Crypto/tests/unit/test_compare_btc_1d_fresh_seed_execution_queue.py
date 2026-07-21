from __future__ import annotations

from scripts.compare_btc_1d_fresh_seed_execution_queue import build_report


def test_fresh_seed_execution_queue_runs_primary_seed_first() -> None:
    report = build_report()

    summary = report["queue_summary"]
    first = report["execution_queue"][0]
    verdict = report["queue_verdict"]

    assert summary["queue_mode"] == "fresh_seed_attack_restart"
    assert summary["primary_seed_family"] == "post_spike_consolidation_breakout"
    assert summary["secondary_seed_family"] == "impulse_flag_breakout"
    assert summary["next_step_now"] == "reopen_batch"
    assert "run_btc_1d_post_spike_consolidation_breakout_high_cagr_batch.py" in summary["next_runner_now"]
    assert first["status"] == "run_now"
    assert verdict["active_lane"] == "post_spike_consolidation_breakout"


def test_fresh_seed_execution_queue_keeps_secondary_on_standby() -> None:
    report = build_report()

    queue = report["execution_queue"]
    standby_rows = [row for row in queue if row["family"] == "impulse_flag_breakout"]
    primary_followups = [row for row in queue if row["family"] == "post_spike_consolidation_breakout"]

    assert standby_rows
    assert standby_rows[0]["status"] == "standby"
    assert all(row["status"].startswith("after_") for row in primary_followups[1:])
    assert any("validate_btc_1d_post_spike_consolidation_breakout_candidate.py" in row["runner"] for row in primary_followups)
