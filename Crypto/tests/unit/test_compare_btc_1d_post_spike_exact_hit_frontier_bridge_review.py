from __future__ import annotations

import json

import scripts.compare_btc_1d_post_spike_exact_hit_frontier_bridge_review as mod


def test_exact_hit_frontier_bridge_review_requests_new_family_when_gap_stays_open(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)
    monkeypatch.setattr(
        mod,
        "build_cost_repair_review",
        lambda: {
            "cost_repair_verdict": {
                "next_step_now": "search_new_exact_hit_family_or_non_cost_axes",
            }
        },
    )
    (tmp_path / "btc_1d_post_spike_exact_hit_frontier_bridge_batch_20260420T000000Z.json").write_text(
        json.dumps(
            {
                "promoted_backup_cost20_cagr_reference": 0.34639312,
                "best_variant": {
                    "variant_label": "bridge_27_firm",
                    "base_cagr": 0.345,
                    "base_sharpe": 1.81,
                    "base_max_drawdown": 0.095,
                    "sensitivity_max_drift": 0.19,
                    "cost20_cagr_edge_vs_promoted_backup": -0.001,
                    "negative_window_count": 0,
                },
            }
        ),
        encoding="utf-8",
    )

    report = mod.build_report()

    assert report["frontier_bridge_verdict"]["frontier_bridge_found_backup_replacement"] is False
    assert report["frontier_bridge_verdict"]["next_step_now"] == "expand_to_new_post_spike_family_outside_frontier_bridge"


def test_exact_hit_frontier_bridge_review_blocks_when_frontier_has_no_exact_hit(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)
    monkeypatch.setattr(
        mod,
        "build_cost_repair_review",
        lambda: (_ for _ in ()).throw(ValueError("No exact-hit candidate found in frontier payload.")),
    )

    report = mod.build_report()

    assert report["frontier_bridge_verdict"]["frontier_bridge_found_backup_replacement"] is False
    assert report["frontier_bridge_verdict"]["next_step_now"] == "open_new_exit_mechanism_axis"
    assert report["frontier_bridge_reference"]["previous_next_step_now"] == "frontier_exact_hit_missing"
