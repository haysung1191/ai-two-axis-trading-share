from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_attack_challenger_validation_review as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_attack_challenger_validation_review_detects_rotation_already_applied(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "btc_1d_post_spike_hold36_drift_repair_candidates_latest.json",
        {
            "active_challenger_reference": {
                "label": "post_spike_trend864_depth055_volume100_hold32",
            },
            "hold36_drift_repair_candidates": [
                {
                    "variant_label": "depth055_volume100_hold36",
                    "base_cagr": 0.3010,
                    "base_sharpe": 1.6408,
                    "base_max_drawdown": 0.1267,
                    "sensitivity_max_drift": 0.1325,
                    "parameters": {
                        "trend_ema_window": 96,
                        "max_consolidation_depth_pct": 0.055,
                        "min_volume_ratio": 1.0,
                        "max_hold_bars": 36,
                    },
                    "cagr_delta_vs_active": 0.0068,
                    "sharpe_delta_vs_active": 0.1010,
                    "max_drawdown_delta_vs_active": 0.0085,
                    "drift_delta_vs_active": 0.0399,
                    "beats_active_rotation_gate": True,
                }
            ],
            "drift_repair_verdict": {
                "top_candidate": "depth055_volume100_hold36",
                "top_candidate_beats_active_rotation_gate": True,
            },
        },
    )

    report = mod.build_report(analysis_dir=tmp_path)

    verdict = report["validation_review"]
    assert verdict["approve_rotation_now"] is False
    assert verdict["rotation_already_applied"] is True
    assert verdict["proposed_attack_challenger"] == "post_spike_trend960_depth055_volume100_hold36"
    assert verdict["next_step_now"] == "monitor_active_post_spike_challenger_against_attack_stack"


def test_attack_challenger_validation_review_main_writes_latest_aliases(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)
    monkeypatch.setattr(
        mod,
        "build_report",
        lambda analysis_dir=tmp_path: {
            "active_challenger_reference": {"label": "post_spike_trend864_depth055_volume100_hold32"},
            "validated_candidate": {
                "variant_label": "depth055_volume100_hold36",
                "base_cagr": 0.3010,
                "base_sharpe": 1.6408,
                "base_max_drawdown": 0.1267,
                "sensitivity_max_drift": 0.1325,
                "cagr_delta_vs_active": 0.0068,
                "sharpe_delta_vs_active": 0.1010,
                "max_drawdown_delta_vs_active": 0.0085,
                "drift_delta_vs_active": 0.0399,
            },
            "validation_review": {
                "candidate_found": True,
                "candidate_label": "depth055_volume100_hold36",
                "approve_rotation_now": True,
                "keep_current_challenger_until_switch": False,
                "proposed_attack_challenger": "depth055_volume100_hold36",
                "next_step_now": "approve_hold36_drift_repair_challenger_rotation",
                "reason": "ok",
            },
            "approval_checks": [],
            "decision_summary": [],
        },
    )

    exit_code = mod.main()

    assert exit_code == 0
    latest_json = tmp_path / "btc_1d_attack_challenger_validation_review_latest.json"
    latest_md = tmp_path / "btc_1d_attack_challenger_validation_review_md_latest.md"
    assert latest_json.exists()
    assert latest_md.exists()
