from __future__ import annotations

from pathlib import Path

from scripts.candidate_alpha_extended_window_report import render_extended_window_markdown


def test_render_extended_window_markdown_includes_history_and_decision() -> None:
    report = {
        "history_window": {
            "bithumb_krw_btc_rows": 5000,
            "bithumb_krw_usdt_rows": 5000,
            "binance_btcusdt_rows": 4999,
            "common_start": "2025-09-06T06:00:00+00:00",
            "common_end": "2026-04-03T05:00:00+00:00",
            "common_rows": 4999,
        },
        "overlay_validation": {
            "comparison": {
                "baseline": {"sharpe": -1.0, "cagr": -0.1, "trades": 10, "win_rate": 0.5, "max_drawdown": 0.1},
                "baseline_plus_candidate_alpha_avoidance_filter": {"sharpe": -0.5, "cagr": 0.0, "trades": 12, "win_rate": 0.55, "max_drawdown": 0.08},
            }
        },
        "overlay_robustness": {
            "consistency": {
                "sharpe_improved_chunks": 2,
                "cagr_improved_chunks": 2,
                "win_rate_improved_chunks": 2,
                "drawdown_improved_chunks": 2,
            }
        },
        "final_decision": "continue",
        "decision_reason": "test reason",
    }

    text = render_extended_window_markdown(report)

    assert "common_rows: 4999" in text
    assert "decision: continue" in text
    assert "sharpe improved chunks: 2" in text
