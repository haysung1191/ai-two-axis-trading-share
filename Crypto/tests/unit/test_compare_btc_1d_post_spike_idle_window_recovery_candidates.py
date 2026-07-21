from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_post_spike_idle_window_recovery_candidates as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_post_spike_idle_window_recovery_candidates_prefers_stronger_same_profile_variant(
    tmp_path: Path,
) -> None:
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_candidate_stage_review_latest.json",
        {
            "candidate_profile": {
                "label": "post_spike_consolidation_breakout_trend864_depth055_volume100_hold32",
                "paper_validation_cagr": 0.2941,
                "paper_validation_sharpe": 1.5398,
                "paper_validation_max_drawdown": 0.1352,
                "walk_forward_sensitivity_max_drift": 0.1724,
                "negative_walk_forward_windows": [],
                "idle_walk_forward_windows": [2],
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch_latest.json",
        {
            "repair_focus": {
                "active_anchor": "post_spike_consolidation_breakout_trend864_depth055_volume100_hold32",
                "selected_variant_labels": [
                    "trend864_depth055_volume100_hold32",
                    "trend864_depth055_volume100_hold36",
                ],
            },
            "results": [
                {
                    "variant_label": "trend864_depth055_volume100_hold32",
                    "base_cagr": 0.3023,
                    "base_sharpe": 1.5796,
                    "base_max_drawdown": 0.1267,
                    "sensitivity_max_drift": 0.1724,
                    "negative_windows": [],
                    "idle_windows": [2],
                },
                {
                    "variant_label": "trend864_depth055_volume100_hold36",
                    "base_cagr": 0.3340,
                    "base_sharpe": 1.6886,
                    "base_max_drawdown": 0.1267,
                    "sensitivity_max_drift": 0.2020,
                    "negative_windows": [],
                    "idle_windows": [2],
                },
            ]
        },
    )

    report = mod.build_report(analysis_dir=tmp_path)

    verdict = report["idle_window_recovery_verdict"]
    assert verdict["top_same_profile_variant"] == "trend864_depth055_volume100_hold36"
    assert verdict["recommend_rotation_review"] is True
    assert (
        verdict["next_step_now"]
        == "validate_top_idle_window_recovery_variant_against_active_challenger"
    )


def test_post_spike_idle_window_recovery_candidates_blocks_stale_repair_batch_against_new_active(
    tmp_path: Path,
) -> None:
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_candidate_stage_review_latest.json",
        {
            "candidate_profile": {
                "label": "post_spike_consolidation_breakout_trend960_depth055_volume100_hold36",
                "paper_validation_cagr": 0.3010,
                "paper_validation_sharpe": 1.6408,
                "paper_validation_max_drawdown": 0.1267,
                "walk_forward_sensitivity_max_drift": 0.1325,
                "negative_walk_forward_windows": [],
                "idle_walk_forward_windows": [2],
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch_latest.json",
        {
            "repair_focus": {
                "active_anchor": "post_spike_consolidation_breakout_trend96_depth055_volume104_hold36",
                "selected_variant_labels": [
                    "trend864_depth055_volume100_hold32",
                    "trend864_depth055_volume100_hold36",
                ],
            },
            "results": [
                {
                    "variant_label": "trend864_depth055_volume100_hold36",
                    "base_cagr": 0.3340,
                    "base_sharpe": 1.6886,
                    "base_max_drawdown": 0.1267,
                    "sensitivity_max_drift": 0.2020,
                    "negative_windows": [],
                    "idle_windows": [2],
                }
            ],
        },
    )

    report = mod.build_report(analysis_dir=tmp_path)

    assert report["active_challenger_reference"]["sensitivity_max_drift"] == 0.1325
    assert report["repair_batch_context"]["repair_batch_matches_active_candidate"] is False
    verdict = report["idle_window_recovery_verdict"]
    assert verdict["recommend_rotation_review"] is False
    assert verdict["next_step_now"] == "expand_post_spike_trend_family_to_recover_idle_windows"


def test_post_spike_idle_window_recovery_candidates_main_writes_latest_aliases(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)
    monkeypatch.setattr(
        mod,
        "build_report",
        lambda analysis_dir=tmp_path: {
            "active_challenger_reference": {
                "label": "post_spike_trend864_depth055_volume100_hold32",
                "candidate_label": "post_spike_consolidation_breakout_trend864_depth055_volume100_hold32",
                "paper_validation_cagr": 0.2941,
                "paper_validation_sharpe": 1.5398,
                "paper_validation_max_drawdown": 0.1352,
                "negative_walk_forward_windows": [],
                "idle_walk_forward_windows": [2],
            },
            "repair_batch_context": {
                "active_anchor": "post_spike_consolidation_breakout_trend864_depth055_volume100_hold32",
                "repair_batch_matches_active_candidate": True,
                "selected_variant_labels": [],
            },
            "idle_window_recovery_candidates": [],
            "idle_window_recovery_verdict": {
                "top_same_profile_variant": "trend864_depth055_volume100_hold36",
                "recommend_rotation_review": True,
                "next_step_now": "validate_top_idle_window_recovery_variant_against_active_challenger",
                "reason": "ok",
            },
            "decision_summary": [],
        },
    )

    exit_code = mod.main()

    assert exit_code == 0
    latest_json = tmp_path / "btc_1d_post_spike_idle_window_recovery_candidates_latest.json"
    latest_md = tmp_path / "btc_1d_post_spike_idle_window_recovery_candidates_md_latest.md"
    assert latest_json.exists()
    assert latest_md.exists()
