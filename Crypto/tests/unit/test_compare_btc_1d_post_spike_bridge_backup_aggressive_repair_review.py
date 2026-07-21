from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_post_spike_bridge_backup_aggressive_repair_review as mod


def _write_batch(path: Path, rows: list[dict]) -> None:
    payload = {
        "main_base_cagr_reference": 0.42427487,
        "main_cost20_cagr_reference": 0.40362936,
        "best_variant": rows[0] if rows else {},
        "results": rows,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_aggressive_repair_review_closes_failed_axis(tmp_path, monkeypatch) -> None:
    rows = [
        {
            "variant_label": "aggr_repair_trend864_depth055_volume104",
            "base_cagr_gap_to_main": 0.12469599,
            "cost20_cagr_gap_to_main": 0.11551526,
            "max_sensitivity_drift": 0.24988975,
            "negative_window_clean": False,
            "replacement_open_passed": False,
        }
    ]
    _write_batch(
        tmp_path / "btc_1d_post_spike_bridge_backup_aggressive_repair_batch_20260515T000001Z.json",
        rows,
    )
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)

    report = mod.build_report()

    assert report["aggressive_repair_reference"]["completed_variant_count"] == 1
    assert report["aggressive_repair_reference"]["clean_variant_count"] == 0
    assert report["aggressive_repair_verdict"]["main_gap_recovery_found"] is False
    assert report["aggressive_repair_verdict"]["completed_axis_failed"] is True
    assert report["aggressive_repair_verdict"]["next_step_now"] == "close_aggressive_repair_axis_and_open_new_return_family"


def test_aggressive_repair_review_opens_when_variant_passes(tmp_path, monkeypatch) -> None:
    rows = [
        {
            "variant_label": "aggr_repair_winner",
            "base_cagr_gap_to_main": 0.03,
            "cost20_cagr_gap_to_main": 0.04,
            "max_sensitivity_drift": 0.12,
            "negative_window_clean": True,
            "replacement_open_passed": True,
        }
    ]
    _write_batch(
        tmp_path / "btc_1d_post_spike_bridge_backup_aggressive_repair_batch_20260515T000001Z.json",
        rows,
    )
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)

    report = mod.build_report()

    assert report["aggressive_repair_verdict"]["main_gap_recovery_found"] is True
    assert report["aggressive_repair_verdict"]["completed_axis_failed"] is False
    assert report["aggressive_repair_verdict"]["next_step_now"] == "open_attack_main_replacement_review"
