from __future__ import annotations

from scripts.compare_btc_1d_attack_experiment_spec import build_report


def test_attack_experiment_spec_keeps_trend_dip_as_primary() -> None:
    report = build_report()

    spec = report["experiment_spec"]
    assert spec["primary_label"] == "trend_dip_reversal_breakout_tighter_stop_mid_hold"
    assert spec["primary_family"] == "trend_dip_reversal_breakout"
    assert spec["secondary_label"] == "volatility_spike_reversal_continuation_slower_trend"
    attack_seed = report["attack_rule_seed"]
    assert attack_seed["available"] is True
    assert attack_seed["recommended_attack_rule_seed"]["trend_ema_window"] == 96.0


def test_attack_experiment_spec_keeps_expected_runner_sequence() -> None:
    report = build_report()

    mutation_axes = report["mutation_plan"]["primary_mutation_axes"]
    validation_sequence = report["mutation_plan"]["validation_sequence"]

    assert mutation_axes[0]["axis"] == "exit_shape"
    assert "run_btc_1d_trend_dip_reversal_breakout_exit_compression_batch.py" in mutation_axes[0]["runner"]
    assert "--apply-attack-seed" in mutation_axes[0]["runner"]
    assert mutation_axes[0]["seed_alignment"]["max_hold_bars"] == 34.0
    assert mutation_axes[1]["axis"] == "exit_symmetry"
    assert "run_btc_1d_trend_dip_reversal_breakout_exit_symmetry_batch.py" in mutation_axes[1]["runner"]
    assert mutation_axes[1]["seed_alignment"]["min_volume_ratio"] == 1.08
    assert validation_sequence[0]["step"] == "candidate_validation"
    assert "validate_btc_1d_trend_dip_reversal_breakout_tsmh_candidate.py" in validation_sequence[0]["runner"]
    assert validation_sequence[1]["step"] == "walk_forward"
    assert validation_sequence[2]["step"] == "friction"
