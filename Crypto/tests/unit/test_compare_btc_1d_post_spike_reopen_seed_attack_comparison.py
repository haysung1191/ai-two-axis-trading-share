from __future__ import annotations

import scripts.compare_btc_1d_post_spike_reopen_seed_attack_comparison as mod


def test_reopen_seed_attack_comparison_opens_reopen_lane_for_clean_seed(monkeypatch) -> None:
    monkeypatch.setattr(
        mod,
        "build_attack_stack_screen",
        lambda: {
            "stack_top": {
                "attack_main": "main_a",
                "attack_backup": "backup_b",
                "attack_challenger": "challenger_c",
            },
            "compared_models": [
                {"role": "attack_main", "label": "main_a", "base_cagr": 0.42},
                {"role": "attack_backup", "label": "backup_b", "base_cagr": 0.34},
                {"role": "attack_challenger", "label": "challenger_c", "base_cagr": 0.33},
            ],
        },
    )
    monkeypatch.setattr(
        mod,
        "_seed_cycle",
        lambda: {
            "requested_preferred_seed": "seed_x",
            "requested_backup_seed": "seed_y",
            "cycle_json": "analysis_results/cycle.json",
            "preferred_seed": {
                "seed_label": "seed_x",
                "paper_validation_passed": True,
                "walk_forward_passed": True,
                "negative_window_count": 0,
                "base_cagr": 0.35,
                "base_sharpe": 1.7,
                "base_max_drawdown": 0.10,
                "sensitivity_max_drift": 0.19,
                "validation_json": "a.json",
                "walk_forward_json": "b.json",
            },
            "backup_seed": {
                "seed_label": "seed_y",
                "paper_validation_passed": True,
                "walk_forward_passed": True,
                "negative_window_count": 0,
                "base_cagr": 0.34,
                "base_sharpe": 1.6,
                "base_max_drawdown": 0.11,
                "sensitivity_max_drift": 0.18,
                "validation_json": "c.json",
                "walk_forward_json": "d.json",
            },
        },
    )

    report = mod.build_report()

    assert report["reopen_attack_comparison"]["preferred_seed_has_clean_reopen"] is True
    assert report["reopen_attack_comparison"]["preferred_seed_pressures_active_backup"] is True
    assert report["reopen_attack_comparison"]["next_step_now"] == "open_revalidated_seed_board_comparison"
