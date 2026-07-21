from __future__ import annotations

import json
from pathlib import Path

import scripts.publish_btc_1d_approved_post_spike_candidate_artifacts as mod
from scripts.compare_btc_1d_attack_challenger_rotation_application_readiness import build_report as build_readiness


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_publish_approved_post_spike_candidate_artifacts_unblocks_readiness(tmp_path: Path, monkeypatch) -> None:
    _write_json(
        tmp_path / "btc_1d_attack_challenger_promotion_review_latest.json",
        {
            "promotion_review": {
                "approved_attack_challenger": "depth055_volume100_hold36",
                "promote_attack_challenger_now": True,
            },
            "approved_candidate_snapshot": {
                "base_cagr": 0.3010,
                "base_sharpe": 1.6408,
                "base_max_drawdown": 0.1267,
                "sensitivity_max_drift": 0.1325,
                "failed_gates": [],
                "overfitting_flags": [],
                "parameters": {
                    "trend_ema_window": 96,
                    "spike_lookback": 24,
                    "min_spike_pct": 0.085,
                    "consolidation_window": 7,
                    "max_consolidation_depth_pct": 0.055,
                    "breakout_buffer_pct": 0.002,
                    "volume_lookback": 20,
                    "min_volume_ratio": 1.0,
                    "stop_ema_window": 20,
                    "max_hold_bars": 36,
                },
            },
        },
    )
    _write_json(
        tmp_path / "btc_1d_attack_challenger_validation_review_latest.json",
        {
            "active_challenger_reference": {
                "idle_walk_forward_windows": [2],
            }
        },
    )

    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)
    assert mod.main() == 0

    readiness = build_readiness(analysis_dir=tmp_path)
    assert readiness["application_readiness"]["ready_to_apply_rotation"] is True
    assert readiness["application_readiness"]["next_step_now"] == "apply_approved_attack_challenger_rotation"
