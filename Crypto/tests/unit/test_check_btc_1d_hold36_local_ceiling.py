from __future__ import annotations

import json

from scripts.check_btc_1d_hold36_local_ceiling import (
    check_hold36_local_ceiling,
    render_hold36_local_ceiling_line,
)


def test_check_hold36_local_ceiling_passes_on_expected_contract(tmp_path) -> None:
    payload = {
        "handoff_reference": {
            "active_backup": "post_spike_trend92_depth058_volume105_hold36",
        },
        "local_ceiling_status": {
            "status_band": "pressure_watch",
            "ceiling_confirmed": True,
            "primary_blocker": "base_cagr_gap",
            "remaining_base_cagr_gap_to_open": 0.037,
            "remaining_cost20_cagr_gap_to_open": 0.0,
            "closed_local_axes": [
                "challenger_reopen",
                "base_gap_recovery",
                "entry_timing",
                "entry_strength",
                "structure",
            ],
            "do_not_repeat_local_loop": True,
        },
        "handoff_metrics": {
            "sharpe_edge_vs_main": 0.25,
            "mdd_improvement_vs_main": 0.06,
            "drift_improvement_vs_main": 0.20,
        },
    }
    (tmp_path / "btc_1d_hold36_local_ceiling_handoff_latest.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    result = check_hold36_local_ceiling(analysis_dir=tmp_path)

    assert result["ok"] is True
    assert result["failed_checks"] == []


def test_render_hold36_local_ceiling_line_mentions_failed_check_count(tmp_path) -> None:
    payload = {
        "handoff_reference": {
            "active_backup": "wrong_backup",
        },
        "local_ceiling_status": {
            "status_band": "baseline_hold",
            "ceiling_confirmed": False,
            "primary_blocker": "wrong_blocker",
            "remaining_base_cagr_gap_to_open": 0.0,
            "remaining_cost20_cagr_gap_to_open": 0.01,
            "closed_local_axes": [],
            "do_not_repeat_local_loop": False,
        },
        "handoff_metrics": {
            "sharpe_edge_vs_main": 0.0,
            "mdd_improvement_vs_main": 0.0,
            "drift_improvement_vs_main": 0.0,
        },
    }
    (tmp_path / "btc_1d_hold36_local_ceiling_handoff_latest.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    result = check_hold36_local_ceiling(analysis_dir=tmp_path)
    line = render_hold36_local_ceiling_line(result)

    assert result["ok"] is False
    assert "failed_checks=" in line
