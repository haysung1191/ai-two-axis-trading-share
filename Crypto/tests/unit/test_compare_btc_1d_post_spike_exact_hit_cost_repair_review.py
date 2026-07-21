from __future__ import annotations

import json

import scripts.compare_btc_1d_post_spike_exact_hit_cost_repair_review as mod


def test_exact_hit_cost_repair_review_marks_axis_closed_when_anchor_stays_best(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)
    monkeypatch.setattr(
        mod,
        "build_attack_stack_review",
        lambda: {
            "exact_hit_stack_verdict": {
                "next_step_now": "keep_promoted_backup_and_monitor_exact_hit",
            }
        },
    )
    (tmp_path / "btc_1d_post_spike_exact_hit_cost_repair_batch_20260420T000000Z.json").write_text(
        json.dumps(
            {
                "exact_hit_candidate_label": "seed_a",
                "promoted_backup_cost20_cagr_reference": 0.346,
                "best_variant": {
                    "variant_label": "exact_hit_anchor",
                    "base_cagr": 0.344,
                    "base_sharpe": 1.80,
                    "base_max_drawdown": 0.095,
                    "sensitivity_max_drift": 0.183,
                    "cost20_cagr_edge_vs_promoted_backup": -0.002,
                    "negative_window_count": 0,
                },
                "results": [
                    {
                        "variant_label": "exact_hit_anchor",
                        "cost20_cagr_edge_vs_promoted_backup": -0.002,
                    },
                    {
                        "variant_label": "stop22",
                        "cost20_cagr_edge_vs_promoted_backup": -0.006,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    report = mod.build_report()

    assert report["cost_repair_verdict"]["cost_repair_axis_closed"] is True
    assert report["cost_repair_verdict"]["promote_exact_hit_to_backup_now"] is False
    assert report["cost_repair_verdict"]["next_step_now"] == "search_new_exact_hit_family_or_non_cost_axes"
