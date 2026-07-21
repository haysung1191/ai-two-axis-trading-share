from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_post_spike_reopen_candidate_review as mod


def test_reopen_candidate_review_prefers_exact_hit_when_frontier_is_open_for_promotion(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)
    monkeypatch.setattr(
        mod,
        "build_axis_closure_review",
        lambda: {
            "closure_reference": {
                "attack_main": "main_x",
                "promoted_backup": "backup_y",
                "monitoring_candidate": "backup_y::hold36",
            },
            "axis_closure_summary": {
                "all_current_hold36_axes_closed": True,
            },
            "open_blocker_state": {
                "remaining_base_cagr_gap": 0.037,
                "remaining_cost20_cagr_gap": 0.0,
            },
        },
    )

    repair_payload = {
        "repair_winner_profile": {
            "candidate_label": "repair_seed",
            "validation_cagr": 0.32,
            "validation_sharpe": 1.65,
            "validation_max_drawdown": 0.12,
            "walk_forward_sensitivity_max_drift": 0.18,
            "negative_walk_forward_windows": [],
        },
        "repair_winner_stage_verdict": {
            "candidate_stage_ready": True,
        },
    }
    (tmp_path / "btc_1d_post_spike_consolidation_breakout_repair_winner_stage_review_latest.json").write_text(
        json.dumps(repair_payload), encoding="utf-8"
    )

    frontier_payload = {
        "frontier_verdict": {
            "exact_hit_found": True,
        },
        "pareto_frontier": [
            {
                "variant_label": "frontier_a",
                "source": "frontier_batch",
                "base_cagr": 0.35,
                "base_sharpe": 1.8,
                "base_max_drawdown": 0.09,
                "sensitivity_max_drift": 0.19,
                "negative_window_count": 0,
                "rotation_gap_passed": True,
                "drift_guardrail_passed": True,
                "source_json": "analysis_results/frontier_a.json",
            }
        ]
    }
    (tmp_path / "btc_1d_post_spike_exit_tradeoff_frontier_20260419T000000Z.json").write_text(
        json.dumps(frontier_payload), encoding="utf-8"
    )

    report = mod.build_report()

    assert report["reopen_gate"]["preferred_reopen_seed"] == "frontier_a"
    assert report["reopen_gate"]["next_step_now"] == "promote_exact_hit_into_rotation_review"
    assert len(report["reopen_candidates"]) >= 2
