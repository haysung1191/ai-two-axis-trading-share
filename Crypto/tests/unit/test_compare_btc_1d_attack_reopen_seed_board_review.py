from __future__ import annotations

import scripts.compare_btc_1d_attack_reopen_seed_board_review as mod


def test_reopen_seed_board_review_promotes_seed_when_it_beats_active_backup(monkeypatch) -> None:
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
                {"role": "attack_backup", "label": "backup_b", "base_cagr": 0.33},
                {"role": "attack_challenger", "label": "challenger_c", "base_cagr": 0.40},
            ],
        },
    )
    monkeypatch.setattr(
        mod,
        "build_reopen_seed_attack_comparison",
        lambda: {
            "reopen_seed_reference": {
                "preferred_seed_now": "seed_x",
                "backup_seed_now": "seed_y",
            },
            "reopen_attack_comparison": {
                "preferred_seed_has_clean_reopen": True,
                "preferred_seed_pressures_active_backup": True,
                "backup_seed_is_viable": True,
            },
            "comparison_metrics": {
                "preferred_seed_base_cagr": 0.34,
                "preferred_seed_base_sharpe": 1.7,
                "preferred_seed_base_mdd": 0.10,
                "preferred_seed_sensitivity_max_drift": 0.19,
                "backup_seed_base_cagr": 0.33,
                "backup_seed_base_sharpe": 1.6,
                "backup_seed_base_mdd": 0.11,
            },
        },
    )

    report = mod.build_report()

    assert report["reopen_seed_board_review"]["preferred_seed_promotes_into_backup"] is True
    assert report["reopen_seed_board_review"]["proposed_attack_backup"] == "seed_x"
    assert report["reopen_seed_board_review"]["next_step_now"] == "open_attack_backup_replacement_from_reopen_seed"
