from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.candidate_alpha_post_analysis import (
    build_interval_regime_frame,
    build_post_analysis_report,
    join_candidate_alpha_labels,
    load_direct_backtest_timeseries,
    reconstruct_backtest_timeseries,
    summarize_trade_ledger_by_regime,
)


def test_post_analysis_prefers_direct_timestamps_and_trade_bucket_summary(tmp_path: Path) -> None:
    alpha_index = pd.date_range("2026-01-01T00:00:00Z", periods=12, freq="1h")
    alpha_frame = pd.DataFrame(
        {
            "avoidance_regime": [False] * 4 + [True] * 4 + [False] * 4,
            "tradable_regime": [True] * 4 + [False] * 4 + [True] * 4,
        },
        index=alpha_index,
    )
    interval_frame = build_interval_regime_frame(alpha_frame, "4h")

    report = {
        "strategy_name": "dummy",
        "symbols": ["KRW-BTC"],
        "trades": 2,
        "win_rate": 0.5,
        "max_drawdown": 0.1,
        "equity_curve": [1.0, 1.1, 1.0],
        "equity_timestamps": [
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T04:00:00+00:00",
            "2026-01-01T08:00:00+00:00",
        ],
        "trade_ledger": [
            {
                "entry_timestamp": "2026-01-01T00:00:00+00:00",
                "exit_timestamp": "2026-01-01T04:00:00+00:00",
                "direction": "long",
                "bars_held": 2,
                "pnl": 0.1,
                "win": True,
            },
            {
                "entry_timestamp": "2026-01-01T04:00:00+00:00",
                "exit_timestamp": "2026-01-01T08:00:00+00:00",
                "direction": "long",
                "bars_held": 1,
                "pnl": -0.05,
                "win": False,
            },
        ],
    }
    spec = {"metadata": {"symbols": ["KRW-BTC"], "ohlcv_interval": "4h"}}

    direct = load_direct_backtest_timeseries(report, spec)
    assert direct is not None
    assert list(direct.index.astype(str)) == [
        "2026-01-01 00:00:00+00:00",
        "2026-01-01 04:00:00+00:00",
        "2026-01-01 08:00:00+00:00",
    ]

    joined = join_candidate_alpha_labels(direct, interval_frame)
    trade_bucket_summary = summarize_trade_ledger_by_regime(report["trade_ledger"], interval_frame)
    final_report = build_post_analysis_report(
        tmp_path,
        report,
        spec,
        joined,
        trade_bucket_summary,
        used_direct_timestamps=True,
    )

    assert final_report["join_coverage"]["used_direct_timestamps"] is True
    assert final_report["join_coverage"]["matched_label_ratio"] == 1.0
    assert final_report["bucket_summary"]["avoidance_regime"]["trade_count"] == 1
    assert final_report["bucket_summary"]["avoidance_regime"]["win_rate"] == 0.0
    assert final_report["bucket_summary"]["non_avoidance_regime"]["trade_count"] == 1
    assert final_report["bucket_summary"]["non_avoidance_regime"]["win_rate"] == 1.0


def test_post_analysis_reconstructs_when_direct_timestamps_missing() -> None:
    alpha_index = pd.date_range("2026-01-01T00:00:00Z", periods=12, freq="1h")
    alpha_frame = pd.DataFrame(
        {
            "avoidance_regime": [False] * 4 + [True] * 4 + [False] * 4,
            "tradable_regime": [True] * 4 + [False] * 4 + [True] * 4,
        },
        index=alpha_index,
    )
    interval_frame = build_interval_regime_frame(alpha_frame, "4h")
    report = {
        "strategy_name": "dummy",
        "symbols": ["KRW-BTC"],
        "equity_curve": [1.0, 1.1, 1.0],
    }
    spec = {"metadata": {"symbols": ["KRW-BTC"], "ohlcv_interval": "4h"}}

    reconstructed = reconstruct_backtest_timeseries(report, spec, interval_frame)

    assert len(reconstructed) == 3
    assert reconstructed.index[0] == interval_frame.index[-3]
