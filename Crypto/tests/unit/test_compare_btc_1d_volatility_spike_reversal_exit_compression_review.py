from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_volatility_spike_reversal_exit_compression_review as mod


def _write_batch(path: Path, current_mdd: float, tighter_mdd: float) -> None:
    payload = {
        "stage1_survivors": ["v1", "v2", "v3"],
        "results": [
            {
                "variant_label": "current_reference",
                "decision": "KEEP",
                "sharpe": 1.19,
                "cagr": 0.38,
                "max_drawdown": current_mdd,
                "failed_gates": ["backtest_max_drawdown"],
            },
            {
                "variant_label": "tighter_stop",
                "decision": "KEEP",
                "sharpe": 1.03,
                "cagr": 0.31,
                "max_drawdown": tighter_mdd,
                "failed_gates": ["backtest_max_drawdown"],
            },
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_walk_forward(path: Path, cagrs: list[float]) -> None:
    payload = {
        "config": {"candidate_label": mod.CANDIDATE_LABEL},
        "base_metrics": {
            "trades": 96,
            "sharpe": 1.03,
            "max_drawdown": 0.26,
            "cagr": 0.31,
        },
        "overfitting": {
            "walk_forward": [
                {"window": index, "metrics": {"cagr": cagr}}
                for index, cagr in enumerate(cagrs, start=1)
            ],
            "sensitivity_max_drift": 0.25,
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_exit_compression_review_closes_axis_when_negative_windows_remain(tmp_path, monkeypatch) -> None:
    _write_batch(
        tmp_path / "btc_1d_volatility_spike_reversal_continuation_exit_compression_batch_20260515T000001Z.json",
        current_mdd=0.28714206,
        tighter_mdd=0.25968288,
    )
    _write_walk_forward(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260515T000002Z.json",
        [0.97, -0.08, 0.54, -0.02, -0.14],
    )
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)

    report = mod.build_report()

    assert report["exit_compression_reference"]["stage1_survivor_count"] == 3
    assert report["best_exit_compression_by_cagr"]["variant_label"] == "current_reference"
    assert report["exit_compression_verdict"]["mdd_reduction_from_current_reference"] == 0.02745918
    assert report["tighter_stop_walk_forward"]["negative_windows"] == [2, 4, 5]
    assert report["exit_compression_verdict"]["exit_compression_repair_found"] is False
    assert report["exit_compression_verdict"]["completed_axis_failed"] is True
    assert (
        report["exit_compression_verdict"]["next_step_now"]
        == "close_spike_reversal_exit_compression_axis_and_open_new_return_family"
    )


def test_exit_compression_review_opens_when_tighter_stop_repairs_axis(tmp_path, monkeypatch) -> None:
    _write_batch(
        tmp_path / "btc_1d_volatility_spike_reversal_continuation_exit_compression_batch_20260515T000001Z.json",
        current_mdd=0.28,
        tighter_mdd=0.24,
    )
    _write_walk_forward(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260515T000002Z.json",
        [0.20, 0.10, 0.30, 0.05, 0.12],
    )
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)

    report = mod.build_report()

    assert report["exit_compression_verdict"]["exit_compression_repair_found"] is True
    assert report["exit_compression_verdict"]["completed_axis_failed"] is False
    assert report["exit_compression_verdict"]["next_step_now"] == "open_attack_main_replacement_review"
