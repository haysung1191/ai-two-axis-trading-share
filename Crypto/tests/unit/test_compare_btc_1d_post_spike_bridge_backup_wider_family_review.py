from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_post_spike_bridge_backup_wider_family_review as mod


def _write_diagnostic(path: Path, candidate_label: str, cagr: float, drift: float, negative_windows: list[int]) -> None:
    walk_forward = []
    for window in range(1, 6):
        is_negative = window in negative_windows
        walk_forward.append(
            {
                "window": window,
                "metrics": {
                    "cagr": -0.01 if is_negative else 0.05,
                    "sharpe": -0.1 if is_negative else 0.8,
                    "trades": 0 if window == 2 else 3,
                },
            }
        )
    payload = {
        "config": {
            "candidate_label": candidate_label,
        },
        "base_metrics": {
            "cagr": cagr,
            "sharpe": 1.9,
            "max_drawdown": 0.09,
        },
        "overfitting": {
            "sensitivity_max_drift": drift,
            "walk_forward": walk_forward,
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_wider_family_review_reports_in_progress_pairs(tmp_path, monkeypatch) -> None:
    _write_diagnostic(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260515T000001Z.json",
        "post_spike_bridge_backup::bridge_wide_trend84_spike24_buffer018::base",
        0.39,
        0.12,
        [],
    )
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)

    report = mod.build_report()

    assert report["wider_family_reference"]["completed_variant_count"] == 0
    assert report["wider_family_reference"]["pending_variant_count"] == len(mod.WIDER_FAMILY_VARIANTS)
    assert report["wider_family_verdict"]["wider_family_complete"] is False
    assert report["wider_family_verdict"]["next_step_now"] == "keep_wider_family_batch_running"


def test_wider_family_review_opens_when_completed_variant_passes(tmp_path, monkeypatch) -> None:
    _write_diagnostic(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260515T000001Z.json",
        "post_spike_bridge_backup::bridge_wide_trend84_spike24_buffer018::base",
        0.395,
        0.12,
        [],
    )
    _write_diagnostic(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260515T000002Z.json",
        "post_spike_bridge_backup::bridge_wide_trend84_spike24_buffer018::cost20",
        0.355,
        0.13,
        [],
    )
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)

    report = mod.build_report()

    assert report["wider_family_reference"]["completed_variant_count"] == 1
    assert report["best_completed_variant"]["variant_label"] == "bridge_wide_trend84_spike24_buffer018"
    assert report["wider_family_verdict"]["main_gap_recovery_found"] is True
    assert report["wider_family_verdict"]["next_step_now"] == "open_attack_main_replacement_review"
