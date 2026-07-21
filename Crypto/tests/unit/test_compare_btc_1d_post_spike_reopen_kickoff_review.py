from __future__ import annotations

import scripts.compare_btc_1d_post_spike_reopen_kickoff_review as mod


def test_reopen_kickoff_review_picks_preferred_and_backup_seed(monkeypatch) -> None:
    monkeypatch.setattr(
        mod,
        "build_reopen_candidate_review",
        lambda: {
            "reopen_reference": {
                "attack_main": "main_x",
                "promoted_backup": "backup_y",
                "monitoring_candidate": "backup_y::hold36",
                "current_hold36_line_closed": True,
            },
            "reopen_gate": {
                "preferred_reopen_seed": "seed_a",
                "next_step_now": "promote_exact_hit_into_rotation_review",
            },
            "reopen_candidates": [
                {
                    "candidate_label": "seed_a",
                    "source": "entry_shape",
                    "base_cagr": 0.355,
                    "base_sharpe": 1.85,
                    "base_max_drawdown": 0.09,
                    "sensitivity_max_drift": 0.18,
                    "negative_window_count": 0,
                    "candidate_stage_ready": True,
                    "drift_guardrail_passed": True,
                    "exact_hit": True,
                },
                {
                    "candidate_label": "seed_b",
                    "source": "guardrail_repair",
                    "base_cagr": 0.33,
                    "base_sharpe": 1.78,
                    "base_max_drawdown": 0.09,
                    "sensitivity_max_drift": 0.19,
                    "negative_window_count": 0,
                    "candidate_stage_ready": True,
                    "drift_guardrail_passed": True,
                },
            ],
        },
    )

    report = mod.build_report()

    assert report["reopen_kickoff"]["preferred_seed_label"] == "seed_a"
    assert report["reopen_kickoff"]["backup_seed_label"] == "seed_b"
    assert report["reopen_kickoff"]["preferred_seed_class"] == "frontier_exact_hit_seed"
    assert report["reopen_kickoff"]["next_step_now"] == "launch_exact_hit_rotation_review"
