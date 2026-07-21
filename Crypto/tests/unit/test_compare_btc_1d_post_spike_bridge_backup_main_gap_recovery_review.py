from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_post_spike_bridge_backup_main_gap_recovery_review as mod


def _write_batch(path: Path, rows: list[dict]) -> None:
    payload = {
        "active_bridge_backup_label": "bridge_28_relief",
        "main_base_cagr_reference": 0.42427487,
        "main_cost20_cagr_reference": 0.40362936,
        "best_variant": rows[0] if rows else {},
        "results": rows,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_bridge_backup_main_gap_recovery_review_closes_local_gap_axis(tmp_path, monkeypatch) -> None:
    rows = [
        {
            "variant_label": "bridge_28_relief",
            "base_cagr_gap_to_main": 0.10884736,
            "cost20_cagr_gap_to_main": 0.09820287,
            "max_sensitivity_drift": 0.15420068,
            "negative_window_clean": True,
            "replacement_open_passed": False,
        },
        {
            "variant_label": "bridge_28_volume100",
            "base_cagr_gap_to_main": 0.142,
            "cost20_cagr_gap_to_main": 0.121,
            "max_sensitivity_drift": 0.18,
            "negative_window_clean": False,
            "replacement_open_passed": False,
        },
    ]
    _write_batch(
        tmp_path / "btc_1d_post_spike_bridge_backup_main_gap_recovery_batch_20260515T000001Z.json",
        rows,
    )
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)

    report = mod.build_report()

    assert report["main_gap_recovery_reference"]["completed_variant_count"] == 2
    assert report["main_gap_recovery_reference"]["clean_variant_count"] == 1
    assert report["best_completed_variant"]["variant_label"] == "bridge_28_relief"
    assert report["main_gap_recovery_verdict"]["main_gap_recovery_found"] is False
    assert report["main_gap_recovery_verdict"]["completed_local_gap_axes_failed"] is True
    assert report["main_gap_recovery_verdict"]["next_step_now"] == "open_wider_bridge_family_or_new_axis"


def test_bridge_backup_main_gap_recovery_review_opens_when_variant_passes(tmp_path, monkeypatch) -> None:
    rows = [
        {
            "variant_label": "bridge_28_wider_family",
            "base_cagr_gap_to_main": 0.03,
            "cost20_cagr_gap_to_main": 0.04,
            "max_sensitivity_drift": 0.12,
            "negative_window_clean": True,
            "replacement_open_passed": True,
        },
    ]
    _write_batch(
        tmp_path / "btc_1d_post_spike_bridge_backup_main_gap_recovery_batch_20260515T000001Z.json",
        rows,
    )
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)

    report = mod.build_report()

    assert report["main_gap_recovery_verdict"]["main_gap_recovery_found"] is True
    assert report["main_gap_recovery_verdict"]["completed_local_gap_axes_failed"] is False
    assert report["main_gap_recovery_verdict"]["next_step_now"] == "open_attack_main_replacement_review"
