from __future__ import annotations

import pandas as pd
from pathlib import Path

from tools.operations import build_split_models_shadow_report as shadow


def test_split_models_shadow_report_outputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(shadow, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(
        shadow,
        "run_backtests",
        lambda output_dir, config: _fake_backtest_results(output_dir),
    )
    shadow.main()

    expected = [
        "shadow_summary.csv",
        "shadow_summary.json",
        "shadow_health.csv",
        "shadow_health.json",
        "shadow_summary_history.csv",
        "shadow_health_history.csv",
        "shadow_turnover_monitor.csv",
        "shadow_current_book.csv",
        "shadow_current_sector_mix.csv",
        "shadow_loss_month_diagnostics.csv",
    ]
    for name in expected:
        assert (tmp_path / name).exists()

    summary = (tmp_path / "shadow_summary.csv").read_text(encoding="utf-8-sig")
    assert "health_verdict" in summary
    assert "current_max_sector_weight" in summary
    assert "health_total_checks" in summary
    health = (tmp_path / "shadow_health.csv").read_text(encoding="utf-8-sig")
    assert "Passed" in health
    assert "Current max sector weight <= 0.50" in health
    assert "Recent max sector weight <= 0.70" in health
    loss_diag = (tmp_path / "shadow_loss_month_diagnostics.csv").read_text(encoding="utf-8-sig")
    assert "DominantSector" in loss_diag

    shadow.main()
    history = (tmp_path / "shadow_summary_history.csv").read_text(encoding="utf-8-sig")
    assert "RunTimestamp" in history


def _fake_backtest_results(output_dir: Path) -> dict[str, pd.DataFrame]:
    nav = pd.DataFrame(
        [
            {
                "SignalDate": "2026-01-31",
                "NextDate": "2026-02-28",
                "GrossReturn": 0.03,
                "NetReturn": 0.02,
                "Turnover": 0.8,
                "NAV": 1.00,
                "Holdings": 4,
            },
            {
                "SignalDate": "2026-02-28",
                "NextDate": "2026-03-31",
                "GrossReturn": 0.04,
                "NetReturn": 0.03,
                "Turnover": 0.9,
                "NAV": 1.05,
                "Holdings": 4,
            },
        ]
    )
    positions = pd.DataFrame(
        [
            {
                "SignalDate": "2026-02-28",
                "Symbol": "ETF1",
                "TargetWeight": 0.25,
                "MomentumScore": 1.2,
                "FlowScore": 0.8,
                "Market": "KR",
                "Sector": "Tech",
            },
            {
                "SignalDate": "2026-02-28",
                "Symbol": "ETF2",
                "TargetWeight": 0.25,
                "MomentumScore": 1.1,
                "FlowScore": 0.7,
                "Market": "KR",
                "Sector": "Finance",
            },
            {
                "SignalDate": "2026-02-28",
                "Symbol": "ETF3",
                "TargetWeight": 0.25,
                "MomentumScore": 1.0,
                "FlowScore": 0.6,
                "Market": "KR",
                "Sector": "Industrial",
            },
            {
                "SignalDate": "2026-02-28",
                "Symbol": "ETF4",
                "TargetWeight": 0.25,
                "MomentumScore": 0.9,
                "FlowScore": 0.5,
                "Market": "KR",
                "Sector": "Utilities",
            },
        ]
    )
    weights = positions[["SignalDate", "Symbol", "TargetWeight"]].copy()
    weights.to_csv(output_dir / "trading_book_backtest_weights.csv", index=False, encoding="utf-8-sig")
    return {
        "trading_book_backtest_nav": nav,
        "trading_book_backtest_positions": positions,
    }
