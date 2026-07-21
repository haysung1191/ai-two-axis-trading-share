from __future__ import annotations

import scripts.compare_btc_1d_post_spike_exact_hit_attack_stack_review as mod


def test_exact_hit_attack_stack_review_keeps_backup_when_cost20_lags(monkeypatch) -> None:
    monkeypatch.setattr(
        mod,
        "build_attack_stack_screen",
        lambda: {
            "compared_models": [
                {
                    "label": "ratio112_tighter_stop_main",
                    "base_cagr": 0.424,
                    "base_mdd": 0.161,
                    "base_sharpe": 1.56,
                    "sensitivity_max_drift": 0.429,
                    "cost20_cagr": 0.404,
                    "cost20_mdd": 0.161,
                    "cost20_sharpe": 1.49,
                },
                {
                    "label": "post_spike_trend92_depth058_volume105_hold36",
                    "base_cagr": 0.346,
                    "base_mdd": 0.095,
                    "base_sharpe": 1.813,
                    "sensitivity_max_drift": 0.225,
                    "cost20_cagr": 0.346,
                    "cost20_mdd": 0.095,
                    "cost20_sharpe": 1.813,
                },
            ]
        },
    )
    monkeypatch.setattr(
        mod,
        "build_exact_hit_rotation_review",
        lambda: {
            "frontier_exact_hit_review": {
                "preferred_exact_hit_variant_label": "deeper_reset_entry_shape",
                "base_cagr": 0.356,
                "base_sharpe": 1.856,
                "base_max_drawdown": 0.091,
                "sensitivity_max_drift": 0.181,
            },
            "cost20_confirmation_review": {
                "diagnostic_json": "analysis_results/diag.json",
                "base_cagr": 0.344,
                "base_sharpe": 1.800,
                "base_max_drawdown": 0.095,
            },
            "rotation_gate": {
                "rotation_review_ready": True,
            },
        },
    )

    report = mod.build_report()
    verdict = report["exact_hit_stack_verdict"]

    assert verdict["exact_hit_has_backup_pressure"] is True
    assert verdict["promote_exact_hit_to_backup_now"] is False
    assert verdict["keep_current_promoted_backup"] is True
    assert verdict["next_step_now"] == "keep_promoted_backup_and_monitor_exact_hit"


def test_exact_hit_attack_stack_review_opens_backup_replacement_when_cost20_also_improves(monkeypatch) -> None:
    monkeypatch.setattr(
        mod,
        "build_attack_stack_screen",
        lambda: {
            "compared_models": [
                {
                    "label": "ratio112_tighter_stop_main",
                    "base_cagr": 0.424,
                    "base_mdd": 0.161,
                    "base_sharpe": 1.56,
                    "sensitivity_max_drift": 0.429,
                    "cost20_cagr": 0.404,
                    "cost20_mdd": 0.161,
                    "cost20_sharpe": 1.49,
                },
                {
                    "label": "post_spike_trend92_depth058_volume105_hold36",
                    "base_cagr": 0.346,
                    "base_mdd": 0.095,
                    "base_sharpe": 1.813,
                    "sensitivity_max_drift": 0.225,
                    "cost20_cagr": 0.346,
                    "cost20_mdd": 0.095,
                    "cost20_sharpe": 1.813,
                },
            ]
        },
    )
    monkeypatch.setattr(
        mod,
        "build_exact_hit_rotation_review",
        lambda: {
            "frontier_exact_hit_review": {
                "preferred_exact_hit_variant_label": "deeper_reset_entry_shape",
                "base_cagr": 0.360,
                "base_sharpe": 1.860,
                "base_max_drawdown": 0.090,
                "sensitivity_max_drift": 0.180,
            },
            "cost20_confirmation_review": {
                "diagnostic_json": "analysis_results/diag.json",
                "base_cagr": 0.349,
                "base_sharpe": 1.820,
                "base_max_drawdown": 0.094,
            },
            "rotation_gate": {
                "rotation_review_ready": True,
            },
        },
    )

    report = mod.build_report()
    verdict = report["exact_hit_stack_verdict"]

    assert verdict["promote_exact_hit_to_backup_now"] is True
    assert verdict["open_attack_main_replacement_review"] is False
    assert verdict["next_step_now"] == "open_exact_hit_backup_replacement_review"
