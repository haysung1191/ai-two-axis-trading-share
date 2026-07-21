from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_post_spike_idle_window_context as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_post_spike_idle_window_context_flags_repeated_window2_idle(tmp_path: Path) -> None:
    batch_payload = {
        "best_variant": {
            "variant_label": "anchor_entry_shape",
            "base_cagr": 0.26,
            "base_sharpe": 1.6,
            "sensitivity_max_drift": 0.29,
            "negative_windows": [4],
            "idle_windows": [2],
            "analysis_result_json": "analysis_results\\anchor_diag.json",
        },
        "results": [
            {
                "variant_label": "anchor_entry_shape",
                "base_cagr": 0.26,
                "base_sharpe": 1.6,
                "sensitivity_max_drift": 0.29,
                "negative_windows": [4],
                "idle_windows": [2],
                "analysis_result_json": "analysis_results\\anchor_diag.json",
            },
            {
                "variant_label": "faster_trigger_entry_shape",
                "base_cagr": 0.26,
                "base_sharpe": 1.6,
                "sensitivity_max_drift": 0.29,
                "negative_windows": [4],
                "idle_windows": [2],
                "analysis_result_json": "analysis_results\\fast_diag.json",
            },
            {
                "variant_label": "deeper_confirmation_entry_shape",
                "base_cagr": 0.22,
                "base_sharpe": 1.5,
                "sensitivity_max_drift": 0.33,
                "negative_windows": [],
                "idle_windows": [2, 4],
                "analysis_result_json": "analysis_results\\slow_diag.json",
            },
        ],
    }
    followup_payload = {
        "best_variant": {},
        "results": [
            {
                "variant_label": "trend9504_depth055_volume104_hold36",
                "base_cagr": 0.34,
                "base_sharpe": 1.75,
                "sensitivity_max_drift": 0.23,
                "negative_windows": [4, 5],
                "idle_windows": [2],
                "analysis_result_json": "analysis_results\\trend9504_diag.json",
            }
        ],
    }
    _write_json(tmp_path / "btc_1d_post_spike_idle_window_followup_stage3_batch_latest.json", batch_payload)
    _write_json(tmp_path / "btc_1d_post_spike_entry_shape_idle_repair_batch_latest.json", batch_payload)
    _write_json(tmp_path / "btc_1d_post_spike_idle_window_followup_batch_latest.json", followup_payload)

    def _diag_payload(trades: int) -> dict:
        return {
            "overfitting": {
                "walk_forward": [
                    {"window": 2, "metrics": {
                        "trades": trades,
                        "sharpe": 0.0,
                        "cagr": 0.0,
                        "max_drawdown": 0.0,
                        "equity_curve_summary": {"start": 1.0, "end": 1.0},
                        "equity_timestamps": [
                            "2021-01-01T00:00:00+00:00",
                            "2021-06-25T00:00:00+00:00",
                        ],
                        "trade_ledger": [],
                    }}
                ]
            }
        }

    _write_json(tmp_path / "anchor_diag.json", _diag_payload(0))
    _write_json(tmp_path / "fast_diag.json", _diag_payload(0))
    _write_json(tmp_path / "trend9504_diag.json", _diag_payload(0))
    _write_json(tmp_path / "slow_diag.json", _diag_payload(0))

    report = mod.build_report(analysis_dir=tmp_path)

    verdict = report["idle_window_context_verdict"]
    assert verdict["window_2_is_structurally_idle_across_current_axes"] is True
    assert "repair_anchor_best" in verdict["repeated_idle_roles"]
    assert report["window_2_reference"]["trades"] == 0
