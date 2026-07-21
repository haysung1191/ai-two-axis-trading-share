from __future__ import annotations

from scripts.compare_btc_1d_post_spike_attack_backup_rotation_spec import build_report


def test_post_spike_backup_rotation_spec_promotes_challenger_when_gap_and_quality_clear() -> None:
    report = build_report()
    verdict = report["rotation_verdict"]

    assert verdict["challenger_rotation_ready"] is True
    assert verdict["keep_current_backup"] is False
    assert verdict["challenger_status"] == "promote_into_attack_backup_slot"
    assert verdict["next_step_now"] == "run_backup_slot_replacement_review"


def test_post_spike_backup_rotation_spec_still_records_quality_edge() -> None:
    report = build_report()
    metrics = report["rotation_metrics"]

    assert metrics["sharpe_edge_vs_backup"] > 0.0
    assert metrics["mdd_improvement_vs_backup"] > 0.0
    assert metrics["drift_improvement_vs_backup"] > 0.0
    assert metrics["cagr_gap_to_backup"] <= report["rotation_gate"]["allowed_max_cagr_gap"]
