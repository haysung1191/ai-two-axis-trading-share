from pathlib import Path

import pandas as pd

from live_core.kis_orchestration import (
    append_hybrid_results,
    blend_strategy_results,
    run_strategy_batch,
    save_backtest_outputs,
)


class _Strategy:
    def __init__(self, name: str):
        self.name = name


def _component_out(returns):
    out = pd.DataFrame({"daily_return": returns}, index=pd.date_range("2024-01-01", periods=len(returns), freq="B"))
    out["nav"] = (1.0 + out["daily_return"]).cumprod()
    return out


def test_blend_strategy_results_combines_component_returns():
    rs = _component_out([0.01, 0.00, -0.01])
    rb = _component_out([0.00, 0.02, 0.01])
    component_results = {
        "Weekly Score50 RegimeState": (rs, {"CAGR": 0.1}),
        "Weekly ETF RiskBudget": (rb, {"CAGR": 0.2}),
    }

    out, metrics = blend_strategy_results("Weekly Hybrid RS50 RB50", component_results)

    assert round(float(out["daily_return"].iloc[0]), 10) == 0.005
    assert round(float(out["daily_return"].iloc[1]), 10) == 0.01
    assert "CAGR" in metrics


def test_run_strategy_batch_and_append_hybrid_results():
    strategies = [_Strategy("Weekly Score50 RegimeState"), _Strategy("Weekly ETF RiskBudget")]

    def _runner(strategy):
        out = _component_out([0.01, 0.0, 0.0]) if "Score50" in strategy.name else _component_out([0.0, 0.01, 0.0])
        return out, {"CAGR": 0.1 if "Score50" in strategy.name else 0.2}

    summary, nav, outputs = run_strategy_batch(strategies, _runner)
    summary, nav = append_hybrid_results(summary, nav, outputs)

    strategy_names = {row["Strategy"] for row in summary}
    assert "Weekly Hybrid RS50 RB50" in strategy_names
    assert "Weekly Hybrid RS50 RB50" in nav.columns


def test_save_backtest_outputs_writes_summary_and_nav(tmp_path: Path):
    summary = [{"Strategy": "A", "CAGR": 0.1}]
    nav = pd.DataFrame({"A": [1.0, 1.1]}, index=pd.date_range("2024-01-01", periods=2, freq="B"))

    summary_df, summary_path, nav_path = save_backtest_outputs(summary, nav, str(tmp_path / "backtest"))

    assert summary_df.shape[0] == 1
    assert Path(summary_path).exists()
    assert Path(nav_path).exists()
