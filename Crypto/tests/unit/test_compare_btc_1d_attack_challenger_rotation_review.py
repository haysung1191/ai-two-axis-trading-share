from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_attack_challenger_rotation_review as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_attack_challenger_rotation_review_prefers_hold36_same_profile_upgrade(
    tmp_path: Path,
) -> None:
    _write_json(
        tmp_path / "btc_1d_post_spike_idle_window_recovery_candidates_latest.json",
        {
            "active_challenger_reference": {
                "label": "post_spike_trend864_depth055_volume100_hold32",
                "candidate_label": "post_spike_consolidation_breakout_trend864_depth055_volume100_hold32",
                "paper_validation_cagr": 0.2941,
                "paper_validation_sharpe": 1.5398,
                "paper_validation_max_drawdown": 0.1352,
                "negative_walk_forward_windows": [],
                "idle_walk_forward_windows": [2],
                "sensitivity_max_drift": 0.1724,
            },
            "idle_window_recovery_candidates": [
                {
                    "variant_label": "trend864_depth055_volume100_hold32",
                    "base_cagr": 0.3023,
                    "base_sharpe": 1.5796,
                    "base_max_drawdown": 0.1267,
                    "sensitivity_max_drift": 0.1724,
                    "negative_windows": [],
                    "idle_windows": [2],
                    "cagr_delta_vs_active": 0.0082,
                    "sharpe_delta_vs_active": 0.0398,
                },
                {
                    "variant_label": "trend864_depth055_volume100_hold36",
                    "base_cagr": 0.3340,
                    "base_sharpe": 1.6886,
                    "base_max_drawdown": 0.1267,
                    "sensitivity_max_drift": 0.2020,
                    "negative_windows": [],
                    "idle_windows": [2],
                    "cagr_delta_vs_active": 0.0399,
                    "sharpe_delta_vs_active": 0.1488,
                }
            ],
            "idle_window_recovery_verdict": {
                "top_same_profile_variant": "trend864_depth055_volume100_hold36",
                "recommend_rotation_review": True,
                "next_step_now": "validate_top_idle_window_recovery_variant_against_active_challenger",
                "reason": "ok",
            },
        },
    )

    report = mod.build_report(analysis_dir=tmp_path)

    verdict = report["rotation_review"]
    assert verdict["open_rotation_review"] is True
    assert verdict["proposed_attack_challenger"] == "trend864_depth055_volume100_hold36"
    assert verdict["approve_challenger_rotation_now"] is False
    assert report["rotation_gate"]["blocking_reasons"] == ["drift_not_worse"]
    assert verdict["next_step_now"] == "repair_hold36_drift_gap_before_rotation"


def test_attack_challenger_rotation_review_main_writes_latest_aliases(
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
                "paper_validation_cagr": 0.2941,
                "paper_validation_sharpe": 1.5398,
                "paper_validation_max_drawdown": 0.1352,
                "negative_walk_forward_windows": [],
                "idle_walk_forward_windows": [2],
            },
            "rotation_candidate": {
                "variant_label": "trend864_depth055_volume100_hold36",
                "base_cagr": 0.3340,
                "base_sharpe": 1.6886,
                "base_max_drawdown": 0.1267,
                "sensitivity_max_drift": 0.2020,
                "cagr_delta_vs_active": 0.0399,
                "sharpe_delta_vs_active": 0.1488,
                "max_drawdown_delta_vs_active": 0.0085,
                "drift_delta_vs_active": -0.0296,
                "same_negative_profile_as_active": True,
                "same_idle_profile_as_active": True,
            },
            "rotation_review": {
                "open_rotation_review": True,
                "keep_attack_main_unchanged": True,
                "keep_attack_backup_unchanged": True,
                "keep_current_challenger_live_until_validation": True,
                "current_attack_challenger": "post_spike_trend864_depth055_volume100_hold32",
                "proposed_attack_challenger": "trend864_depth055_volume100_hold36",
                "approve_challenger_rotation_now": False,
                "manual_review_required": True,
                "next_step_now": "repair_hold36_drift_gap_before_rotation",
                "reason": "ok",
            },
            "rotation_gate": {
                "gate_open": True,
                "approve_challenger_rotation_now": False,
                "manual_review_required": True,
                "blocking_reasons": ["drift_not_worse"],
                "checks": [],
                "next_step_now": "repair_hold36_drift_gap_before_rotation",
            },
            "decision_summary": [],
        },
    )

    exit_code = mod.main()

    assert exit_code == 0
    latest_json = tmp_path / "btc_1d_attack_challenger_rotation_review_latest.json"
    latest_md = tmp_path / "btc_1d_attack_challenger_rotation_review_md_latest.md"
    assert latest_json.exists()
    assert latest_md.exists()
