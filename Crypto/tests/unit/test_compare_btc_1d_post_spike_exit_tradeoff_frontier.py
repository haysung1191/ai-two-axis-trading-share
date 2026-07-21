from __future__ import annotations

import json
from pathlib import Path

from scripts.compare_btc_1d_post_spike_exit_tradeoff_frontier import build_report


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_post_spike_exit_tradeoff_frontier_detects_no_exact_hit(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_guardrail_repair_batch_20260420T000000Z.json",
        {
            "results": [
                {
                    "variant_label": "guardrail_best",
                    "base_cagr": 0.336,
                    "base_sharpe": 1.78,
                    "base_max_drawdown": 0.09,
                    "sensitivity_max_drift": 0.188,
                    "negative_window_count": 0,
                    "idle_window_count": 1,
                    "cagr_gap_to_backup": 0.081,
                    "rotation_gap_passed": False,
                    "drift_guardrail_passed": True,
                    "parameters": {},
                }
            ]
        },
    )
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_cost_robust_cagr_batch_20260420T000001Z.json",
        {
            "results": [
                {
                    "variant_label": "cost_best",
                    "base_cagr": 0.343,
                    "base_sharpe": 1.81,
                    "base_max_drawdown": 0.09,
                    "sensitivity_max_drift": 0.225,
                    "negative_window_count": 0,
                    "idle_window_count": 1,
                    "cagr_gap_to_backup": 0.072,
                    "rotation_gap_passed": True,
                    "drift_guardrail_passed": False,
                    "parameters": {},
                }
            ]
        },
    )
    _write_json(tmp_path / "btc_1d_post_spike_consolidation_breakout_exit_defense_batch_20260420T000002Z.json", {"results": []})
    _write_json(tmp_path / "btc_1d_post_spike_consolidation_breakout_hold_stop_coupling_batch_20260420T000003Z.json", {"results": []})

    import scripts.compare_btc_1d_post_spike_exit_tradeoff_frontier as mod

    original = mod.ANALYSIS_DIR
    mod.ANALYSIS_DIR = tmp_path
    try:
        report = build_report()
    finally:
        mod.ANALYSIS_DIR = original

    assert report["frontier_summary"]["exact_hit_found"] is False
    assert report["frontier_verdict"]["next_step_now"] == "open_new_exit_mechanism_axis"


def test_post_spike_exit_tradeoff_frontier_detects_exact_hit(tmp_path: Path) -> None:
    payload = {
        "results": [
            {
                "variant_label": "exact_hit",
                "base_cagr": 0.339,
                "base_sharpe": 1.79,
                "base_max_drawdown": 0.09,
                "sensitivity_max_drift": 0.19,
                "negative_window_count": 0,
                "idle_window_count": 1,
                "cagr_gap_to_backup": 0.076,
                "rotation_gap_passed": True,
                "drift_guardrail_passed": True,
                "parameters": {},
            }
        ]
    }
    _write_json(tmp_path / "btc_1d_post_spike_consolidation_breakout_guardrail_repair_batch_20260420T000000Z.json", payload)
    _write_json(tmp_path / "btc_1d_post_spike_consolidation_breakout_cost_robust_cagr_batch_20260420T000001Z.json", {"results": []})
    _write_json(tmp_path / "btc_1d_post_spike_consolidation_breakout_exit_defense_batch_20260420T000002Z.json", {"results": []})
    _write_json(tmp_path / "btc_1d_post_spike_consolidation_breakout_hold_stop_coupling_batch_20260420T000003Z.json", {"results": []})

    import scripts.compare_btc_1d_post_spike_exit_tradeoff_frontier as mod

    original = mod.ANALYSIS_DIR
    mod.ANALYSIS_DIR = tmp_path
    try:
        report = build_report()
    finally:
        mod.ANALYSIS_DIR = original

    assert report["frontier_summary"]["exact_hit_found"] is True
    assert report["frontier_verdict"]["next_step_now"] == "promote_exact_hit_into_rotation_review"
