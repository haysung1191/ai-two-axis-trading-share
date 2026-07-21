from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_post_spike_hold36_drift_repair_candidates as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_hold36_drift_repair_candidates_prefers_gate_passing_variant(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "btc_1d_attack_challenger_rotation_review_latest.json",
        {
            "active_challenger_reference": {
                "label": "post_spike_trend864_depth055_volume100_hold32",
                "paper_validation_cagr": 0.2941,
                "paper_validation_sharpe": 1.5398,
                "paper_validation_max_drawdown": 0.1352,
                "negative_walk_forward_windows": [],
                "idle_walk_forward_windows": [2],
                "sensitivity_max_drift": 0.1724,
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch_latest.json",
        {
            "results": [
                {
                    "variant_label": "trend864_depth055_volume100_hold36",
                    "base_cagr": 0.3340,
                    "base_sharpe": 1.6886,
                    "base_max_drawdown": 0.1267,
                    "sensitivity_max_drift": 0.2020,
                }
            ]
        },
    )
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_sensitivity_repair_batch_latest.json",
        {
            "results": [
                {
                    "variant_label": "depth055_volume100_hold36",
                    "decision": "KEEP",
                    "sharpe": 1.6408,
                    "cagr": 0.3010,
                    "max_drawdown": 0.1267,
                    "sensitivity_max_drift": 0.1325,
                    "failed_gates": [],
                    "overfitting_flags": [],
                    "parameters": {},
                },
                {
                    "variant_label": "depth055_volume104_hold36",
                    "decision": "KEEP",
                    "sharpe": 1.6718,
                    "cagr": 0.3052,
                    "max_drawdown": 0.1267,
                    "sensitivity_max_drift": 0.1818,
                    "failed_gates": [],
                    "overfitting_flags": [],
                    "parameters": {},
                },
            ]
        },
    )

    report = mod.build_report(analysis_dir=tmp_path)

    verdict = report["drift_repair_verdict"]
    assert verdict["top_candidate"] == "depth055_volume100_hold36"
    assert verdict["top_candidate_beats_active_rotation_gate"] is True
    assert verdict["next_step_now"] == "validate_hold36_drift_repair_candidate_against_active_challenger"


def test_hold36_drift_repair_candidates_accepts_active_baseline_as_fallback_baseline(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "btc_1d_attack_challenger_rotation_review_latest.json",
        {
            "active_challenger_reference": {
                "label": "post_spike_trend960_depth055_volume100_hold36",
                "paper_validation_cagr": 0.3010,
                "paper_validation_sharpe": 1.6408,
                "paper_validation_max_drawdown": 0.1267,
                "negative_walk_forward_windows": [],
                "idle_walk_forward_windows": [2],
                "sensitivity_max_drift": 0.1325,
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch_latest.json",
        {
            "results": [
                {
                    "variant_label": "active_baseline",
                    "base_cagr": 0.3010,
                    "base_sharpe": 1.6408,
                    "base_max_drawdown": 0.1267,
                    "sensitivity_max_drift": 0.1325,
                }
            ]
        },
    )
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_sensitivity_repair_batch_latest.json",
        {
            "results": [
                {
                    "variant_label": "depth055_volume100_hold36",
                    "decision": "KEEP",
                    "sharpe": 1.6408,
                    "cagr": 0.3010,
                    "max_drawdown": 0.1267,
                    "sensitivity_max_drift": 0.1325,
                    "failed_gates": [],
                    "overfitting_flags": [],
                    "parameters": {},
                }
            ]
        },
    )

    report = mod.build_report(analysis_dir=tmp_path)

    assert report["current_hold36_baseline"]["variant_label"] == "active_baseline"


def test_hold36_drift_repair_candidates_main_writes_latest_aliases(
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
                "sensitivity_max_drift": 0.1724,
            },
            "current_hold36_baseline": {
                "variant_label": "trend864_depth055_volume100_hold36",
                "sensitivity_max_drift": 0.2020,
            },
            "hold36_drift_repair_candidates": [],
            "drift_repair_verdict": {
                "candidate_found": True,
                "top_candidate": "depth055_volume100_hold36",
                "top_candidate_beats_active_rotation_gate": True,
                "next_step_now": "validate_hold36_drift_repair_candidate_against_active_challenger",
                "reason": "ok",
            },
            "decision_summary": [],
        },
    )

    exit_code = mod.main()

    assert exit_code == 0
    latest_json = tmp_path / "btc_1d_post_spike_hold36_drift_repair_candidates_latest.json"
    latest_md = tmp_path / "btc_1d_post_spike_hold36_drift_repair_candidates_md_latest.md"
    assert latest_json.exists()
    assert latest_md.exists()
