from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_post_spike_bridge_backup_negative_window_repair_review as mod


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
            "sharpe": 1.8,
            "max_drawdown": 0.09,
        },
        "overfitting": {
            "sensitivity_max_drift": drift,
            "walk_forward": walk_forward,
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_bridge_backup_negative_window_repair_review_closes_local_axes_when_completed_repairs_fail(tmp_path, monkeypatch) -> None:
    _write_diagnostic(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260421T000001Z.json",
        "post_spike_bridge_backup::bridge_28_relief::base",
        0.35726566,
        0.1321,
        [5],
    )
    _write_diagnostic(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260421T000002Z.json",
        "post_spike_bridge_backup::bridge_28_relief::cost20",
        0.34639312,
        0.1322,
        [5],
    )
    _write_diagnostic(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260421T000003Z.json",
        "post_spike_bridge_backup::bridge_28_hold34::base",
        0.33654617,
        0.1338,
        [5],
    )
    _write_diagnostic(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260421T000004Z.json",
        "post_spike_bridge_backup::bridge_28_hold34::cost20",
        0.32586119,
        0.1404,
        [5],
    )
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)

    report = mod.build_report()

    assert report["repair_review_reference"]["completed_variant_count"] == 2
    assert report["repair_review_verdict"]["negative_window_repair_found"] is False
    assert report["repair_review_verdict"]["completed_local_repair_axes_failed"] is True
    assert report["repair_review_verdict"]["next_step_now"] == "close_local_bridge_window_repairs_and_open_new_axis"
    assert report["best_completed_variant"]["variant_label"] == "bridge_28_relief"
