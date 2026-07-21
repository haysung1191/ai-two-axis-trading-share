from __future__ import annotations

import scripts.run_btc_1d_post_spike_reopen_seed_cycle as mod


def test_reopen_seed_cycle_prefers_stronger_current_seed(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        mod,
        "_run_seed",
        lambda **kwargs: {
            "seed_label": kwargs["seed_label"],
            "candidate_label": kwargs["seed_label"],
            "strategy_name": "btc_1d_post_spike_consolidation_breakout_v4",
            "paper_validation_passed": True,
            "base_cagr": 0.33 if kwargs["seed_label"] == mod.PREFERRED_REOPEN_SEED else 0.35,
            "base_sharpe": 1.6 if kwargs["seed_label"] == mod.PREFERRED_REOPEN_SEED else 1.8,
            "base_max_drawdown": 0.12,
            "completed_trades": 10,
            "walk_forward_passed": True,
            "sensitivity_max_drift": 0.18,
            "negative_window_count": 0,
            "negative_windows": [],
            "validation_json": "a.json",
            "walk_forward_json": "b.json",
        },
    )

    report = mod.build_report(
        periods=2200,
        allow_synthetic_ohlcv_fallback=True,
        analysis_dir=tmp_path,
    )

    assert report["reopen_seed_cycle"]["preferred_seed_now"] == mod.BACKUP_REOPEN_SEED
    assert report["reopen_seed_cycle"]["comparison_ready"] is True
