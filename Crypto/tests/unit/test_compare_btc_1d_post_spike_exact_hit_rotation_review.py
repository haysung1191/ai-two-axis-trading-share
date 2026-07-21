from __future__ import annotations

import json

import scripts.compare_btc_1d_post_spike_exact_hit_rotation_review as mod


def test_exact_hit_rotation_review_marks_candidate_ready_when_frontier_and_cost20_confirm(monkeypatch) -> None:
    report = {
        "kickoff_reference": {
            "attack_main": "main_x",
            "promoted_backup": "backup_y",
            "monitoring_candidate": "backup_y",
        },
        "reopen_kickoff": {
            "backup_seed_source": "repair_review",
            "backup_seed_class": "repair_winner_seed",
            "next_step_now": "launch_exact_hit_rotation_review",
            "execution_order": [
                "promote::seed_a",
                "rotation_review::seed_a",
                "compare_against::seed_b",
            ],
        },
        "preferred_seed_metrics": {
            "candidate_label": "seed_a",
            "base_cagr": 0.355,
            "base_sharpe": 1.85,
            "base_max_drawdown": 0.09,
            "sensitivity_max_drift": 0.18,
            "negative_window_count": 0,
        },
        "backup_seed_metrics": {
            "candidate_label": "seed_b",
            "base_cagr": 0.338,
            "base_sharpe": 1.71,
            "base_max_drawdown": 0.126,
            "sensitivity_max_drift": 0.29,
            "negative_window_count": 0,
        },
    }

    frontier_payload = {
        "targets": {
            "max_cagr_gap_to_backup": 0.08,
            "max_sensitivity_drift": 0.2,
            "max_negative_window_count": 0,
        },
        "pareto_frontier": [
            {
                "source": "entry_shape",
                "variant_label": "seed_a",
                "base_cagr": 0.355,
                "base_sharpe": 1.85,
                "base_max_drawdown": 0.09,
                "sensitivity_max_drift": 0.18,
                "cagr_gap_to_backup": 0.059,
                "negative_window_count": 0,
                "idle_window_count": 1,
                "rotation_gap_passed": True,
                "drift_guardrail_passed": True,
                "parameters": {
                    "trend_ema_window": 92,
                },
            }
        ],
    }

    diagnostic_payload = {
        "config": {
            "candidate_label": "post_spike_entry_shape::seed_a::20bps_check",
            "fee_bps": 20.0,
            "slippage_bps": 20.0,
        },
        "base_metrics": {
            "cagr": 0.344,
            "sharpe": 1.80,
            "max_drawdown": 0.095,
        },
        "walk_forward_sensitivity": {
            "sensitivity_max_drift": 0.183,
            "negative_windows": [],
            "idle_windows": [2],
        },
    }

    monkeypatch.setattr(mod, "build_reopen_kickoff_review", lambda: report)
    monkeypatch.setattr(mod, "_load_frontier", lambda: (frontier_payload, mod.Path("analysis_results/frontier.json")))
    monkeypatch.setattr(
        mod,
        "_load_cost20_confirmation",
        lambda preferred_label: (
            diagnostic_payload,
            mod.Path("analysis_results/diag.json"),
        ),
    )

    built = mod.build_report()

    assert built["rotation_review_reference"]["preferred_exact_hit_candidate"] == "seed_a"
    assert built["rotation_gate"]["rotation_review_ready"] is True
    assert built["rotation_gate"]["promote_exact_hit_now"] is True
    assert built["rotation_gate"]["next_step_now"] == "compare_exact_hit_against_attack_main_and_promoted_backup"
    assert built["cost20_confirmation_review"]["cost20_guardrail_passed"] is True


def test_exact_hit_rotation_review_stays_unready_without_cost20_confirmation(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)
    monkeypatch.setattr(
        mod,
        "build_reopen_kickoff_review",
        lambda: {
            "kickoff_reference": {
                "attack_main": "main_x",
                "promoted_backup": "backup_y",
                "monitoring_candidate": "backup_y",
            },
            "reopen_kickoff": {
                "backup_seed_source": "repair_review",
                "backup_seed_class": "repair_winner_seed",
                "next_step_now": "launch_exact_hit_rotation_review",
                "execution_order": [],
            },
            "preferred_seed_metrics": {
                "candidate_label": "seed_a",
                "base_cagr": 0.355,
                "base_sharpe": 1.85,
                "base_max_drawdown": 0.09,
                "sensitivity_max_drift": 0.18,
                "negative_window_count": 0,
            },
            "backup_seed_metrics": {
                "candidate_label": "seed_b",
                "base_cagr": 0.338,
                "base_sharpe": 1.71,
                "base_max_drawdown": 0.126,
                "sensitivity_max_drift": 0.29,
                "negative_window_count": 0,
            },
        },
    )
    (tmp_path / "btc_1d_post_spike_exit_tradeoff_frontier_20260420T000000Z.json").write_text(
        json.dumps(
            {
                "targets": {
                    "max_cagr_gap_to_backup": 0.08,
                    "max_sensitivity_drift": 0.2,
                    "max_negative_window_count": 0,
                },
                "pareto_frontier": [
                    {
                        "source": "entry_shape",
                        "variant_label": "seed_a",
                        "base_cagr": 0.355,
                        "base_sharpe": 1.85,
                        "base_max_drawdown": 0.09,
                        "sensitivity_max_drift": 0.18,
                        "cagr_gap_to_backup": 0.059,
                        "negative_window_count": 0,
                        "idle_window_count": 1,
                        "rotation_gap_passed": True,
                        "drift_guardrail_passed": True,
                        "parameters": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    built = mod.build_report()

    assert built["rotation_gate"]["rotation_review_ready"] is False
    assert built["rotation_gate"]["promote_exact_hit_now"] is False
    assert built["rotation_gate"]["next_step_now"] == "repair_exact_hit_rotation_review_inputs"
    assert built["cost20_confirmation_review"]["cost20_confirmation_available"] is False
